import sys
from PyQt6.QtWidgets import QApplication
from ui.selector import ScreenSelector
from ui.overlay import TranslationOverlay
from core.auto_watcher import AutoWatcherWorker

class LivePipelineTest:
    def __init__(self):
        self.selector = ScreenSelector()
        self.overlay = TranslationOverlay()
        self.watcher = None

        self.selector.area_selected.connect(self.on_area_selected)

    def start(self):
        print("\n=== GAMELINGO CANLI TEST ===")
        print("1. Fareyle ekranda metin içeren bir alanı kutu içine al (İptal için ESC).")
        self.selector.start_selection()

    def on_area_selected(self, coords):
        print(f"\n[Alan Seçildi] Koordinatlar: {coords}")
        
        # Overlay'i seçilen alanın hemen üstüne yerleştir
        x, y, w, h = coords
        self.overlay.move(x, max(30, y - 110))
        self.overlay.show()

        # Otomatik takip motorunu başlat (0ms Yerel Motor ile)
        self.watcher = AutoWatcherWorker(roi_coords=coords, interval=0.5, engine="local")
        self.watcher.translation_ready.connect(self.overlay.update_content)
        self.watcher.status_updated.connect(lambda msg: print(f"[Watcher] {msg}"))
        self.watcher.start()
        print("\n[Canlı Çeviri Devrede] Seçtiğin alandaki metni değiştirdiğinde çeviri anında overlay'e gelecek.\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pipeline = LivePipelineTest()
    pipeline.start()
    sys.exit(app.exec())