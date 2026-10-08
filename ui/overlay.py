from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy, QSizeGrip
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QPainter, QColor, QPen

class VisualSizeGrip(QSizeGrip):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        self.is_hovered = False

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        line_color = QColor(0, 195, 255, 220) if self.is_hovered else QColor(255, 255, 255, 70)
        pen = QPen(line_color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        w, h = self.width(), self.height()
        painter.drawLine(w - 3, h - 1, w - 1, h - 3)
        painter.drawLine(w - 7, h - 1, w - 1, h - 7)
        painter.drawLine(w - 11, h - 1, w - 1, h - 11)


class TranslationOverlay(QWidget):
    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.drag_position = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(220, 80)

        init_w = self.config.get("overlay_width", 380)
        init_h = self.config.get("overlay_height", 120)
        self.resize(init_w, init_h)

        self.init_ui()
        self.apply_style()

    def init_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # Ana Kart
        self.card = QFrame(self)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(12, 8, 4, 4)
        self.card_layout.setSpacing(4)

        # Üst Başlık (Rozet + Kapat)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 4, 0)
        
        self.engine_badge = QLabel("⚡ YEREL ÇEVİRİ", self.card)
        self.engine_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold;")
        header.addWidget(self.engine_badge)
        header.addStretch()

        self.close_btn = QPushButton("×", self.card)
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888899;
                font-size: 16px;
                font-weight: bold;
                border: none;
                margin-top: -4px;
            }
            QPushButton:hover { color: #ff5555; }
        """)
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)

        self.card_layout.addLayout(header)

        # Orijinal OCR Metni (Seçeneğe bağlı gösterilir)
        self.original_label = QLabel(self.card)
        self.original_label.setWordWrap(True)
        self.original_label.setStyleSheet("""
            color: #8c8c9e; 
            font-size: 11px; 
            font-style: italic; 
            background: transparent; 
            border: none;
            padding-bottom: 2px;
        """)
        self.original_label.hide()
        self.card_layout.addWidget(self.original_label)

        # İçerik Alanı
        self.content_container = QWidget(self.card)
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)

        # Çeviri Metni
        self.trans_label = QLabel("Çeviri bekleniyor...", self.content_container)
        self.trans_label.setWordWrap(True)
        self.trans_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.content_layout.addWidget(self.trans_label, stretch=3)

        # Kelimeler Paneli
        self.vocab_container = QWidget(self.content_container)
        self.vocab_layout = QVBoxLayout(self.vocab_container)
        self.vocab_layout.setContentsMargins(0, 0, 0, 0)
        self.vocab_layout.setSpacing(4)
        self.content_layout.addWidget(self.vocab_container, stretch=2)

        self.card_layout.addWidget(self.content_container)

        # Alt Satır & Boyutlandırma Köşesi
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 2, 2)
        footer.addStretch()

        self.size_grip = VisualSizeGrip(self)
        footer.addWidget(self.size_grip)

        self.card_layout.addLayout(footer)
        self.root_layout.addWidget(self.card)

    def apply_style(self):
        bg = self.config.get("bg_color", "18, 18, 24")
        opacity = self.config.get("bg_opacity", 0.88)
        radius = int(self.config.get("border_radius", 8))
        border = self.config.get("border_color", "rgba(255, 255, 255, 0.15)")
        text_color = self.config.get("text_color", "#ffffff")
        font_family = self.config.get("font_family", "Segoe UI")
        font_size = int(self.config.get("font_size", 13))

        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({bg}, {opacity});
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)

        self.trans_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: '{font_family}';
                font-size: {font_size}px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)

    def update_settings(self, new_config: dict):
        self.config = new_config
        self.apply_style()

    def update_content(self, data: dict):
        engine = data.get("engine", "local")
        self.engine_badge.setText("✦ GEMINI AI" if engine == "gemini" else "⚡ YEREL ÇEVİRİ")
        self.engine_badge.setStyleSheet(
            "color: #00c3ff; font-size: 10px; font-weight: bold;" if engine == "gemini" 
            else "color: #00ffaa; font-size: 10px; font-weight: bold;"
        )

        # 1. Orijinal Metin Kontrolü
        original_text = data.get("original_text", "")
        if self.config.get("show_original_text", False) and original_text:
            self.original_label.setText(f'"{original_text}"')
            self.original_label.show()
        else:
            self.original_label.hide()

        # 2. Çeviri Metni
        translated = data.get("translated_text", "")
        self.trans_label.setText(translated if translated else "...")

        # 3. Kelimeler
        while self.vocab_layout.count():
            item = self.vocab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        mode = self.config.get("layout_mode", "bottom_words")
        show_vocab = self.config.get("show_vocab", True)
        vocab_list = data.get("vocabulary", [])
        max_count = int(self.config.get("vocab_max_count", 2))
        show_level = self.config.get("show_vocab_level", True)

        if mode == "minimal" or not show_vocab or not vocab_list or max_count <= 0:
            self.vocab_container.hide()
            return

        active_words = vocab_list[:max_count]
        if not active_words:
            self.vocab_container.hide()
            return

        if mode == "side_words":
            self.content_layout.setDirection(QHBoxLayout.Direction.LeftToRight)
            self.vocab_container.show()
        else:
            self.content_layout.setDirection(QHBoxLayout.Direction.TopToBottom)
            self.vocab_container.show()

        for item in active_words:
            w = item.get("word", "")
            m = item.get("meaning", "")
            lvl = item.get("level", "")

            level_str = f" <span style='color:#ffd700; font-size:10px;'>[{lvl}]</span>" if (show_level and lvl) else ""
            html = f"<span style='color:#00e5ff; font-weight:bold;'>{w}</span>: <span style='color:#cccccc;'>{m}</span>{level_str}"
            
            lbl = QLabel(html, self.vocab_container)
            lbl.setStyleSheet("background: transparent; border: none; font-size: 11px;")
            self.vocab_layout.addWidget(lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.config["overlay_width"] = self.width()
        self.config["overlay_height"] = self.height()