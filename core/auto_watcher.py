import time
import os
import mss
import numpy as np
import cv2
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication

try:
    from core.ocr_engine import RapidOCREngine as OCREngineClass
except ImportError:
    try:
        from core.ocr_engine import OCREngine as OCREngineClass
    except ImportError:
        from core.ocr_engine import GameOCREngine as OCREngineClass

from core.translator_manager import TranslatorManager
from core.ai_translator import GeminiTranslator
from core.config_manager import ConfigManager


class AutoWatcherWorker(QThread):
    translation_ready = pyqtSignal(dict)
    status_updated = pyqtSignal(str)

    def __init__(self, roi_coords: tuple, interval: float = 0.5, engine: str = "local", parent=None):
        super().__init__(parent)
        self.roi_coords = roi_coords
        self.interval = interval
        self.engine = engine
        self.is_running = True
        self.last_clean_text = ""

    def stop(self):
        self.is_running = False
        self.wait()

    def run(self):
        config = ConfigManager.load_config()
        api_key = config.get("gemini_api_key", "")
        model_name = config.get("gemini_model", "gemini-1.5-flash")

        try:
            ocr_engine = OCREngineClass()
        except Exception as e:
            print(f"[HATA - OCR Yüklenemedi]: {e}")
            ocr_engine = None

        try:
            local_engine = TranslatorManager()
        except Exception as e:
            print(f"[HATA - TranslatorManager Yüklenemedi]: {e}")
            local_engine = None

        gemini_engine = GeminiTranslator(api_key=api_key, model_name=model_name)

        # Doğrudan PyQt'nin verdiği koordinatları tam sayı olarak alıyoruz
        x, y, w, h = [int(v) for v in self.roi_coords]
        monitor_roi = {"top": y, "left": x, "width": w, "height": h}
        print(f"\n[TAKİP BAŞLADI] Seçilen Bölge (MSS Koordinatları): {monitor_roi}")

        self.status_updated.emit("Canlı takip çalışıyor...")
        saved_debug_crop = False

        with mss.mss() as sct:
            while self.is_running:
                try:
                    sct_img = sct.grab(monitor_roi)
                    frame_bgra = np.array(sct_img)
                    frame = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2BGR)

                    # İlk yakalanan kareyi diske kaydet (Böylece nereyi çektiğini kontrol edebilirsin)
                    if not saved_debug_crop:
                        cv2.imwrite("debug_crop.png", frame)
                        print(f"[KAYDEDİLDİ] Ekran görüntüsü 'debug_crop.png' olarak kaydedildi. Nereye baktığını görmek için açıp bakabilirsin!")
                        saved_debug_crop = True

                    if ocr_engine is None:
                        time.sleep(self.interval)
                        continue

                    # OCR Çıktısı Al
                    if hasattr(ocr_engine, "extract_text"):
                        ocr_result = ocr_engine.extract_text(frame)
                    elif hasattr(ocr_engine, "run_ocr"):
                        ocr_result = ocr_engine.run_ocr(frame)
                    else:
                        ocr_result = ocr_engine(frame)

                    # Metin ayıklama
                    current_text = ""
                    if isinstance(ocr_result, dict):
                        current_text = ocr_result.get("text", "").strip()
                    elif isinstance(ocr_result, str):
                        current_text = ocr_result.strip()
                    elif isinstance(ocr_result, (list, tuple)) and len(ocr_result) > 0:
                        # RapidOCR genellikle tuple/list döner: (sonuçlar, süre)
                        first_item = ocr_result[0]
                        if isinstance(first_item, list):
                            # [[bbox, text, score], ...]
                            lines = [box[1] for box in first_item if len(box) > 1 and box[1]]
                            current_text = " ".join(lines).strip()
                        elif isinstance(first_item, str):
                            current_text = first_item.strip()
                        else:
                            current_text = str(first_item or "").strip()
                    else:
                        current_text = str(ocr_result or "").strip()

                    print(f"[OCR RAW SONUÇ]: '{current_text}'")

                    if current_text and current_text != self.last_clean_text:
                        self.last_clean_text = current_text
                        print(f"[YENİ METİN YAKALANDI]: {current_text}")

                        if self.engine == "gemini" and api_key:
                            self.status_updated.emit("Gemini AI çeviriyor...")
                            res = gemini_engine.translate_single(current_text, model_name=model_name)
                            payload = {
                                "engine": "gemini",
                                "original_text": current_text,
                                "translated_text": res.get("translated_text", ""),
                                "vocabulary": res.get("vocabulary", [])
                            }
                        else:
                            self.status_updated.emit("Yerel motor çeviriyor...")
                            try:
                                if local_engine is not None:
                                    translated = local_engine.translate(current_text)
                                else:
                                    translated = "(Yerel motor başlatılamadı)"
                                print(f"[YEREL ÇEVİRİ BAŞARILI]: {translated}")
                            except Exception as tr_err:
                                print(f"[YEREL ÇEVİRİ HATASI]: {tr_err}")
                                translated = f"(Çeviri hatası: {tr_err})"

                            payload = {
                                "engine": "local",
                                "original_text": current_text,
                                "translated_text": translated,
                                "vocabulary": []
                            }

                        self.translation_ready.emit(payload)
                        self.status_updated.emit("Canlı takip aktif.")

                except Exception as loop_err:
                    print(f"[DÖNGÜ HATASI]: {loop_err}")

                time.sleep(self.interval)