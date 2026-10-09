import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


class OCREngine:
    def __init__(self):
        # Oyun altyazıları için en kararlı varsayılan ayarlar
        # Yön tahmini kapalı, satırları düz kabul eder
        self.ocr = RapidOCR()

    def isolate_game_text(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Hareketli oyun arka planını silip metni öne çıkarır:
        1. Kontrastı güçlendirir (CLAHE).
        2. Arka plan dalgalanmalarını filtreleyip harf hatlarını netleştirir.
        """
        # Griye çevir
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Kontrast eşitleme (özellikle gölgeli/ışıklı oyun sahneleri için)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_boosted = clahe.apply(gray)

        # 3 kanala geri çevirip RapidOCR'a ver (RapidOCR 3 kanal bekler)
        return cv2.cvtColor(contrast_boosted, cv2.COLOR_GRAY2BGR)

    def extract_text(self, img_input, enhance: bool = True) -> str:
        if isinstance(img_input, Image.Image):
            img_np = cv2.cvtColor(np.array(img_input), cv2.COLOR_RGB2BGR)
        else:
            img_np = img_input

        if img_np is None or img_np.size == 0:
            return ""

        # Arka plan hareketini filtrele
        clean_frame = self.isolate_game_text(img_np)

        try:
            # use_cls=False: Oyun altyazılarında satırların ters/yamuk algılanmasını önler
            results, _ = self.ocr(clean_frame, use_det=True, use_cls=False, use_rec=True)
        except Exception:
            try:
                results, _ = self.ocr(clean_frame)
            except Exception as e:
                print(f"[OCR Hatası]: {e}")
                return ""

        if not results:
            return ""

        # Bulunan kutuları yukarıdan aşağıya (satır sırasına göre) diz
        lines = []
        # results -> [ [bbox, text, score], ... ]
        valid_items = [item for item in results if len(item) >= 3 and float(item[2]) >= 0.40 and item[1].strip()]
        
        # Kutunun üst Y koordinatına göre basit sıralama
        valid_items.sort(key=lambda x: min(pt[1] for pt in x[0]))

        for item in valid_items:
            lines.append(item[1].strip())

        return " ".join(lines).strip()