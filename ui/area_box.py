from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor

class AreaPreviewFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # WindowTransparentForInput bayrağı işletim sistemi düzeyinde tıklamaları arkaya paslar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def show_box(self, x: int, y: int, w: int, h: int):
        self.setGeometry(x, y, w, h)
        self.show()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(0, 229, 255, 230), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 229, 255, 12))

        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)