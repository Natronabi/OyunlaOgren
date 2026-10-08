import sys
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QApplication

class ScreenSelector(QWidget):
    """
    Kullanıcının ekranda fareyle sürükleyip OCR alanını (ROI)
    seçmesini sağlayan tam ekran yarı şeffaf araç.
    """
    area_selected = pyqtSignal(tuple)  # (x, y, width, height) fırlatır

    def __init__(self):
        super().__init__()
        # Çerçevesiz, her zaman üstte ve tam ekran pencere ayarları
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False

    def start_selection(self):
        """Tüm ekranı kaplayacak şekilde seçiciyi açar."""
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
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
            
            selected_rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Yanlışlıkla yapılan ufak tıklamaları engelle (min 10x10 piksel)
            if selected_rect.width() > 10 and selected_rect.height() > 10:
                coords = (
                    selected_rect.x(),
                    selected_rect.y(),
                    selected_rect.width(),
                    selected_rect.height()
                )
                self.hide()
                self.area_selected.emit(coords)
            else:
                self.hide()

    def keyPressEvent(self, event):
        # ESC tuşuna basılırsa seçimi iptal et
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 1. Ekranın tamamını yarı şeffaf siyahla kapla
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        # 2. Seçim yapılıyorsa kutunun içini aydınlat ve çerçeve çiz
        if self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Seçilen alanın arkasındaki şeffaflığı temizle (aydınlık göster)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Çerçeve çizgisi (Parlak mavi neon)
            pen = QPen(QColor(0, 162, 255), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)