import sys
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QGraphicsDropShadowEffect, QHBoxLayout, QFrame, QPushButton, QApplication
)

class TranslationOverlay(QWidget):
    def __init__(self, config: dict = None):
        super().__init__()
        
        self.config = {
            "font_family": "Segoe UI",
            "font_size": 13,
            "text_color": "#ffffff",
            "bg_color": "18, 18, 24",
            "bg_opacity": 0.88,
            "border_color": "rgba(255, 255, 255, 0.15)",
            "border_radius": 8
        }
        if config:
            self.config.update(config)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.drag_position = QPoint()
        self.init_ui()

    def init_ui(self):
        self.resize(550, 100)
        self.setMinimumWidth(320)
        
        self.container = QFrame(self)
        self.apply_style()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 190))
        shadow.setOffset(0, 2)
        self.container.setGraphicsEffect(shadow)

        # Kompakt yerleşim: Boşluklar minimuma çekildi
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(10, 6, 8, 8)
        layout.setSpacing(4)

        # Üst Satır: Rozet ve Tam Köşe Kapatma Butonu
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        self.engine_badge = QLabel("⚡ GameLingo", self)
        self.engine_badge.setStyleSheet("color: #00d2ff; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        header_layout.addWidget(self.engine_badge)

        header_layout.addStretch()

        # Sağ üst köşeye sıfırlanmış ufak çarpı butonu
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: #777777;
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                color: #ff4d4d;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        header_layout.addWidget(self.close_btn)

        layout.addLayout(header_layout)

        # Çeviri Metni: Kenarlara kadar yayılır
        self.translation_label = QLabel("Altyazı bekleniyor...", self)
        self.apply_font_style()
        self.translation_label.setWordWrap(True)
        layout.addWidget(self.translation_label)

        # Kelime Kartları
        self.vocab_container = QWidget(self)
        self.vocab_container.setStyleSheet("background: transparent; border: none;")
        self.vocab_layout = QHBoxLayout(self.vocab_container)
        self.vocab_layout.setContentsMargins(0, 2, 0, 0)
        self.vocab_layout.setSpacing(6)
        layout.addWidget(self.vocab_container)
        self.vocab_container.hide()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

    def apply_style(self):
        bg = self.config["bg_color"]
        opacity = self.config["bg_opacity"]
        radius = self.config["border_radius"]
        border = self.config["border_color"]
        
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({bg}, {opacity});
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)

    def apply_font_style(self):
        font_family = self.config["font_family"]
        font_size = self.config["font_size"]
        text_color = self.config["text_color"]

        self.translation_label.setFont(QFont(font_family, font_size, QFont.Weight.Medium))
        self.translation_label.setStyleSheet(f"""
            color: {text_color};
            background: transparent;
            border: none;
            line-height: 1.25;
            padding: 0px;
            margin: 0px;
        """)

    def update_settings(self, new_config: dict):
        self.config.update(new_config)
        self.apply_style()
        self.apply_font_style()
        self.update()

    def update_content(self, data: dict):
        engine = data.get("engine", "local").upper()
        translated = data.get("translated_text", "")
        vocabulary = data.get("vocabulary", [])

        if engine == "LOCAL":
            self.engine_badge.setText("⚡ YEREL (0ms)")
            self.engine_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        else:
            self.engine_badge.setText("🧠 GEMINI")
            self.engine_badge.setStyleSheet("color: #00c3ff; font-size: 10px; font-weight: bold; background: transparent; border: none;")

        self.translation_label.setText(translated)

        while self.vocab_layout.count():
            item = self.vocab_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if vocabulary:
            for item in vocabulary[:3]:
                word = item.get("word", "")
                meaning = item.get("meaning", "")
                level = item.get("level", "B2")

                chip = QLabel(f"<b>{word}</b> ({level}): {meaning}", self)
                chip.setStyleSheet("""
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #d8d8d8;
                    border: 1px solid rgba(255, 255, 255, 0.16);
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 11px;
                """)
                self.vocab_layout.addWidget(chip)
            self.vocab_container.show()
        else:
            self.vocab_container.hide()

        self.adjustSize()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()