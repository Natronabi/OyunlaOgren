import sys
import keyboard
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QGuiApplication

from ui.selector import ScreenSelector
from ui.overlay import TranslationOverlay
from ui.settings_dialog import SettingsDialog
from ui.area_box import AreaPreviewFrame
from core.auto_watcher import AutoWatcherWorker
from core.config_manager import ConfigManager

class HotkeyBridge(QObject):
    trigger_select = pyqtSignal()
    trigger_toggle = pyqtSignal()
    trigger_overlay = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameLingo Translator")
        self.setFixedSize(360, 420)

        self.config = ConfigManager.load_config()
        self.roi_coords = None
        self.watcher = None

        self.selector = ScreenSelector()
        self.overlay = TranslationOverlay(config=self.config)
        self.area_box = AreaPreviewFrame()

        self.selector.area_selected.connect(self.on_area_selected)

        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.trigger_select.connect(self.start_selection)
        self.hotkey_bridge.trigger_toggle.connect(self.toggle_watcher)
        self.hotkey_bridge.trigger_overlay.connect(self.toggle_overlay_visibility)

        self.init_ui()
        self.position_on_screen_edge()
        self.register_hotkeys()

    def position_on_screen_edge(self):
        screen = QGuiApplication.primaryScreen().geometry()
        margin_right = 40
        margin_top = 80
        pos_x = screen.width() - self.width() - margin_right
        pos_y = margin_top
        self.move(pos_x, pos_y)

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121216;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #b0b0b8;
                font-size: 12px;
            }
            QComboBox {
                background-color: #1e1e24;
                color: #ffffff;
                border: 1px solid #33333e;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton {
                font-weight: 600;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        title_lbl = QLabel("GameLingo")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title_lbl)

        version_badge = QLabel("v1.0")
        version_badge.setStyleSheet("color: #00c3ff; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(version_badge)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        status_card = QFrame(self)
        status_card.setStyleSheet("background-color: #181820; border: 1px solid #2a2a35; border-radius: 8px;")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.setSpacing(4)

        self.status_lbl = QLabel("Durum: Hazır (Alan seçimi bekleniyor)")
        self.status_lbl.setStyleSheet("color: #00ffaa; font-weight: 500;")
        status_layout.addWidget(self.status_lbl)

        self.area_lbl = QLabel("Seçili Alan: Yok")
        self.area_lbl.setStyleSheet("color: #888899; font-size: 11px;")
        status_layout.addWidget(self.area_lbl)
        main_layout.addWidget(status_card)

        engine_box = QVBoxLayout()
        engine_box.setSpacing(4)
        lbl_engine = QLabel("Çeviri Motoru:")
        lbl_engine.setStyleSheet("color: #e0e0e0; font-weight: 500;")
        self.engine_combo = QComboBox(self)
        self.engine_combo.addItem("⚡ Yerel Motor (Argostranslate - Çevrimdışı/0ms)", "local")
        self.engine_combo.addItem("✦ Gemini AI (Yapay Zeka + Sözlük/Analiz)", "gemini")
        
        default_eng = self.config.get("default_engine", "local")
        idx = 0 if default_eng == "local" else 1
        self.engine_combo.setCurrentIndex(idx)
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)

        engine_box.addWidget(lbl_engine)
        engine_box.addWidget(self.engine_combo)
        main_layout.addLayout(engine_box)

        # Alan Seç Butonu (Kısayol etiketli)
        self.select_btn = QPushButton(self)
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #252532;
                color: #ffffff;
                border: 1px solid #3e3e50;
            }
            QPushButton:hover {
                background-color: #353545;
                border-color: #00c3ff;
            }
        """)
        self.select_btn.clicked.connect(self.start_selection)
        main_layout.addWidget(self.select_btn)

        # Canlı Takip Başlat / Durdur
        self.toggle_btn = QPushButton(self)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c3ff;
                color: #000000;
                border: none;
            }
            QPushButton:hover { background-color: #33d0ff; }
            QPushButton:disabled { background-color: #222228; color: #555560; }
        """)
        self.toggle_btn.clicked.connect(self.toggle_watcher)
        main_layout.addWidget(self.toggle_btn)

        # Ayarlar
        bottom_row = QHBoxLayout()
        self.settings_btn = QPushButton("⚙ Ayarlar", self)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a0b0;
                border: 1px solid #2a2a35;
            }
            QPushButton:hover { background-color: #1a1a22; color: #ffffff; }
        """)
        self.settings_btn.clicked.connect(self.open_settings)
        bottom_row.addWidget(self.settings_btn)

        main_layout.addLayout(bottom_row)
        main_layout.addStretch()

        self.hotkey_info = QLabel(self)
        self.hotkey_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hotkey_info.setStyleSheet("color: #666677; font-size: 10px;")
        main_layout.addWidget(self.hotkey_info)

        self.update_button_texts()

    def update_button_texts(self):
        hk_sel = self.config.get("hotkey_select", "F9")
        hk_tog = self.config.get("hotkey_toggle", "F10")
        hk_ov = self.config.get("hotkey_overlay", "F11")

        self.select_btn.setText(f"🎯 Oyun Alanını Seç ({hk_sel})")
        
        if self.watcher and self.watcher.isRunning():
            self.toggle_btn.setText(f"⏸ Takibi Durdur ({hk_tog})")
        else:
            self.toggle_btn.setText(f"▶ Canlı Takibi Başlat ({hk_tog})")

        self.hotkey_info.setText(f"Kısayollar: {hk_sel} (Seç) | {hk_tog} (Takip) | {hk_ov} (Gizle/Göster)")

    def register_hotkeys(self):
        """Eski kısayolları temizleyip config'teki yeni tuşları bağlar."""
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        hk_sel = self.config.get("hotkey_select", "F9")
        hk_tog = self.config.get("hotkey_toggle", "F10")
        hk_ov = self.config.get("hotkey_overlay", "F11")

        try:
            keyboard.add_hotkey(hk_sel, lambda: self.hotkey_bridge.trigger_select.emit())
            keyboard.add_hotkey(hk_tog, lambda: self.hotkey_bridge.trigger_toggle.emit())
            keyboard.add_hotkey(hk_ov, lambda: self.hotkey_bridge.trigger_overlay.emit())
        except Exception as e:
            print(f"[Hotkey Hatası] Kısayollar atanamadı ({hk_sel}, {hk_tog}, {hk_ov}): {e}")

        self.update_button_texts()

    def start_selection(self):
        self.area_box.hide()
        self.status_lbl.setText("Durum: Oyun alanı seçiliyor...")
        self.selector.start_selection()

    def on_area_selected(self, coords):
        self.roi_coords = coords
        x, y, w, h = coords
        self.area_lbl.setText(f"Seçili Alan: X={x}, Y={y}, {w}x{h} px")
        self.status_lbl.setText("Durum: Alan belirlendi. Takip başlatabilirsiniz.")
        self.toggle_btn.setEnabled(True)

        self.area_box.show_box(x, y, w, h)
        self.overlay.move(x, max(30, y - self.overlay.height() - 10))
        self.overlay.show()
        self.activateWindow()
        self.raise_()

    def toggle_watcher(self):
        if not self.roi_coords:
            return

        hk_tog = self.config.get("hotkey_toggle", "F10")

        if self.watcher and self.watcher.isRunning():
            self.watcher.stop()
            self.watcher = None
            self.toggle_btn.setText(f"▶ Canlı Takibi Başlat ({hk_tog})")
            self.toggle_btn.setStyleSheet("background-color: #00c3ff; color: #000000;")
            self.status_lbl.setText("Durum: Takip duraklatıldı.")
            self.area_box.show()
        else:
            self.area_box.hide()
            
            current_engine = self.engine_combo.currentData()
            self.watcher = AutoWatcherWorker(
                roi_coords=self.roi_coords,
                interval=self.config.get("ocr_interval", 0.5),
                engine=current_engine
            )
            self.watcher.translation_ready.connect(self.overlay.update_content)
            self.watcher.status_updated.connect(lambda msg: self.status_lbl.setText(f"Durum: {msg}"))
            self.watcher.start()

            self.overlay.show()
            self.toggle_btn.setText(f"⏸ Takibi Durdur ({hk_tog})")
            self.toggle_btn.setStyleSheet("background-color: #ff4757; color: #ffffff;")
            self.status_lbl.setText("Durum: Canlı izleme aktif...")

    def on_engine_changed(self):
        new_engine = self.engine_combo.currentData()
        self.config["default_engine"] = new_engine
        ConfigManager.save_config(self.config)
        
        if self.watcher and self.watcher.isRunning():
            self.toggle_watcher()
            self.toggle_watcher()

    def toggle_overlay_visibility(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def open_settings(self):
        dialog = SettingsDialog(current_config=self.config, parent=self)
        dialog.settings_changed.connect(self.overlay.update_settings)
        if dialog.exec():
            self.config = ConfigManager.load_config()
            self.overlay.update_settings(self.config)
            # Yeni kısayolları ana sisteme tekrar bağla
            self.register_hotkeys()

    def closeEvent(self, event):
        if self.watcher and self.watcher.isRunning():
            self.watcher.stop()
        self.area_box.close()
        self.overlay.close()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())