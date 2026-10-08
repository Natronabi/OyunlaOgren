from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QListWidget, QListWidgetItem, 
    QWidget, QFrame, QColorDialog, QRadioButton, QButtonGroup, 
    QCheckBox, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QKeySequence
from core.config_manager import ConfigManager

class KeyRecordButton(QPushButton):
    """Tıklandığında kullanıcının klavyeden basacağı tuşu kaydeden buton."""
    key_changed = pyqtSignal(str)

    def __init__(self, current_key="F9", parent=None):
        super().__init__(parent)
        self.current_key = current_key
        self.is_recording = False
        self.setText(self.current_key)
        self.setFixedSize(110, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.start_recording)

    def update_style(self):
        if self.is_recording:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ff4757;
                    color: #ffffff;
                    font-weight: bold;
                    border: 1px solid #ff6b81;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e28;
                    color: #00c3ff;
                    font-weight: bold;
                    border: 1px solid #3a3a4c;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #282836;
                    border-color: #00c3ff;
                }
            """)

    def start_recording(self):
        self.is_recording = True
        self.setText("Tuşa Basın...")
        self.update_style()
        self.setFocus()

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return  # Sadece mod tuşlarına basıldıysa tam tuş bekle

        seq = QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText)
        if seq:
            self.current_key = seq.upper()
            self.setText(self.current_key)
            self.is_recording = False
            self.update_style()
            self.key_changed.emit(self.current_key)
            self.clearFocus()

    def focusOutEvent(self, event):
        if self.is_recording:
            self.is_recording = False
            self.setText(self.current_key)
            self.update_style()
        super().focusOutEvent(event)


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
        {"word": "ruins", "meaning": "harabeler", "level": "B2"}
    ]

    def __init__(self, current_config: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GameLingo - Ayarlar")
        self.setFixedSize(520, 680)
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
            QTabWidget::pane {
                border: 1px solid #2a2a38;
                border-radius: 6px;
                background-color: #16161e;
                padding: 10px;
            }
            QTabBar::tab {
                background: #181822;
                color: #888899;
                padding: 6px 14px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #252536;
                color: #00c3ff;
                font-weight: bold;
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
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Tab Bileşeni (Görünüm vs Kısayollar)
        self.tabs = QTabWidget(self)
        
        # --- TAB 1: GÖRÜNÜM AYARLARI ---
        appearance_tab = QWidget()
        app_layout = QVBoxLayout(appearance_tab)
        app_layout.setContentsMargins(8, 8, 8, 8)
        app_layout.setSpacing(10)

        # Önizleme
        self.preview_frame = QFrame(appearance_tab)
        self.preview_frame.setMinimumHeight(100)
        self.frame_inner = QVBoxLayout(self.preview_frame)
        self.frame_inner.setContentsMargins(12, 8, 12, 8)
        self.frame_inner.setSpacing(4)

        self.preview_badge = QLabel("⚡ YEREL ÇEVİRİ", self.preview_frame)
        self.preview_badge.setStyleSheet("color: #00ffaa; font-size: 10px; font-weight: bold;")
        self.frame_inner.addWidget(self.preview_badge)

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
        app_layout.addWidget(self.preview_frame)

        # Modlar
        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.rb_bottom = QRadioButton("Alt Kelimeler")
        self.rb_side = QRadioButton("Yan Panel")
        self.rb_minimal = QRadioButton("Sadece Çeviri")

        self.mode_group.addButton(self.rb_bottom, 1)
        self.mode_group.addButton(self.rb_side, 2)
        self.mode_group.addButton(self.rb_minimal, 3)

        curr_mode = self.config.get("layout_mode", "bottom_words")
        if curr_mode == "side_words": self.rb_side.setChecked(True)
        elif curr_mode == "minimal": self.rb_minimal.setChecked(True)
        else: self.rb_bottom.setChecked(True)

        self.mode_group.buttonClicked.connect(self.on_mode_changed)
        mode_row.addWidget(self.rb_bottom)
        mode_row.addWidget(self.rb_side)
        mode_row.addWidget(self.rb_minimal)
        mode_row.addStretch()
        app_layout.addLayout(mode_row)

        # Seçenekler
        extra_row = QHBoxLayout()
        self.cb_original = QCheckBox("Orijinal Metni Göster")
        self.cb_original.setChecked(self.config.get("show_original_text", False))
        self.cb_original.toggled.connect(self.on_original_toggled)

        self.cb_level = QCheckBox("Seviyeyi Göster [B1]")
        self.cb_level.setChecked(self.config.get("show_vocab_level", True))
        self.cb_level.toggled.connect(self.on_level_toggled)

        extra_row.addWidget(self.cb_original)
        extra_row.addWidget(self.cb_level)
        extra_row.addStretch()
        app_layout.addLayout(extra_row)

        # Yazı Boyutu
        size_box = QFrame(appearance_tab)
        size_layout = QHBoxLayout(size_box)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)

        lbl_size = QLabel("Boyut:")
        btn_minus = QPushButton("-", size_box)
        btn_minus.setProperty("class", "step-btn")
        btn_minus.setFixedSize(26, 26)
        btn_minus.clicked.connect(lambda: self.size_slider.setValue(max(10, self.size_slider.value() - 1)))

        self.size_slider = QSlider(Qt.Orientation.Horizontal, size_box)
        self.size_slider.setRange(10, 30)
        curr_size = int(self.config.get("font_size", 13))
        self.size_slider.setValue(curr_size)
        self.size_slider.valueChanged.connect(self.on_font_size_changed)

        btn_plus = QPushButton("+", size_box)
        btn_plus.setProperty("class", "step-btn")
        btn_plus.setFixedSize(26, 26)
        btn_plus.clicked.connect(lambda: self.size_slider.setValue(min(30, self.size_slider.value() + 1)))

        self.size_val_lbl = QLabel(f"{curr_size}px")
        size_layout.addWidget(lbl_size)
        size_layout.addWidget(btn_minus)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(btn_plus)
        size_layout.addWidget(self.size_val_lbl)
        app_layout.addWidget(size_box)

        # Font Seçimi
        app_layout.addWidget(QLabel("Yazı Tipi (★ Favoriler):"))
        self.font_list_widget = QListWidget(appearance_tab)
        self.font_list_widget.setFixedHeight(85)
        self.font_list_widget.itemClicked.connect(self.on_font_item_clicked)
        app_layout.addWidget(self.font_list_widget)

        # Renk, Opaklık ve Ovallik
        sliders_box = QVBoxLayout()
        sliders_box.setSpacing(6)

        c_row = QHBoxLayout()
        c_row.addWidget(QLabel("Yazı Rengi:"))
        self.text_color_btn = QPushButton(appearance_tab)
        self.text_color_btn.setFixedHeight(24)
        self.update_btn_color(self.text_color_btn, self.config.get("text_color", "#ffffff"))
        self.text_color_btn.clicked.connect(self.choose_text_color)
        c_row.addWidget(self.text_color_btn)
        sliders_box.addLayout(c_row)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Opaklık:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, appearance_tab)
        self.opacity_slider.setRange(20, 100)
        curr_op = int(float(self.config.get("bg_opacity", 0.88)) * 100)
        self.opacity_slider.setValue(curr_op)
        self.opacity_val_lbl = QLabel(f"%{curr_op}")
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        op_row.addWidget(self.opacity_slider)
        op_row.addWidget(self.opacity_val_lbl)
        sliders_box.addLayout(op_row)

        rad_row = QHBoxLayout()
        rad_row.addWidget(QLabel("Köşe Ovalliği:"))
        self.rad_slider = QSlider(Qt.Orientation.Horizontal, appearance_tab)
        self.rad_slider.setRange(0, 24)
        curr_rad = int(self.config.get("border_radius", 8))
        self.rad_slider.setValue(curr_rad)
        self.rad_val_lbl = QLabel(f"{curr_rad}px")
        self.rad_slider.valueChanged.connect(self.on_radius_changed)
        rad_row.addWidget(self.rad_slider)
        rad_row.addWidget(self.rad_val_lbl)
        sliders_box.addLayout(rad_row)

        app_layout.addLayout(sliders_box)
        self.tabs.addTab(appearance_tab, "🎨 Görünüm & Düzen")

        # --- TAB 2: KISAYOL TUŞLARI ---
        hotkey_tab = QWidget()
        hk_layout = QVBoxLayout(hotkey_tab)
        hk_layout.setContentsMargins(16, 20, 16, 20)
        hk_layout.setSpacing(16)

        info_box = QLabel("Tuşları değiştirmek için butona tıklayıp klavyenizdeki yeni tuşa basın:")
        info_box.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        hk_layout.addWidget(info_box)

        # 1. Alan Seçme Tuşu
        row_sel = QHBoxLayout()
        lbl_s = QLabel("🎯 Oyun Alanını Seç:")
        lbl_s.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.btn_hk_select = KeyRecordButton(self.config.get("hotkey_select", "F9"), hotkey_tab)
        self.btn_hk_select.key_changed.connect(lambda k: self.config.update({"hotkey_select": k}))
        row_sel.addWidget(lbl_s)
        row_sel.addStretch()
        row_sel.addWidget(self.btn_hk_select)
        hk_layout.addLayout(row_sel)

        # 2. Canlı Takip Başlat / Durdur
        row_tog = QHBoxLayout()
        lbl_t = QLabel("▶ Canlı Takip (Başlat / Durdur):")
        lbl_t.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.btn_hk_toggle = KeyRecordButton(self.config.get("hotkey_toggle", "F10"), hotkey_tab)
        self.btn_hk_toggle.key_changed.connect(lambda k: self.config.update({"hotkey_toggle": k}))
        row_tog.addWidget(lbl_t)
        row_tog.addStretch()
        row_tog.addWidget(self.btn_hk_toggle)
        hk_layout.addLayout(row_tog)

        # 3. Overlay Göster / Gizle
        row_ov = QHBoxLayout()
        lbl_o = QLabel("👁 Çeviri Kutusunu Göster / Gizle:")
        lbl_o.setStyleSheet("color: #ffffff; font-weight: 500;")
        self.btn_hk_overlay = KeyRecordButton(self.config.get("hotkey_overlay", "F11"), hotkey_tab)
        self.btn_hk_overlay.key_changed.connect(lambda k: self.config.update({"hotkey_overlay": k}))
        row_ov.addWidget(lbl_o)
        row_ov.addStretch()
        row_ov.addWidget(self.btn_hk_overlay)
        hk_layout.addLayout(row_ov)

        hk_layout.addStretch()
        self.tabs.addTab(hotkey_tab, "⌨ Kısayol Tuşları")

        layout.addWidget(self.tabs)

        # Kaydet Butonu
        self.save_btn = QPushButton("Değişiklikleri Kaydet ve Kapat", self)
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

    def on_level_toggled(self, checked):
        self.config["show_vocab_level"] = checked
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_original_toggled(self, checked):
        self.config["show_original_text"] = checked
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_font_size_changed(self, val):
        self.size_val_lbl.setText(f"{val}px")
        self.config["font_size"] = val
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_opacity_changed(self, val):
        self.opacity_val_lbl.setText(f"%{val}")
        self.config["bg_opacity"] = round(val / 100.0, 2)
        self.update_preview()
        self.settings_changed.emit(self.config)

    def on_radius_changed(self, val):
        self.rad_val_lbl.setText(f"{val}px")
        self.config["border_radius"] = val
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
        show_orig = self.config.get("show_original_text", False)

        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba({bg}, {opacity});
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
        """)

        if show_orig: self.preview_original.show()
        else: self.preview_original.hide()

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
            for itm in self.SAMPLE_DATA[:2]:
                html = f"<span style='color:#00e5ff; font-weight:bold;'>{itm['word']}</span>: <span style='color:#bbbbcc;'>{itm['meaning']}</span>"
                lbl = QLabel(html, self.preview_vocab_box)
                lbl.setStyleSheet("background: transparent; border: none; font-size: 11px;")
                self.preview_vocab_layout.addWidget(lbl)

    def save_and_close(self):
        ConfigManager.save_config(self.config)
        self.accept()