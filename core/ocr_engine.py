import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

class OCREngine:
    def __init__(self):
        self.ocr = RapidOCR()

    def preprocess_image(self, img_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_boosted = clahe.apply(gray)
        _, thresholded = cv2.threshold(contrast_boosted, 185, 255, cv2.THRESH_BINARY)
        return thresholded

    def extract_text(self, img_bgr: np.ndarray, apply_filter: bool = True) -> str:
        target_img = self.preprocess_image(img_bgr) if apply_filter else img_bgr
        results, _ = self.ocr(target_img)
        if not results:
            return ""
        extracted_lines = [item[1].strip() for item in results if item[1].strip()]
        return " ".join(extracted_lines)