import time
import re
from difflib import SequenceMatcher
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import ImageGrab
from core.ocr_engine import OCREngine
from core.translator_manager import TranslatorManager

class AutoWatcherWorker(QThread):
    """
    Belirlenen ekran alanını (ROI) arka planda periyodik olarak tarar.
    Renk bağımsız RapidOCR ile metni okur.
    Önceki metinle benzerliği kontrol ederek gereksiz çevirileri önler (0% CPU / Kota tasarrufu).
    Yeni bir diyalog geldiğinde çevirip overlay'e sinyal gönderir.
    """
    translation_ready = pyqtSignal(dict)
    status_updated = pyqtSignal(str)

    def __init__(self, roi_coords: tuple, interval: float = 0.5, engine: str = "local"):
        super().__init__()
        self.roi = roi_coords
        self.interval = interval
        self.is_running = False
        
        self.detector = OCREngine()
        self.translator = TranslatorManager(default_engine=engine)
        self.last_text = ""

    def set_roi(self, coords: tuple):
        """Kullanıcı yeni alan seçtiğinde koordinatları günceller."""
        self.roi = coords
        self.last_text = ""

    def set_engine(self, engine: str):
        """Çeviri motorunu değiştirir ('local' veya 'gemini')."""
        self.translator.set_engine(engine)

    def is_similar(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """Karakter/kamera titremelerinden kaynaklanan ufak OCR farklarını yakalar."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() >= threshold

    def is_garbage_text(self, text: str) -> bool:
        """Oyun içi parçacık ve patlama kırıntılarını eler (en az 2 harfli bir kelime yoksa çöp sayar)."""
        words = re.findall(r'[a-zA-Z]{2,}', text)
        return len(words) == 0

    def run(self):
        self.is_running = True
        self.status_updated.emit("Otomatik izleme döngüsü başladı...")

        while self.is_running:
            if not self.roi or self.roi[2] <= 0 or self.roi[3] <= 0:
                time.sleep(self.interval)
                continue

            try:
                x, y, w, h = self.roi
                bbox = (x, y, x + w, y + h)
                
                # Ekran görüntüsünü al
                screenshot = ImageGrab.grab(bbox=bbox)

                # Renk ayrımı yapmaksızın derin öğrenme ile metni oku
                clean_text = self.detector.extract_text(screenshot)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                # Anlamsız sembolleri veya boş kareleri es geç
                if not clean_text or len(clean_text) < 3 or self.is_garbage_text(clean_text):
                    time.sleep(self.interval)
                    continue

                # Ekranda hala aynı altyazı duruyorsa çeviri motorunu meşgul etme
                if self.is_similar(clean_text, self.last_text):
                    time.sleep(self.interval)
                    continue

                # Yeni metin yakalandı!
                self.last_text = clean_text
                self.status_updated.emit(f"Yeni Metin: {clean_text}")

                # Çeviriyi yap ve sonucu Overlay'e ilet
                res = self.translator.translate(clean_text)
                self.translation_ready.emit(res)

            except Exception as e:
                self.status_updated.emit(f"Döngü hatası: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.is_running = False
        self.wait()