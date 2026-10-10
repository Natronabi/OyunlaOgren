from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QColor
from core.config_manager import ConfigManager
from core.vocabulary_db import VocabularyDB


class SaveableEntryCard(QFrame):
    """Metin ve yanında kompakt kaydet butonu olan kart."""
    saved_signal = pyqtSignal(dict)

    def __init__(self, data: dict, item_type: str = "word", parent=None):
        super().__init__(parent)
        self.data = data
        self.item_type = item_type
        self.db = VocabularyDB()
        self.is_saved = False

        self._setup_ui()

    def _setup_ui(self):
        self.main_lay = QHBoxLayout(self)
        self.main_lay.setContentsMargins(6, 4, 4, 4)
        self.main_lay.setSpacing(6)

        # Metin Alanı
        self.lbl_text = QLabel(self)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.main_lay.addWidget(self.lbl_text, stretch=1)

        # 0.5s Toast / Bildirim Etiketi
        self.lbl_toast = QLabel(self)
        self.lbl_toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_toast.hide()
        self.main_lay.addWidget(self.lbl_toast)

        # Minik Kaydet Butonu
        self.btn_save = QPushButton("🔖", self)
        self.btn_save.setFixedSize(22, 22)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setToolTip("Sözlüğe Kaydet")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #00c3ff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #00c3ff;
                color: #000000;
                border-color: #00c3ff;
            }
        """)
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.main_lay.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignTop)

        self.apply_style()

    def set_content(self, text: str):
        if isinstance(text, dict):
            text = text.get("translated_text", "")
        self.lbl_text.setText(str(text) if text else "")

    def apply_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.06);
                border-color: rgba(0, 195, 255, 0.3);
            }
        """)

    def on_save_clicked(self):
        # 1. Kontrol: Boş metin mi?
        target_word = self.data.get("word", "").strip() if self.item_type == "word" else self.data.get("original", "").strip()
        if not target_word:
            return

        # 2. Kontrol: Veritabanında zaten var mı?
        existing_words = [w["word"].strip().lower() for w in self.db.get_all_words()]
        if target_word.lower() in existing_words or self.is_saved:
            self.show_toast("⚠️ Zaten Kayıtlı", "#ffd700")
            return

        # 3. Kaydet
        if self.item_type == "sentence":
            raw_orig = self.data.get("original", "")
            self.db.add_word(
                word=raw_orig[:60] + ("..." if len(raw_orig) > 60 else ""),
                meaning=self.data.get("translation", ""),
                level="Cümle",
                game_title="Oyun Çevirisi",
                context_sentence=raw_orig
            )
        else:
            self.db.add_word(
                word=self.data.get("word", ""),
                meaning=self.data.get("meaning", ""),
                level=self.data.get("level", "B1"),
                game_title="Oyun",
                context_sentence=self.data.get("context_sentence", "")
            )

        self.is_saved = True
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("background-color: #00aa66; color: #ffffff; border: none; border-radius: 4px;")
        self.show_toast("✓ Saved", "#00ffaa")

    def show_toast(self, msg: str, color_hex: str):
        self.lbl_text.hide()
        self.lbl_toast.setText(msg)
        self.lbl_toast.setStyleSheet(f"color: {color_hex}; font-weight: bold; font-size: 11px;")
        self.lbl_toast.show()

        # 0.5 saniye sonra animasyonu bitirip metni geri aç
        QTimer.singleShot(500, self._hide_toast)

    def _hide_toast(self):
        self.lbl_toast.hide()
        self.lbl_text.show()


class TranslationOverlay(QWidget):
    EDGE_MARGIN = 8

    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.drag_position = QPoint()
        self.vocab_cards = []

        self.resizing_edge = None
        self.is_moving = False
        self.resize_start_geom = QRect()
        self.resize_start_pos = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 75)

        init_w = int(self.config.get("overlay_width", 500))
        init_h = int(self.config.get("overlay_height", 140))
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

    def init_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.card = QFrame(self)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(10, 6, 8, 6)
        self.card_layout.setSpacing(4)

        # Üst Başlık
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

        # QSplitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.card)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.15);
                width: 4px;
                margin: 4px 1px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #00c3ff;
            }
        """)

        # 1. Sol Bölme (Çeviri / Paragraf)
        self.left_scroll = QScrollArea(self.splitter)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setStyleSheet("background: transparent; border: none;")

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background: transparent;")
        self.left_vbox = QVBoxLayout(self.left_panel)
        self.left_vbox.setContentsMargins(0, 0, 4, 0)
        self.left_vbox.setSpacing(4)

        sentence_data = {"type": "sentence", "original": "", "translation": ""}
        self.trans_card = SaveableEntryCard(sentence_data, item_type="sentence", parent=self.left_panel)
        self.trans_card.set_content("Oyun çevirisi burada görünecek... (F10 ile başlatın)")
        self.left_vbox.addWidget(self.trans_card)

        self.original_label = QLabel(self.left_panel)
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
        self.left_vbox.addWidget(self.original_label)

        self.left_scroll.setWidget(self.left_panel)
        self.splitter.addWidget(self.left_scroll)

        # 2. Sağ Bölme (Özel Kelimeler)
        self.right_scroll = QScrollArea(self.splitter)
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.right_scroll.setStyleSheet("background: transparent; border: none;")

        self.vocab_container = QWidget()
        self.vocab_container.setStyleSheet("background: transparent;")
        self.vocab_layout = QVBoxLayout(self.vocab_container)
        self.vocab_layout.setContentsMargins(4, 0, 0, 0)
        self.vocab_layout.setSpacing(4)

        sample_data = {"type": "word", "word": "example", "meaning": "örnek", "level": "A1", "context_sentence": ""}
        self.sample_card = SaveableEntryCard(sample_data, item_type="word", parent=self.vocab_container)
        self.sample_card.set_content("<span style='color:#00e5ff; font-weight:bold;'>word</span> : <span style='color:#aaa;'>anlamı</span>")
        self.vocab_layout.addWidget(self.sample_card)

        self.right_scroll.setWidget(self.vocab_container)
        self.splitter.addWidget(self.right_scroll)

        self.splitter.setSizes([320, 180])
        self.card_layout.addWidget(self.splitter)

        self.root_layout.addWidget(self.card)

    def reset_to_waiting(self):
        if hasattr(self, "trans_card") and self.trans_card:
            self.trans_card.set_content("⏳ Çeviri bekleniyor...")
            self.trans_card.btn_save.setEnabled(False)
        if hasattr(self, "sample_card") and self.sample_card:
            self.sample_card.hide()
        if hasattr(self, "original_label"):
            self.original_label.hide()

    def apply_style(self):
        enable_bg = self.config.get("enable_bg", True)

        if enable_bg:
            bg = self.config.get("bg_color", "18, 18, 24")
            bg_opacity = self.config.get("bg_opacity", 0.65)
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
            card_style = "QFrame { background-color: transparent; border: none; }"

        self.card.setStyleSheet(card_style)

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
                    line-height: 1.35;
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
        if engine == "gemini":
            self.engine_badge.setText("✦ GEMINI AI")
            self.engine_badge.setStyleSheet("color: #00c3ff; font-size: 10px; font-weight: bold;")
        else:
            self.engine_badge.setText("⚡ YEREL ÇEVİRİ")
            self.engine_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold;")

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
        self.trans_card.btn_save.setEnabled(True)
        self.trans_card.btn_save.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #00c3ff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #00c3ff; color: #000000; }
        """)
        self.trans_card.set_content(translated_str)

        if self.config.get("show_original_text", False) and original_text:
            self.original_label.setText(str(original_text))
            self.original_label.show()
        else:
            self.original_label.hide()

        # Sağ Bölme Kelime Kartlarını Yenile
        while self.vocab_layout.count():
            item = self.vocab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.vocab_cards = []

        vocab_list = data.get("vocabulary", [])
        show_vocab = self.config.get("show_vocabulary", self.config.get("show_vocab", True))

        if not show_vocab or not vocab_list:
            self.right_scroll.hide()
        else:
            self.right_scroll.show()
            max_count = int(self.config.get("vocab_max_count", 4))
            for item in vocab_list[:max_count]:
                w = item.get("word", "")
                m = item.get("meaning", "")
                lvl = item.get("level", "B1")
                html = (
                    f"<span style='color:#00e5ff; font-weight:bold; font-size:12px;'>{w}</span> "
                    f"<span style='color:#777788; font-size:10px;'>[{lvl}]</span><br>"
                    f"<span style='color:#dddddd; font-size:11px;'>{m}</span>"
                )
                
                word_data = {
                    "type": "word", 
                    "word": w, 
                    "meaning": m, 
                    "level": lvl, 
                    "context_sentence": original_text
                }
                card = SaveableEntryCard(word_data, item_type="word", parent=self.vocab_container)
                card.set_content(html)
                self.vocab_cards.append(card)
                self.vocab_layout.addWidget(card)

    def _get_resize_edge(self, pos: QPoint):
        m = self.EDGE_MARGIN
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        if top and left: return "top-left"
        elif top and right: return "top-right"
        elif bottom and left: return "bottom-left"
        elif bottom and right: return "bottom-right"
        elif left: return "left"
        elif right: return "right"
        elif top: return "top"
        elif bottom: return "bottom"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing_edge = edge
                self.resize_start_geom = self.geometry()
                self.resize_start_pos = event.globalPosition().toPoint()
            else:
                self.is_moving = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        global_pos = event.globalPosition().toPoint()

        if self.resizing_edge:
            diff = global_pos - self.resize_start_pos
            geom = QRect(self.resize_start_geom)

            if "left" in self.resizing_edge:
                new_w = max(self.minimumWidth(), geom.width() - diff.x())
                geom.setLeft(geom.right() - new_w)
            if "right" in self.resizing_edge:
                geom.setWidth(max(self.minimumWidth(), geom.width() + diff.x()))
            if "top" in self.resizing_edge:
                new_h = max(self.minimumHeight(), geom.height() - diff.y())
                geom.setTop(geom.bottom() - new_h)
            if "bottom" in self.resizing_edge:
                geom.setHeight(max(self.minimumHeight(), geom.height() + diff.y()))

            self.setGeometry(geom)
            event.accept()
            return

        if self.is_moving:
            self.move(global_pos - self.drag_position)
            event.accept()
            return

        edge = self._get_resize_edge(event.pos())
        if edge in ("top-left", "bottom-right"): self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("top-right", "bottom-left"): self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge in ("left", "right"): self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge in ("top", "bottom"): self.setCursor(Qt.CursorShape.SizeVerCursor)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resizing_edge:
                self.config["overlay_width"] = self.width()
                self.config["overlay_height"] = self.height()
                ConfigManager.save_config(self.config)
            self.resizing_edge = None
            self.is_moving = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()