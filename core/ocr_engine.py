import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

class OCREngine:
    def __init__(self):
        # ONNX DBNet modeli - Renk bağımsız çalışır
        self.ocr = RapidOCR()

    def preprocess_image(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Küçük puntolu oyun içi yazılar için 2x büyütme uygular.
        Renkleri ve doğal kontrastı koruyarak harf detaylarını açar.
        """
        height, width = img_bgr.shape[:2]
        resized = cv2.resize(img_bgr, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        return resized

    def extract_text(self, img_input, enhance: bool = True) -> str:
        """
        PIL Image veya NumPy BGR kabul eder.
        Wuthering Waves'teki sarı, altın, gri, beyaz her türlü metni renk ayrımı yapmadan okur.
        """
        # PIL formatından BGR formatına çevir
        if isinstance(img_input, Image.Image):
            img_np = cv2.cvtColor(np.array(img_input), cv2.COLOR_RGB2BGR)
        else:
            img_np = img_input

        if img_np is None or img_np.size == 0:
            return ""

        # Görüntüyü büyüt
        target_img = self.preprocess_image(img_np) if enhance else img_np
        
        # Derin öğrenme motoru renkli görsel üzerinden çalışır
        results, _ = self.ocr(target_img)
        
        if not results:
            return ""

        # Güven skoru 0.50 üstü olan satırları filtrele ve birleştir
        extracted_lines = [
            item[1].strip() for item in results 
            if len(item) >= 3 and float(item[2]) >= 0.50 and item[1].strip()
        ]
        return " ".join(extracted_lines)