import sys
import mss
import numpy as np
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QImage, QPixmap, QGuiApplication
from PyQt6.QtWidgets import QWidget, QApplication


class ScreenSelector(QWidget):
    area_selected = pyqtSignal(tuple)  # (phys_x, phys_y, phys_w, phys_h)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.frozen_pixmap = None
        self.img_w = 0
        self.img_h = 0

    def start_selection(self):
        """Masaüstünün tam fiziksel ekran görüntüsünü alıp dondurur."""
        screen = QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            raw_bytes = sct_img.raw
            qimg = QImage(raw_bytes, sct_img.width, sct_img.height, QImage.Format.Format_ARGB32)
            self.frozen_pixmap = QPixmap.fromImage(qimg)
            self.img_w = sct_img.width
            self.img_h = sct_img.height

        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False

        # Pencereyi doğrudan monitörün tam mantıksal geometrisine yerleştir
        self.setGeometry(screen_geo)
        self.showFullScreen()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = self.start_pos
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_pos = event.pos()
            self.hide()

            rect = QRect(self.start_pos, self.end_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                # Ekranda çizilen alanı fiziksel monitör oranına dönüştür
                scale_x = self.img_w / float(self.width())
                scale_y = self.img_h / float(self.height())

                phys_x = int(round(rect.x() * scale_x))
                phys_y = int(round(rect.y() * scale_y))
                phys_w = int(round(rect.width() * scale_x))
                phys_h = int(round(rect.height() * scale_y))

                # Ekran dışı kırpma koruması
                phys_x = max(0, min(phys_x, self.img_w - 1))
                phys_y = max(0, min(phys_y, self.img_h - 1))
                phys_w = min(phys_w, self.img_w - phys_x)
                phys_h = min(phys_h, self.img_h - phys_y)

                print(f"[MORT Seçici] Canvas: {self.width()}x{self.height()} -> Fiziksel: {self.img_w}x{self.img_h}")
                print(f"[MORT Seçici] Gönderilen Fiziksel ROI: X={phys_x}, Y={phys_y}, W={phys_w}, H={phys_h}")

                self.area_selected.emit((phys_x, phys_y, phys_w, phys_h))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)

        # 1. Dondurulan ekranı pencere sınırlarına tam çiz
        if self.frozen_pixmap:
            painter.drawPixmap(self.rect(), self.frozen_pixmap)

        # 2. Karartma katmanı
        painter.fillRect(self.rect(), QColor(0, 0, 0, 95))

        # 3. Seçilen kutunun içini aydınlat ve çerçeve çiz
        if self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()

            if self.frozen_pixmap:
                scale_x = self.img_w / float(self.width())
                scale_y = self.img_h / float(self.height())
                src_rect = QRect(
                    int(rect.x() * scale_x),
                    int(rect.y() * scale_y),
                    int(rect.width() * scale_x),
                    int(rect.height() * scale_y)
                )
                painter.drawPixmap(rect, self.frozen_pixmap, src_rect)

            pen = QPen(QColor(0, 229, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)