from core.capture import ScreenCapture
from core.ocr_engine import OCREngine
import cv2

def main():
    capture = ScreenCapture()
    ocr = OCREngine()

    print("Ekran yakalanıyor...")
    # Ekranda sol üstten (x=100, y=100) başlayıp 600x200 piksellik bir alanı çeker
    frame = capture.grab_region(x=0, y=0, width=2560, height=1600)
    
    text = ocr.extract_text(frame, apply_filter=True)
    print("\n--- OKUNAN METİN ---")
    print(text if text else "[Bu alanda metin bulunamadı]")
    print("--------------------")

    filtered = ocr.preprocess_image(frame)
    cv2.imwrite("debug_test.png", filtered)
    print("Filtrelenmiş görsel 'debug_test.png' adıyla kaydedildi.")

if __name__ == "__main__":
    main()