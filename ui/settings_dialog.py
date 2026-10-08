from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QListWidget, QListWidgetItem, 
    QWidget, QFrame, QColorDialog, QRadioButton, QButtonGroup, 
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QFontDatabase
from core.config_manager import ConfigManager

class FontItemWidget(QWidget):
    favorite_toggled = pyqtSignal(str, bool)

    def __init__(self, font_name: str, is_fav: bool = False, parent=None):
        super().__init__(parent)
        self.font_name = font_name
        self.is_fav = is_fav

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(8)

        self.label = QLabel(font_name)
        self.label.setFont(QFont(font_name, 11))
        self.label.setStyleSheet("color: #e0e0e0; background: transparent;")
        layout.addWidget(self.label, stretch=1)

        self.star_btn = QPushButton()
        self.star_btn.setFixedSize(24, 24)
        self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_star_ui()
        self.star_btn.clicked.connect(self.toggle_favorite)
        layout.addWidget(self.star_btn)

    def update_star_ui(self):
        if self.is_fav:
            self.star_btn.setText("★")
            self.star_btn.setStyleSheet("QPushButton { color: #ffd700; font-size: 15px; border: none; background: transparent; }")
        else:
            self.star_btn.setText("☆")
            self.star_btn.setStyleSheet("QPushButton { color: #666677; font-size: 15px; border: none; background: transparent; } QPushButton:hover { color: #ffd700; }")

    def toggle_favorite(self):
        self.is_fav = not self.is_fav
        self.update_star_ui()
        self.favorite_toggled.emit(self.font_name, self.is_fav)


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    SAMPLE_DATA = [
        {"word": "whisper", "meaning": "fısıltı", "level": "B1"},
        {"word": "echo", "meaning": "yankılanmak", "level": "B1"},
        {"word": "ruins", "meaning": "harabeler", "level": "B2"},
        {"word": "ancient", "meaning": "kadim", "level": "B2"},
        {"word": "destiny", "meaning": "kader", "level": "C1"}
    ]

    def __init__(self, current_config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GameLingo - Görünüm & Düzen Ayarları")
        self.setFixedSize(520, 710)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.config = current_config.copy() if current_config else ConfigManager.load_config()
        self.favorites = set(self.config.get("favorite_fonts", ["Segoe UI", "Arial"]))
        self.all_fonts = sorted(list(set(QFontDatabase.families())))

        self.init_ui()
        self.refresh_font_list()
        self.update_preview()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #121216;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #b0b0b8;
                font-size: 12px;
            }
            QListWidget {
                background-color: #181820;
                border: 1px solid #33333e;
                border-radius: 6px;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #282836;
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #2a2a35;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #00c3ff;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }
            QPushButton.step-btn {
                background-color: #252532;
                color: #ffffff;
                font-weight: bold;
                font-size: 15px;
                border: 1px solid #3e3e50;
                border-radius: 5px;
            }
            QPushButton.step-btn:hover { background-color: #3b3b4f; border-color: #00c3ff; }
            QRadioButton, QCheckBox {
                color: #d0d0d8;
                font-size: 12px;
            }
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                background-color: #00c3ff;
                border: 1px solid #00c3ff;
            }
            QComboBox {
                background-color: #1e1e24;
                color: #ffffff;
                border: 1px solid #33333e;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        # 1. CANLI ÖNİZLEME ALANI
        lbl_prev = QLabel("Canlı Görünüm & Düzen Önizlemesi:")
        lbl_prev.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(lbl_prev)

        self.preview_frame = QFrame(self)
        self.preview_frame.setMinimumHeight(105)
        
        self.frame_inner = QVBoxLayout(self.preview_frame)
        self.frame_inner.setContentsMargins(12, 10, 12, 10)
        self.frame_inner.setSpacing(4)

        self.preview_badge = QLabel("⚡ YEREL ÇEVİRİ", self.preview_frame)
        self.preview_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold;")
        self.frame_inner.addWidget(self.preview_badge)

        # Canlı Önizlemede Orijinal Metin
        self.preview_original = QLabel('"What do these whispers echoing in the dark ruins mean?"', self.preview_frame)
        self.preview_original.setStyleSheet("color: #8c8c9e; font-size: 11px; font-style: italic; background: transparent; border: none;")
        self.frame_inner.addWidget(self.preview_original)

        self.preview_content = QWidget(self.preview_frame)
        self.content_dir = QHBoxLayout(self.preview_content)
        self.content_dir.setContentsMargins(0, 0, 0, 0)
        self.content_dir.setSpacing(10)

        self.preview_trans = QLabel("Karanlık harabelerde yankılanan bu fısıltılar ne anlama geliyor?", self.preview_content)
        self.preview_trans.setWordWrap(True)
        self.content_dir.addWidget(self.preview_trans, stretch=3)

        self.preview_vocab_box = QWidget(self.preview_content)
        self.preview_vocab_layout = QVBoxLayout(self.preview_vocab_box)
        self.preview_vocab_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_vocab_layout.setSpacing(2)
        self.content_dir.addWidget(self.preview_vocab_box, stretch=2)

        self.frame_inner.addWidget(self.preview_content)
        layout.addWidget(self.preview_frame)

        # 2. DÜZEN ŞABLONLARI
        lbl_modes = QLabel("Görünüm Modu:")
        lbl_modes.setStyleSheet("font-weight: bold; color: #ffffff;")
        layout.addWidget(lbl_modes)

        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)

        self.rb_bottom = QRadioButton("Alt Kelimeler")
        self.rb_side = QRadioButton("Yan Panel")
        self.rb_minimal = QRadioButton("Sadece Çeviri")

        self.mode_group.addButton(self.rb_bottom, 1)
        self.mode_group.addButton(self.rb_side, 2)
        self.mode_group.addButton(self.rb_minimal, 3)

        current_mode = self.config.get("layout_mode", "bottom_words")
        if current_mode == "side_words":
            self.rb_side.setChecked(True)
        elif current_mode == "minimal":
            self.rb_minimal.setChecked(True)
        else:
            self.rb_bottom.setChecked(True)

        self.mode_group.buttonClicked.connect(self.on_mode_changed)

        mode_row.addWidget(self.rb_bottom)
        mode_row.addWidget(self.rb_side)
        mode_row.addWidget(self.rb_minimal)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # 3. KELİME & ORİJİNAL METİN SEÇENEKLERİ
        extra_opt_row = QHBoxLayout()
        lbl_v_count = QLabel("Kelime:")
        self.vocab_combo = QComboBox(self)
        self.vocab_combo.addItems(["En Önemli 2", "En Önemli 3", "En Önemli 5"])
        curr_cnt = self.config.get("vocab_max_count", 2)
        idx = 0 if curr_cnt == 2 else (1 if curr_cnt == 3 else 2)
        self.vocab_combo.setCurrentIndex(idx)
        self.vocab_combo.currentIndexChanged.connect(self.on_vocab_count_changed)

        self.cb_level = QCheckBox("Seviyeyi Göster [B1]")
        self.cb_level.setChecked(self.config.get("show_vocab_level", True))
        self.cb_level.toggled.connect(self.on_level_toggled)

        self.cb_original = QCheckBox("Orijinal Metni Göster")
        self.cb_original.setChecked(self.config.get("show_original_text", False))
        self.cb_original.toggled.connect(self.on_original_toggled)

        extra_opt_row.addWidget(lbl_v_count)
        extra_opt_row.addWidget(self.vocab_combo)
        extra_opt_row.addSpacing(10)
        extra_opt_row.addWidget(self.cb_level)
        extra_opt_row.addSpacing(10)
        extra_opt_row.addWidget(self.cb_original)
        extra_opt_row.addStretch()
        layout.addLayout(extra_opt_row)

        # 4. YAZI BOYUTU
        size_box = QFrame(self)
        size_layout = QHBoxLayout(size_box)
        size_layout.setContentsMargins(0, 2, 0, 2)
        size_layout.setSpacing(8)

        lbl_size = QLabel("Yazı Boyutu:")
        lbl_size.setFixedWidth(75)
        
        btn_minus = QPushButton("-", size_box)
        btn_minus.setProperty("class", "step-btn")
        btn_minus.setFixedSize(28, 28)
        btn_minus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_minus.clicked.connect(self.decrement_font_size)

        self.size_slider = QSlider(Qt.Orientation.Horizontal, size_box)
        self.size_slider.setRange(10, 30)
        self.size_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        current_size = int(self.config.get("font_size", 13))
        self.size_slider.setValue(current_size)
        self.size_slider.valueChanged.connect(self.on_font_size_changed)

        btn_plus = QPushButton("+", size_box)
        btn_plus.setProperty("class", "step-btn")
        btn_plus.setFixedSize(28, 28)
        btn_plus.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_plus.clicked.connect(self.increment_font_size)

        self.size_val_lbl = QLabel(f"{current_size}px", size_box)
        self.size_val_lbl.setFixedWidth(40)
        self.size_val_lbl.setStyleSheet("font-weight: bold; color: #00c3ff;")

        size_layout.addWidget(lbl_size)
        size_layout.addWidget(btn_minus)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(btn_plus)
        size_layout.addWidget(self.size_val_lbl)
        layout.addWidget(size_box)

        # 5. FONT LİSTESİ
        lbl_font_title = QLabel("Yazı Tipi (★ Favoriler Üstte):")
        layout.addWidget(lbl_font_title)

        self.font_list_widget = QListWidget(self)
        self.font_list_widget.setFixedHeight(95)
        self.font_list_widget.itemClicked.connect(self.on_font_item_clicked)
        layout.addWidget(self.font_list_widget)

        # 6. RENK & OPAKLIK
        color_row = QHBoxLayout()
        lbl_col = QLabel("Yazı Rengi:")
        lbl_col.setFixedWidth(75)
        self.text_color_btn = QPushButton(self)
        self.text_color_btn.setFixedHeight(26)
        self.text_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_btn_color(self.text_color_btn, self.config.get("text_color", "#ffffff"))
        self.text_color_btn.clicked.connect(self.choose_text_color)
        color_row.addWidget(lbl_col)
        color_row.addWidget(self.text_color_btn)
        layout.addLayout(color_row)

        op_row = QHBoxLayout()
        lbl_op = QLabel("Opaklık:")
        lbl_op.setFixedWidth(75)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        curr_op = int(float(self.config.get("bg_opacity", 0.88)) * 100)
        self.opacity_slider.setValue(curr_op)
        self.opacity_val_lbl = QLabel(f"%{curr_op}")
        self.opacity_val_lbl.setFixedWidth(40)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        op_row.addWidget(lbl_op)
        op_row.addWidget(self.opacity_slider)
        op_row.addWidget(self.opacity_val_lbl)
        layout.addLayout(op_row)

        # Köşe Ovalliği
        rad_row = QHBoxLayout()
        lbl_rad = QLabel("Köşe Ovalliği:")
        lbl_rad.setFixedWidth(75)
        self.rad_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.rad_slider.setRange(0, 24)
        self.rad_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        curr_rad = int(self.config.get("border_radius", 8))
        self.rad_slider.setValue(curr_rad)
        self.rad_val_lbl = QLabel(f"{curr_rad}px")
        self.rad_val_lbl.setFixedWidth(40)
        self.rad_slider.valueChanged.connect(self.on_radius_changed)
        rad_row.addWidget(lbl_rad)
        rad_row.addWidget(self.rad_slider)
        rad_row.addWidget(self.rad_val_lbl)
        layout.addLayout(rad_row)

        # Kaydet Butonu
        self.save_btn = QPushButton("Kaydet ve Uygula", self)
        self.save_btn.setFixedHeight(34)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c3ff;
                color: #000000;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #33d0ff; }
        """)
        self.save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(self.save_btn)

    def on_mode_changed(self, btn):
        if btn == self.rb_minimal:
            self.config["layout_mode"] = "minimal"
            self.config["show_vocab"] = False
        elif btn == self.rb_side:
            self.config["layout_mode"] = "side_words"
            self.config["show_vocab"] = True
        else:
            self.config["layout_mode"] = "bottom_words"
            self.config["show_vocab"] = True

        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_vocab_count_changed(self, idx):
        counts = [2, 3, 5]
        self.config["vocab_max_count"] = counts[idx]
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_level_toggled(self, checked):
        self.config["show_vocab_level"] = checked
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_original_toggled(self, checked):
        self.config["show_original_text"] = checked
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_radius_changed(self, val):
        self.rad_val_lbl.setText(f"{val}px")
        self.config["border_radius"] = val
        self.update_preview()
        self.settings_changed.emit(self.config)

    def update_preview(self):
        bg = self.config.get("bg_color", "18, 18, 24")
        opacity = self.config.get("bg_opacity", 0.88)
        radius = int(self.config.get("border_radius", 8))
        border = self.config.get("border_color", "rgba(255, 255, 255, 0.15)")
        text_color = self.config.get("text_color", "#ffffff")
        font_family = self.config.get("font_family", "Segoe UI")
        font_size = int(self.config.get("font_size", 13))

        mode = self.config.get("layout_mode", "bottom_words")
        show_vocab = self.config.get("show_vocab", True)
        max_count = int(self.config.get("vocab_max_count", 2))
        show_level = self.config.get("show_vocab_level", True)
        show_orig = self.config.get("show_original_text", False)

        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({bg}, {opacity});
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)

        # Orijinal metin kutucuğunu ayara göre aç/kapat
        if show_orig:
            self.preview_original.show()
        else:
            self.preview_original.hide()

        self.preview_trans.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: '{font_family}';
                font-size: {font_size}px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)

        while self.preview_vocab_layout.count():
            item = self.preview_vocab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if mode == "minimal" or not show_vocab:
            self.preview_vocab_box.hide()
        elif mode == "side_words":
            self.content_dir.setDirection(QHBoxLayout.Direction.LeftToRight)
            self.preview_vocab_box.show()
        else:
            self.content_dir.setDirection(QHBoxLayout.Direction.TopToBottom)
            self.preview_vocab_box.show()

        if mode != "minimal" and show_vocab:
            active_items = self.SAMPLE_DATA[:max_count]
            for itm in active_items:
                w, m, lvl = itm["word"], itm["meaning"], itm["level"]
                lvl_badge = f" <span style='color:#ffd700; font-size:10px;'>[{lvl}]</span>" if show_level else ""
                html = f"<span style='color:#00e5ff; font-weight:bold;'>{w}</span>: <span style='color:#bbbbcc;'>{m}</span>{lvl_badge}"
                lbl = QLabel(html, self.preview_vocab_box)
                lbl.setStyleSheet("background: transparent; border: none; font-size: 11px;")
                self.preview_vocab_layout.addWidget(lbl)

    def decrement_font_size(self):
        self.size_slider.setValue(max(10, self.size_slider.value() - 1))

    def increment_font_size(self):
        self.size_slider.setValue(min(30, self.size_slider.value() + 1))

    def on_font_size_changed(self, val):
        self.size_val_lbl.setText(f"{val}px")
        self.config["font_size"] = val
        self.update_preview()
        self.settings_changed.emit(self.config)

    def refresh_font_list(self):
        selected_font = self.config.get("font_family", "Segoe UI")
        self.font_list_widget.clear()

        favs = [f for f in self.all_fonts if f in self.favorites]
        non_favs = [f for f in self.all_fonts if f not in self.favorites]

        for f_name in (favs + non_favs):
            item = QListWidgetItem(self.font_list_widget)
            item.setData(Qt.ItemDataRole.UserRole, f_name)
            row_widget = FontItemWidget(f_name, is_fav=(f_name in self.favorites))
            row_widget.favorite_toggled.connect(self.on_favorite_toggled)

            item.setSizeHint(row_widget.sizeHint())
            self.font_list_widget.addItem(item)
            self.font_list_widget.setItemWidget(item, row_widget)

            if f_name == selected_font:
                self.font_list_widget.setCurrentItem(item)

    def on_favorite_toggled(self, font_name: str, is_fav: bool):
        if is_fav:
            self.favorites.add(font_name)
        else:
            self.favorites.discard(font_name)
        self.config["favorite_fonts"] = list(self.favorites)
        self.refresh_font_list()

    def on_font_item_clicked(self, item: QListWidgetItem):
        self.config["font_family"] = item.data(Qt.ItemDataRole.UserRole)
        self.update_preview()
        self.settings_changed.emit(self.config)

    def update_btn_color(self, btn: QPushButton, hex_code: str):
        is_light = hex_code.lower() in ["#ffffff", "#fff", "#f0f0f0"]
        btn.setStyleSheet(f"QPushButton {{ background-color: {hex_code}; color: {'#111' if is_light else '#fff'}; font-weight: bold; border-radius: 4px; border: 1px solid #444; }}")
        btn.setText(hex_code.upper())

    def choose_text_color(self):
        color = QColorDialog.getColor(QColor(self.config.get("text_color", "#ffffff")), self, "Yazı Rengi Seç")
        if color.isValid():
            hex_val = color.name()
            self.config["text_color"] = hex_val
            self.update_btn_color(self.text_color_btn, hex_val)
            self.update_preview()
            self.settings_changed.emit(self.config)

    def on_opacity_changed(self, val):
        self.opacity_val_lbl.setText(f"%{val}")
        self.config["bg_opacity"] = round(val / 100.0, 2)
        self.update_preview()
        self.settings_changed.emit(self.config)

    def save_and_close(self):
        ConfigManager.save_config(self.config)
        self.accept()