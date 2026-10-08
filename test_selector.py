import sys
from PyQt6.QtWidgets import QApplication
from ui.selector import ScreenSelector

def on_area_picked(coords):
    x, y, w, h = coords
    print(f"\n[BAŞARILI] Seçilen Alan Koordinatları:")
    print(f"X: {x}, Y: {y}, Genişlik: {w}px, Yükseklik: {h}px")
    print(f"MORT formatı (Bölge): {coords}")
    sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("Alan seçici açılıyor... Fare ile bir alan çiz (İptal için ESC).")
    selector = ScreenSelector()
    selector.area_selected.connect(on_area_picked)
    selector.start_selection()
    
    sys.exit(app.exec())