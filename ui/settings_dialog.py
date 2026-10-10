from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QColorDialog, QTabWidget, 
    QWidget, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent
from core.config_manager import ConfigManager


class HotkeyRecordButton(QPushButton):
    key_recorded = pyqtSignal(str)

    def __init__(self, current_key: str = "F9", parent=None):
        super().__init__(parent)
        self.current_key = current_key
        self.is_recording = False
        self.setText(self.current_key)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        self.clicked.connect(self.start_recording)

    def update_style(self):
        if self.is_recording:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2a1b1b;
                    color: #ff5555;
                    border: 2px solid #ff5555;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e28;
                    color: #00c3ff;
                    border: 1px solid #3d3d52;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #28283a;
                    border: 1px solid #00c3ff;
                }
            """)

    def start_recording(self):
        self.is_recording = True
        self.setText("Tuşa Basın...")
        self.update_style()
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Escape:
            self.stop_recording(self.current_key)
            return

        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        parts = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")

        key_name = ""
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            key_name = f"F{key - Qt.Key.Key_F1 + 1}"
        elif key == Qt.Key.Key_Space:
            key_name = "Space"
        elif key == Qt.Key.Key_Tab:
            key_name = "Tab"
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            key_name = "Enter"
        else:
            text = event.text().upper()
            if text and text.isprintable():
                key_name = text
            else:
                key_name = f"Key_{key}"

        parts.append(key_name)
        final_key = "+".join(parts) if len(parts) > 1 else key_name

        self.current_key = final_key
        self.stop_recording(final_key)

    def stop_recording(self, result_key: str):
        self.is_recording = False
        self.releaseKeyboard()
        self.setText(result_key)
        self.update_style()
        self.key_recorded.emit(result_key)


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GameLingo Ayarları")
        self.setFixedSize(510, 640)
        self.config = dict(current_config)

        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2a2a35;
                background-color: #16161e;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #1e1e26;
                color: #a0a0b0;
                padding: 8px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #282836;
                color: #00c3ff;
                font-weight: bold;
            }
        """)

        self.setup_appearance_tab()
        self.setup_engine_tab()
        self.setup_hotkeys_tab()
        self.setup_vocab_tab()

        root_layout.addWidget(self.tabs)

        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(4, 6, 4, 4)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #252532;
                color: #b0b0c0;
                border: 1px solid #3e3e50;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #353545; color: #ffffff; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        btn_box.addStretch()

        save_btn = QPushButton("💾 Kaydet ve Uygula")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c3ff;
                color: #000000;
                font-weight: bold;
                padding: 7px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #33d0ff; }
        """)
        save_btn.clicked.connect(self.save_and_close)
        btn_box.addWidget(save_btn)

        root_layout.addLayout(btn_box)

    # ---------------- 1. SEKME: GÖRÜNÜM & ÇAPA KÖŞESİ ----------------
    def setup_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        action_button_style = """
            QPushButton {
                background-color: #242434;
                color: #ffffff;
                border: 1px solid #44445c;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover { background-color: #2f2f45; border: 1px solid #00c3ff; }
        """

        self.chk_enable_bg = QCheckBox("Panel Arka Planı Etkin Olsun")
        self.chk_enable_bg.setStyleSheet("font-weight: bold; font-size: 13px; color: #00c3ff;")
        self.chk_enable_bg.setChecked(self.config.get("enable_bg", True))
        self.chk_enable_bg.toggled.connect(self.on_enable_bg_toggled)
        layout.addWidget(self.chk_enable_bg)

        bg_row = QHBoxLayout()
        bg_row.setSpacing(8)
        self.btn_bg_color = QPushButton("🎨  Arka Plan Rengini Değiştir...")
        self.btn_bg_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bg_color.setStyleSheet(action_button_style)
        self.btn_bg_color.clicked.connect(self.choose_bg_color)
        bg_row.addWidget(self.btn_bg_color, stretch=3)

        self.bg_preview = QLabel("       ")
        self.update_bg_preview()
        bg_row.addWidget(self.bg_preview, stretch=1)
        layout.addLayout(bg_row)

        # Varsayılan değer %65 yapıldı
        bg_opacity_val = int(self.config.get("bg_opacity", 0.65) * 100)
        self.lbl_bg_opacity = QLabel(f"Arka Plan Saydamlığı: %{bg_opacity_val}")
        self.slider_bg_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_bg_opacity.setRange(10, 100)
        self.slider_bg_opacity.setValue(bg_opacity_val)
        self.slider_bg_opacity.valueChanged.connect(self.on_bg_opacity_changed)
        layout.addWidget(self.lbl_bg_opacity)
        layout.addWidget(self.slider_bg_opacity)

        layout.addSpacing(6)

        layout.addWidget(QLabel("<b>Metin Rengi ve Saydamlık:</b>"))
        txt_row = QHBoxLayout()
        txt_row.setSpacing(8)
        self.btn_text_color = QPushButton("✏️  Yazı Rengini Değiştir...")
        self.btn_text_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_text_color.setStyleSheet(action_button_style)
        self.btn_text_color.clicked.connect(self.choose_text_color)
        txt_row.addWidget(self.btn_text_color, stretch=3)

        self.txt_preview = QLabel("       ")
        self.update_txt_preview()
        txt_row.addWidget(self.txt_preview, stretch=1)
        layout.addLayout(txt_row)

        text_opacity_val = int(self.config.get("text_opacity", 1.0) * 100)
        self.lbl_text_opacity = QLabel(f"Metin Saydamlığı: %{text_opacity_val}")
        self.slider_text_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_text_opacity.setRange(20, 100)
        self.slider_text_opacity.setValue(text_opacity_val)
        self.slider_text_opacity.valueChanged.connect(self.on_text_opacity_changed)
        layout.addWidget(self.lbl_text_opacity)
        layout.addWidget(self.slider_text_opacity)

        layout.addSpacing(6)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Metin Boyutu (px):"))
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(9, 36)
        self.spin_font_size.setValue(int(self.config.get("font_size", 13)))
        self.spin_font_size.valueChanged.connect(self.on_font_size_changed)
        font_row.addWidget(self.spin_font_size)
        font_row.addStretch()
        layout.addLayout(font_row)

        # Çapa Köşesi Seçimi
        anchor_row = QHBoxLayout()
        anchor_row.addWidget(QLabel("📌 Panel Çapa Köşesi (Sabit Nokta):"))
        self.combo_anchor = QComboBox()
        self.combo_anchor.addItem("Sol Üst (Varsayılan)", "top-left")
        self.combo_anchor.addItem("Sağ Üst", "top-right")
        self.combo_anchor.addItem("Sol Alt", "bottom-left")
        self.combo_anchor.addItem("Sağ Alt", "bottom-right")

        cur_anchor = self.config.get("anchor_corner", "top-left")
        idx_anchor = self.combo_anchor.findData(cur_anchor)
        if idx_anchor >= 0:
            self.combo_anchor.setCurrentIndex(idx_anchor)
        anchor_row.addWidget(self.combo_anchor)
        layout.addLayout(anchor_row)

        self.chk_orig = QCheckBox("Orijinal OCR Metnini Panelde Göster")
        self.chk_orig.setChecked(self.config.get("show_original_text", False))
        self.chk_orig.toggled.connect(self.on_orig_toggled)
        layout.addWidget(self.chk_orig)

        self.toggle_bg_controls(self.chk_enable_bg.isChecked())
        layout.addStretch()
        self.tabs.addTab(tab, "Görünüm")

    # ---------------- 2. SEKME: ÇEVİRİ & AI MOTORLARI ----------------
    def setup_engine_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Pencereyi Kapatma Tercihi:</b>"))
        close_row = QHBoxLayout()
        close_row.addWidget(QLabel("X Butonuna Basıldığında:"))
        self.combo_close = QComboBox()
        self.combo_close.addItem("Her Seferinde Sor", "ask")
        self.combo_close.addItem("Sistem Tepsisine Küçült", "tray")
        self.combo_close.addItem("Uygulamayı Tamamen Kapat", "exit")
        
        cur_close = self.config.get("close_behavior", "ask")
        idx_close = self.combo_close.findData(cur_close)
        if idx_close >= 0:
            self.combo_close.setCurrentIndex(idx_close)
        close_row.addWidget(self.combo_close)
        layout.addLayout(close_row)

        layout.addSpacing(6)

        layout.addWidget(QLabel("<b>Gemini AI Ayarları:</b>"))

        layout.addWidget(QLabel("Gemini API Anahtarı:"))
        api_row = QHBoxLayout()
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("AIzaSy...")
        self.api_input.setText(self.config.get("gemini_api_key", ""))
        self.api_input.textChanged.connect(self.on_api_key_changed)
        api_row.addWidget(self.api_input)

        self.btn_fetch_models = QPushButton("🔄 Modelleri Çek")
        self.btn_fetch_models.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch_models.setStyleSheet("""
            QPushButton {
                background-color: #242436;
                color: #00c3ff;
                border: 1px solid #3d3d52;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #2e2e46; border-color: #00c3ff; }
        """)
        self.btn_fetch_models.clicked.connect(self.fetch_active_gemini_models)
        api_row.addWidget(self.btn_fetch_models)
        layout.addLayout(api_row)

        model_header = QHBoxLayout()
        model_header.addWidget(QLabel("Gemini Modeli:"))
        self.lbl_model_status = QLabel("")
        self.lbl_model_status.setStyleSheet("color: #888899; font-size: 11px;")
        model_header.addWidget(self.lbl_model_status)
        model_header.addStretch()
        layout.addLayout(model_header)

        self.model_combo = QComboBox()
        self.populate_default_models()
        layout.addWidget(self.model_combo)

        layout.addSpacing(8)

        layout.addWidget(QLabel("<b>OCR Yenileme Sıklığı:</b>"))
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Ekran Tarama Aralığı (Saniye):"))
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0.2, 5.0)
        self.spin_interval.setSingleStep(0.1)
        self.spin_interval.setValue(float(self.config.get("ocr_interval", 0.5)))
        self.spin_interval.valueChanged.connect(lambda val: self.config.update({"ocr_interval": val}))
        interval_row.addWidget(self.spin_interval)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        layout.addStretch()
        self.tabs.addTab(tab, "Motorlar & AI")

        if self.api_input.text().strip():
            self.fetch_active_gemini_models()

    def populate_default_models(self):
        defaults = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        self.model_combo.clear()
        self.model_combo.addItems(defaults)
        cur = self.config.get("gemini_model", "gemini-1.5-flash")
        idx = self.model_combo.findText(cur)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.addItem(cur)
            self.model_combo.setCurrentText(cur)
        self.model_combo.currentTextChanged.connect(lambda txt: self.config.update({"gemini_model": txt}))

    def on_api_key_changed(self, txt: str):
        self.config["gemini_api_key"] = txt.strip()

    def fetch_active_gemini_models(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.lbl_model_status.setText("(Önce API anahtarını girin)")
            self.lbl_model_status.setStyleSheet("color: #ffaa00; font-size: 11px;")
            return

        self.lbl_model_status.setText("Modeller çekiliyor...")
        self.lbl_model_status.setStyleSheet("color: #00c3ff; font-size: 11px;")
        self.btn_fetch_models.setEnabled(False)

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            models = genai.list_models()

            usable_models = []
            for m in models:
                if "generateContent" in m.supported_generation_methods:
                    clean_name = m.name.replace("models/", "")
                    usable_models.append(clean_name)

            if usable_models:
                usable_models.sort()
                current_selected = self.config.get("gemini_model", "")
                
                self.model_combo.blockSignals(True)
                self.model_combo.clear()
                self.model_combo.addItems(usable_models)

                idx = self.model_combo.findText(current_selected)
                if idx >= 0:
                    self.model_combo.setCurrentIndex(idx)
                elif "gemini-1.5-flash" in usable_models:
                    self.model_combo.setCurrentText("gemini-1.5-flash")
                elif "gemini-2.0-flash" in usable_models:
                    self.model_combo.setCurrentText("gemini-2.0-flash")
                
                self.config["gemini_model"] = self.model_combo.currentText()
                self.model_combo.blockSignals(False)

                self.lbl_model_status.setText(f"✓ {len(usable_models)} aktif model bulundu")
                self.lbl_model_status.setStyleSheet("color: #00ffaa; font-size: 11px;")
            else:
                self.lbl_model_status.setText("Uygun model bulunamadı.")
                self.lbl_model_status.setStyleSheet("color: #ff5555; font-size: 11px;")

        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "400" in err_msg:
                self.lbl_model_status.setText("Geçersiz API Anahtarı!")
            else:
                self.lbl_model_status.setText("Bağlantı hatası oluştu.")
            self.lbl_model_status.setStyleSheet("color: #ff5555; font-size: 11px;")
            print(f"[Model Listeleme Hatası]: {e}")
        finally:
            self.btn_fetch_models.setEnabled(True)

    # ---------------- 3. SEKME: KISAYOL TUŞLARI ----------------
    def setup_hotkeys_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        layout.addWidget(QLabel("<b>Global Klavye Kısayolları:</b>"))
        layout.addWidget(QLabel("<i>Değiştirmek istediğiniz tuşa tıklayın ve yeni tuşa basın. (İptal için ESC)</i>"))

        h1 = QHBoxLayout()
        lbl1 = QLabel("🎯 Alan Seçme Tuşu:")
        lbl1.setFixedWidth(190)
        h1.addWidget(lbl1)
        self.btn_hk_select = HotkeyRecordButton(self.config.get("hotkey_select", "F9"))
        self.btn_hk_select.key_recorded.connect(lambda key: self.config.update({"hotkey_select": key}))
        h1.addWidget(self.btn_hk_select, stretch=1)
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        lbl2 = QLabel("▶ Takip Başlat / Durdur:")
        lbl2.setFixedWidth(190)
        h2.addWidget(lbl2)
        self.btn_hk_toggle = HotkeyRecordButton(self.config.get("hotkey_toggle", "F10"))
        self.btn_hk_toggle.key_recorded.connect(lambda key: self.config.update({"hotkey_toggle": key}))
        h2.addWidget(self.btn_hk_toggle, stretch=1)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        lbl3 = QLabel("👁 Paneli Gizle / Göster:")
        lbl3.setFixedWidth(190)
        h3.addWidget(lbl3)
        self.btn_hk_overlay = HotkeyRecordButton(self.config.get("hotkey_overlay", "F11"))
        self.btn_hk_overlay.key_recorded.connect(lambda key: self.config.update({"hotkey_overlay": key}))
        h3.addWidget(self.btn_hk_overlay, stretch=1)
        layout.addLayout(h3)

        h4 = QHBoxLayout()
        lbl4 = QLabel("✨ Kelime Kaydetme Modu:")
        lbl4.setFixedWidth(190)
        h4.addWidget(lbl4)
        self.btn_hk_save = HotkeyRecordButton(self.config.get("hotkey_save_interactive", "F7"))
        self.btn_hk_save.key_recorded.connect(lambda key: self.config.update({"hotkey_save_interactive": key}))
        h4.addWidget(self.btn_hk_save, stretch=1)
        layout.addLayout(h4)

        layout.addStretch()
        self.tabs.addTab(tab, "Kısayollar")

    # ---------------- 4. SEKME: KELİME KARTLARI ----------------
    def setup_vocab_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Kelime Çıkarım & Kart Ayarları:</b>"))

        self.chk_vocab = QCheckBox("Kelime Analiz Kartlarını Göster")
        current_show_vocab = self.config.get("show_vocabulary", self.config.get("show_vocab", True))
        self.chk_vocab.setChecked(current_show_vocab)
        self.chk_vocab.toggled.connect(self.on_vocab_toggled)
        layout.addWidget(self.chk_vocab)

        self.chk_level = QCheckBox("Kelime Seviyesini Göster ([B1], [C1])")
        self.chk_level.setChecked(self.config.get("show_vocab_level", True))
        self.chk_level.toggled.connect(lambda c: self.config.update({"show_vocab_level": c}))
        layout.addWidget(self.chk_level)

        v_row = QHBoxLayout()
        v_row.addWidget(QLabel("Maksimum Kelime Sayısı:"))
        self.spin_vocab_count = QSpinBox()
        self.spin_vocab_count.setRange(1, 6)
        self.spin_vocab_count.setValue(int(self.config.get("vocab_max_count", 4)))
        self.spin_vocab_count.valueChanged.connect(lambda val: self.config.update({"vocab_max_count": val}))
        v_row.addWidget(self.spin_vocab_count)
        v_row.addStretch()
        layout.addLayout(v_row)

        layout.addStretch()
        self.tabs.addTab(tab, "Kelimeler")

    def on_vocab_toggled(self, checked: bool):
        self.config["show_vocab"] = checked
        self.config["show_vocabulary"] = checked
        self.emit_change()

    # ---------------- YARDIMCI METOTLAR ----------------
    def toggle_bg_controls(self, enabled: bool):
        self.btn_bg_color.setEnabled(enabled)
        self.slider_bg_opacity.setEnabled(enabled)
        self.lbl_bg_opacity.setEnabled(enabled)

        if enabled:
            self.lbl_bg_opacity.setStyleSheet("color: #b0b0b8;")
            self.update_bg_preview()
        else:
            self.lbl_bg_opacity.setStyleSheet("color: #555566;")
            self.bg_preview.setStyleSheet(
                "background-color: #202028; border: 2px solid #333340; border-radius: 6px; min-height: 28px;"
            )

    def on_enable_bg_toggled(self, checked: bool):
        self.config["enable_bg"] = checked
        self.toggle_bg_controls(checked)
        self.emit_change()

    def choose_bg_color(self):
        curr_bg = self.config.get("bg_color", "18, 18, 24")
        try:
            r, g, b = [int(v.strip()) for v in curr_bg.split(",")]
            initial = QColor(r, g, b)
        except Exception:
            initial = QColor(18, 18, 24)

        color = QColorDialog.getColor(initial, self, "Arka Plan Rengi Seç")
        if color.isValid():
            self.config["bg_color"] = f"{color.red()}, {color.green()}, {color.blue()}"
            self.update_bg_preview()
            self.emit_change()

    def update_bg_preview(self):
        if not self.config.get("enable_bg", True):
            return
        bg = self.config.get("bg_color", "18, 18, 24")
        self.bg_preview.setStyleSheet(
            f"background-color: rgb({bg}); border: 2px solid #55556a; border-radius: 6px; min-height: 28px;"
        )

    def on_bg_opacity_changed(self, val):
        self.lbl_bg_opacity.setText(f"Arka Plan Saydamlığı: %{val}")
        self.config["bg_opacity"] = val / 100.0
        self.emit_change()

    def choose_text_color(self):
        curr_hex = self.config.get("text_color", "#ffffff")
        color = QColorDialog.getColor(QColor(curr_hex), self, "Yazı Rengi Seç")
        if color.isValid():
            self.config["text_color"] = color.name()
            self.update_txt_preview()
            self.emit_change()

    def update_txt_preview(self):
        c = self.config.get("text_color", "#ffffff")
        self.txt_preview.setStyleSheet(
            f"background-color: {c}; border: 2px solid #55556a; border-radius: 6px; min-height: 28px;"
        )

    def on_text_opacity_changed(self, val):
        self.lbl_text_opacity.setText(f"Metin Saydamlığı: %{val}")
        self.config["text_opacity"] = val / 100.0
        self.emit_change()

    def on_font_size_changed(self, val):
        self.config["font_size"] = val
        self.emit_change()

    def on_orig_toggled(self, checked):
        self.config["show_original_text"] = checked
        self.emit_change()

    def emit_change(self):
        self.settings_changed.emit(self.config)

    def save_and_close(self):
        self.config["anchor_corner"] = self.combo_anchor.currentData()
        self.config["close_behavior"] = self.combo_close.currentData()
        self.config["bg_opacity"] = self.slider_bg_opacity.value() / 100.0
        self.config["text_opacity"] = self.slider_text_opacity.value() / 100.0
        self.config["font_size"] = self.spin_font_size.value()
        ConfigManager.save_config(self.config)
        self.settings_changed.emit(self.config)
        self.accept()