import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

class OCREngine:
    def __init__(self):
        self.ocr = RapidOCR()

    def preprocess_image(self, img_bgr: np.ndarray) -> np.ndarray:
        # 1. Küçük puntolu yazılar için 2x büyüt
        height, width = img_bgr.shape[:2]
        resized = cv2.resize(img_bgr, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

        # 2. Gri tona çevir
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 3. Kontrastı yerel olarak dengele (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)

        # 4. Otsu eşikleme ile arka planı siyah, yazıları beyaz yap
        _, thresholded = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. Minik parazitleri sil
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)

        return cleaned

    def extract_text(self, img_bgr: np.ndarray, apply_filter: bool = True) -> str:
        target_img = self.preprocess_image(img_bgr) if apply_filter else img_bgr
        results, _ = self.ocr(target_img)
        
        if not results:
            return ""

        extracted_lines = [item[1].strip() for item in results if item[1].strip()]
        return " ".join(extracted_lines)