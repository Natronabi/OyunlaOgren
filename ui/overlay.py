from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy, QSizeGrip, QScrollArea
)
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QColor, QPen


class ClickableSaveCard(QFrame):
    """F7 modunda parlayan, tıklandığında 'Kaydedildi' animasyonu gösteren kart."""
    clicked = pyqtSignal(object)

    def __init__(self, data: dict, item_type: str = "word", parent=None):
        super().__init__(parent)
        self.data = data
        self.item_type = item_type
        self.is_interactive = False
        self.is_saved = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(4, 2, 4, 2)
        self.main_lay.setSpacing(2)

        self.lbl_text = QLabel(self)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.main_lay.addWidget(self.lbl_text)

        self.lbl_toast = QLabel(self)
        self.lbl_toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_toast.hide()
        self.main_lay.addWidget(self.lbl_toast)

        self.apply_style()

    def set_content(self, text: str):
        if isinstance(text, dict):
            text = text.get("translated_text", "")
        self.lbl_text.setText(str(text) if text else "...")

    def set_interactive_mode(self, enabled: bool):
        self.is_interactive = enabled
        self.apply_style()

    def apply_style(self):
        if self.is_interactive:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1a1a28;
                    border: 2px solid #00e5ff;
                    border-radius: 6px;
                }
                QFrame:hover {
                    background-color: #222236;
                    border: 2px solid #33ffff;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                    border: none;
                }
            """)

    def mousePressEvent(self, event):
        if not self.is_interactive:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_saved:
                self.trigger_saved_feedback()
                self.clicked.emit(self.data)
            else:
                self.trigger_already_saved_feedback()

    def trigger_saved_feedback(self):
        self.is_saved = True
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 30, 20, 0.95);
                border: 2px solid #00ffaa;
                border-radius: 6px;
            }
        """)
        self.lbl_text.hide()
        self.lbl_toast.setText("✓ Kaydedildi")
        self.lbl_toast.setStyleSheet("color: #00ffaa; font-weight: bold; font-size: 12px;")
        self.lbl_toast.show()

        QTimer.singleShot(1000, self._restore_after_save)

    def trigger_already_saved_feedback(self):
        self.lbl_text.hide()
        self.lbl_toast.setText("⚠️ Zaten Kaydedildi")
        self.lbl_toast.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 11px;")
        self.lbl_toast.show()

        QTimer.singleShot(1000, self._restore_after_save)

    def _restore_after_save(self):
        self.lbl_toast.hide()
        self.lbl_text.show()
        if self.is_interactive:
            border_col = "#00ffaa" if self.is_saved else "#00e5ff"
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #1a1a28;
                    border: 2px solid {border_col};
                    border-radius: 6px;
                }}
            """)


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
        self.save_mode_active = False
        self.vocab_cards = []

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(260, 75)

        init_w = self.config.get("overlay_width", 420)
        init_h = self.config.get("overlay_height", 130)
        self.resize(init_w, init_h)

        self.init_ui()

        import os
        if os.name == "nt":
            import ctypes
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
            except Exception as e:
                print(f"[Overlay] Ekran yakalamadan hariç tutma başarısız: {e}")
        self.apply_style()

    def toggle_interactive_save_mode(self):
        self.save_mode_active = not self.save_mode_active

        if self.save_mode_active:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowTransparentForInput)
            self.show()
            self.activateWindow()

            if hasattr(self, "trans_card") and self.trans_card:
                self.trans_card.set_interactive_mode(True)
            for card in self.vocab_cards:
                card.set_interactive_mode(True)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowTransparentForInput)
            self.show()

            if hasattr(self, "trans_card") and self.trans_card:
                self.trans_card.set_interactive_mode(False)
            for card in self.vocab_cards:
                card.set_interactive_mode(False)

    def on_item_saved(self, data: dict):
        from core.vocabulary_db import VocabularyDB
        db = VocabularyDB()

        if data.get("type") == "sentence":
            raw_orig = data.get("original", "")
            db.add_word(
                word=raw_orig[:50] + ("..." if len(raw_orig) > 50 else ""),
                meaning=data.get("translation", ""),
                level="Cümle",
                game_title="Oyun",
                context_sentence=raw_orig
            )
        else:
            db.add_word(
                word=data.get("word", ""),
                meaning=data.get("meaning", ""),
                level=data.get("level", "B1"),
                game_title="Oyun",
                context_sentence=data.get("context_sentence", "")
            )

    def init_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # Dış Kart
        self.card = QFrame(self)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(10, 6, 6, 4)
        self.card_layout.setSpacing(2)

        # Üst Başlık (Rozet + Kapatma)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 2, 0)
        
        self.engine_badge = QLabel("⚡ YEREL ÇEVİRİ", self.card)
        self.engine_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold;")
        header.addWidget(self.engine_badge)
        header.addStretch()

        self.close_btn = QPushButton("×", self.card)
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888899;
                font-size: 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { color: #ff5555; }
        """)
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)

        self.card_layout.addLayout(header)

        # Kaydırılabilir İçerik Alanı
        self.scroll = QScrollArea(self.card)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 0.05);
                width: 4px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 195, 255, 0.4);
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 195, 255, 0.8);
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.content_vbox = QVBoxLayout(self.scroll_content)
        self.content_vbox.setContentsMargins(0, 2, 4, 2)
        self.content_vbox.setSpacing(4)

        # 1. ÇEVİRİ METNİ (EN ÜSTTE)
        sentence_data = {"type": "sentence", "original": "", "translation": ""}
        self.trans_card = ClickableSaveCard(sentence_data, item_type="sentence", parent=self.scroll_content)
        self.trans_card.set_content("Çeviri bekleniyor...")
        self.trans_card.clicked.connect(self.on_item_saved)
        self.content_vbox.addWidget(self.trans_card)

        # 2. ORİJİNAL OCR METNİ (VARSAYILAN OLARAK GİZLİ)
        self.original_label = QLabel(self.scroll_content)
        self.original_label.setWordWrap(True)
        self.original_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.original_label.setStyleSheet("""
            color: #8c8c9e; 
            font-size: 11px; 
            font-style: italic; 
            background: transparent; 
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            padding-top: 3px;
            margin-top: 2px;
        """)
        self.original_label.hide()
        self.content_vbox.addWidget(self.original_label)

        # 3. KELİMELER PANELİ
        self.vocab_container = QWidget(self.scroll_content)
        self.vocab_layout = QVBoxLayout(self.vocab_container)
        self.vocab_layout.setContentsMargins(0, 4, 0, 0)
        self.vocab_layout.setSpacing(3)
        self.vocab_container.hide()
        self.content_vbox.addWidget(self.vocab_container)

        self.scroll.setWidget(self.scroll_content)
        self.card_layout.addWidget(self.scroll)

        # Boyutlandırma Köşesi
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 2, 2)
        footer.addStretch()
        self.size_grip = VisualSizeGrip(self)
        footer.addWidget(self.size_grip)
        self.card_layout.addLayout(footer)

        self.root_layout.addWidget(self.card)

    def apply_style(self):
        # Arka plan açık mı? Kapalıysa tamamen şeffaf ve çerçevesiz
        enable_bg = self.config.get("enable_bg", True)

        if enable_bg:
            bg = self.config.get("bg_color", "18, 18, 24")
            bg_opacity = self.config.get("bg_opacity", 0.90)
            radius = int(self.config.get("border_radius", 8))
            border = self.config.get("border_color", "rgba(255, 255, 255, 0.15)")
            card_style = f"""
                QFrame {{
                    background-color: rgba({bg}, {bg_opacity});
                    border: 1px solid {border};
                    border-radius: {radius}px;
                }}
            """
        else:
            card_style = """
                QFrame {
                    background-color: transparent;
                    border: none;
                }
            """

        self.card.setStyleSheet(card_style)

        # Metin rengi ve saydamlığı (Hex -> RGBA)
        raw_text_color = self.config.get("text_color", "#ffffff")
        text_opacity = float(self.config.get("text_opacity", 1.0))
        font_family = self.config.get("font_family", "Segoe UI")
        font_size = int(self.config.get("font_size", 13))

        qcolor = QColor(raw_text_color)
        r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
        final_text_rgba = f"rgba({r}, {g}, {b}, {text_opacity})"

        if hasattr(self, "trans_card") and self.trans_card:
            self.trans_card.lbl_text.setStyleSheet(f"""
                QLabel {{
                    color: {final_text_rgba};
                    font-family: '{font_family}';
                    font-size: {font_size}px;
                    font-weight: 500;
                    line-height: 1.3;
                    background: transparent;
                    border: none;
                }}
            """)

    def update_settings(self, new_config: dict):
        self.config = new_config
        self.apply_style()

    def update_content(self, data: dict):
        if not data:
            return

        engine = data.get("engine", "local")
        self.engine_badge.setText("✦ GEMINI AI" if engine == "gemini" else "⚡ YEREL ÇEVİRİ")
        self.engine_badge.setStyleSheet(
            "color: #00c3ff; font-size: 10px; font-weight: bold;" if engine == "gemini" 
            else "color: #00ffaa; font-size: 10px; font-weight: bold;"
        )

        # 1. Çeviri Metnini Güvenli Çözümle ve Bas
        original_text = data.get("original_text", "")
        translated = data.get("translated_text", "")
        if isinstance(translated, dict):
            translated = translated.get("translated_text", "")
        translated_str = str(translated).strip() if translated else "..."

        self.trans_card.data = {
            "type": "sentence",
            "original": str(original_text),
            "translation": translated_str
        }
        self.trans_card.is_saved = False
        self.trans_card.set_content(translated_str)

        # 2. Orijinal Metin Kontrolü (Varsayılan olarak kapalı)
        if self.config.get("show_original_text", False) and original_text:
            self.original_label.setText(str(original_text))
            self.original_label.show()
        else:
            self.original_label.hide()

        # 3. Kelime Kartları Kontrolü
        while self.vocab_layout.count():
            item = self.vocab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.vocab_cards = []

        vocab_list = data.get("vocabulary", [])
        show_vocab = self.config.get("show_vocab", True)

        if not show_vocab or not vocab_list:
            self.vocab_container.hide()
        else:
            self.vocab_container.show()
            max_count = int(self.config.get("vocab_max_count", 3))
            for item in vocab_list[:max_count]:
                w = item.get("word", "")
                m = item.get("meaning", "")
                lvl = item.get("level", "B1")
                html = f"<span style='color:#00e5ff; font-weight:bold;'>{w}</span>: <span style='color:#cccccc;'>{m}</span>"
                
                word_data = {
                    "type": "word", "word": w, "meaning": m, 
                    "level": lvl, "context_sentence": original_text
                }
                card = ClickableSaveCard(word_data, item_type="word", parent=self.vocab_container)
                card.set_content(html)
                card.clicked.connect(self.on_item_saved)
                self.vocab_cards.append(card)
                self.vocab_layout.addWidget(card)

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