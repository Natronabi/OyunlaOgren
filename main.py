import sys
import os

if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

import keyboard
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame, QSystemTrayIcon, QMenu, QStyle,
    QDialog, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QGuiApplication, QAction

from ui.selector import ScreenSelector
from ui.overlay import TranslationOverlay
from ui.settings_dialog import SettingsDialog
from ui.area_box import AreaPreviewFrame
from ui.practice_window import PracticeWindow
from ui.saved_words_dialog import SavedWordsDialog
from core.auto_watcher import AutoWatcherWorker
from core.config_manager import ConfigManager


class CloseConfirmDialog(QDialog):
    """Kapatma tuşuna basıldığında tercihi soran ve hatırlayan diyalog penceresi."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GameLingo'dan Çıkış")
        self.setFixedSize(380, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #16161e;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 12px;
                spacing: 8px;
            }
            QPushButton {
                font-weight: 600;
                border-radius: 6px;
                padding: 9px 14px;
                font-size: 12px;
            }
        """)

        self.choice = None  # "tray" veya "exit"

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)

        lbl = QLabel("Uygulamayı tamamen kapatmak mı istiyorsunuz, yoksa sistem tepsisinde (arka planda) çalışmaya devam mı etsin?")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        # Hatırla Kutucuğu
        self.chk_remember = QCheckBox("Bu tercihimi hatırla (Bir daha sorma)")
        self.chk_remember.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.chk_remember)

        # Bilgilendirme Notu
        lbl_hint = QLabel("ℹ Bu tercihi daha sonra ⚙ Ayarlar menüsünden dilediğiniz zaman değiştirebilirsiniz.")
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #77778a; font-size: 11px; font-style: italic;")
        lay.addWidget(lbl_hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_tray = QPushButton("📥 Tepsiye Küçült")
        self.btn_tray.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tray.setStyleSheet("""
            QPushButton {
                background-color: #222232;
                color: #00c3ff;
                border: 1px solid #333348;
            }
            QPushButton:hover { background-color: #2b2b40; border-color: #00c3ff; }
        """)
        self.btn_tray.clicked.connect(self.select_tray)
        btn_row.addWidget(self.btn_tray)

        self.btn_exit = QPushButton("❌ Tamamen Kapat")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: #38181c;
                color: #ff5566;
                border: 1px solid #58242a;
            }
            QPushButton:hover { background-color: #4a2026; border-color: #ff5566; }
        """)
        self.btn_exit.clicked.connect(self.select_exit)
        btn_row.addWidget(self.btn_exit)

        lay.addLayout(btn_row)

    def select_tray(self):
        self.choice = "tray"
        self.accept()

    def select_exit(self):
        self.choice = "exit"
        self.accept()


class HotkeyBridge(QObject):
    trigger_select = pyqtSignal()
    trigger_toggle = pyqtSignal()
    trigger_overlay = pyqtSignal()
    trigger_save = pyqtSignal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameLingo Translator")
        self.setFixedSize(360, 520)

        self.config = ConfigManager.load_config()
        self.roi_coords = None
        self.watcher = None
        self.practice_dialog = None
        self.saved_words_dialog = None

        self.selector = ScreenSelector()
        self.overlay = TranslationOverlay(config=self.config)
        self.area_box = AreaPreviewFrame()

        self.selector.area_selected.connect(self.on_area_selected)

        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.trigger_select.connect(self.start_selection)
        self.hotkey_bridge.trigger_toggle.connect(self.toggle_watcher)
        self.hotkey_bridge.trigger_overlay.connect(self.toggle_overlay_visibility)

        self.init_ui()
        self.init_tray_icon()
        self.position_on_screen_edge()
        self.register_hotkeys()

    def position_on_screen_edge(self):
        screen = QGuiApplication.primaryScreen().geometry()
        margin_right = 40
        margin_top = 80
        pos_x = screen.width() - self.width() - margin_right
        pos_y = margin_top
        self.move(pos_x, pos_y)

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(app_icon)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("GameLingo Translator")

        tray_menu = QMenu()

        act_show = QAction("👁 Pencereyi Göster", self)
        act_show.triggered.connect(self.show_and_activate)
        tray_menu.addAction(act_show)

        act_saved = QAction("📚 Kaydedilenler Sözlüğü", self)
        act_saved.triggered.connect(self.open_saved_words_window)
        tray_menu.addAction(act_saved)

        act_practice = QAction("🧠 Kelime Pratiği Yap", self)
        act_practice.triggered.connect(self.open_practice_window)
        tray_menu.addAction(act_practice)

        tray_menu.addSeparator()

        act_toggle = QAction("▶ Canlı Takibi Başlat/Durdur", self)
        act_toggle.triggered.connect(self.toggle_watcher)
        tray_menu.addAction(act_toggle)

        tray_menu.addSeparator()

        act_quit = QAction("❌ Tamamen Çık", self)
        act_quit.triggered.connect(self.force_quit)
        tray_menu.addAction(act_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_activate()

    def show_and_activate(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()
        # Canlı izleme çalışmıyorsa ve koordinat varsa mavi seçim alanını geri getir
        if self.roi_coords and (self.watcher is None or not self.watcher.isRunning()):
            px, py, pw, ph = self.roi_coords
            screen = self.screen() or QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            ui_x = int(round(px / dpr))
            ui_y = int(round(py / dpr))
            ui_w = int(round(pw / dpr))
            ui_h = int(round(ph / dpr))
            self.area_box.show_box(ui_x, ui_y, ui_w, ui_h)

    def hide_to_tray(self):
        """Uygulama arka plana geçtiğinde ana ekranı ve mavi kılavuz kutusunu gizler/kapatır."""
        self.hide()
        if hasattr(self, "area_box") and self.area_box:
            self.area_box.hide()
            self.area_box.close()
        self.tray_icon.showMessage(
            "GameLingo Arka Planda",
            "Uygulama sistem tepsisinde çalışmaya devam ediyor.",
            QSystemTrayIcon.MessageIcon.Information,
            1200
        )

    def changeEvent(self, event):
        """Pencere minimize edildiğinde (simge durumuna küçültüldüğünde) mavi çerçeveyi gizler."""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                if hasattr(self, "area_box") and self.area_box:
                    self.area_box.hide()
                    self.area_box.close()
        super().changeEvent(event)

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
        main_layout.setSpacing(10)

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

        # Kelime Pratiği Yap Butonu
        self.btn_practice = QPushButton("🧠  Kelime Pratiği Yap", self)
        self.btn_practice.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_practice.setStyleSheet("""
            QPushButton {
                background-color: #1a2f23;
                color: #58cc02;
                border: 1px solid #285438;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #244231;
                border-color: #58cc02;
                color: #6fe019;
            }
            QPushButton:pressed {
                background-color: #15241b;
            }
        """)
        self.btn_practice.clicked.connect(self.open_practice_window)
        main_layout.addWidget(self.btn_practice)

        # Kaydedilenler Sözlüğü Butonu
        self.btn_saved_words = QPushButton("📚  Kaydedilenler Sözlüğü", self)
        self.btn_saved_words.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_saved_words.setStyleSheet("""
            QPushButton {
                background-color: #162232;
                color: #00c3ff;
                border: 1px solid #243852;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1f3048;
                border-color: #00e5ff;
                color: #33ffff;
            }
            QPushButton:pressed {
                background-color: #121c2a;
            }
        """)
        self.btn_saved_words.clicked.connect(self.open_saved_words_window)
        main_layout.addWidget(self.btn_saved_words)

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

        self.minimize_tray_btn = QPushButton("📥 Tepsiye Gizle", self)
        self.minimize_tray_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_tray_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #888899; border: 1px solid #2a2a35; } "
            "QPushButton:hover { background-color: #1a1a22; color: #00c3ff; }"
        )
        self.minimize_tray_btn.clicked.connect(self.hide_to_tray)
        bottom_row.addWidget(self.minimize_tray_btn)

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
        if hasattr(self, "area_box") and self.area_box:
            self.area_box.hide()
            self.area_box.close()
        self.status_lbl.setText("Durum: Oyun alanı seçiliyor...")
        self.selector.start_selection()

    def on_area_selected(self, coords):
        self.roi_coords = coords
        px, py, pw, ph = coords

        screen = self.screen() or QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        ui_x = int(round(px / dpr))
        ui_y = int(round(py / dpr))
        ui_w = int(round(pw / dpr))
        ui_h = int(round(ph / dpr))

        self.area_lbl.setText(f"Seçili Alan: X={px}, Y={py}, {pw}x{ph} px")
        self.status_lbl.setText("Durum: Alan belirlendi. Paneli ayarlayıp takibi başlatabilirsiniz.")
        self.toggle_btn.setEnabled(True)

        self.area_box.show_box(ui_x, ui_y, ui_w, ui_h)

        if ui_y > 180:
            target_y = ui_y - self.overlay.height() - 15
        else:
            target_y = ui_y + ui_h + 15

        self.overlay.move(max(10, ui_x), max(10, target_y))
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
            
            px, py, pw, ph = self.roi_coords
            screen = self.screen() or QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            ui_x = int(round(px / dpr))
            ui_y = int(round(py / dpr))
            ui_w = int(round(pw / dpr))
            ui_h = int(round(ph / dpr))
            self.area_box.show_box(ui_x, ui_y, ui_w, ui_h)
        else:
            if hasattr(self, "area_box") and self.area_box:
                self.area_box.hide()
                self.area_box.close()

            self.overlay.reset_to_waiting()
            self.overlay.show()

            current_engine = self.engine_combo.currentData()
            self.watcher = AutoWatcherWorker(
                roi_coords=self.roi_coords,
                interval=self.config.get("ocr_interval", 0.5),
                engine=current_engine
            )
            self.watcher.translation_ready.connect(self.overlay.update_content)
            self.watcher.status_updated.connect(lambda msg: self.status_lbl.setText(f"Durum: {msg}"))
            self.watcher.start()

            self.toggle_btn.setText(f"⏸ Takibi Durdur ({hk_tog})")
            self.toggle_btn.setStyleSheet("background-color: #ff4757; color: #ffffff;")
            self.status_lbl.setText("Durum: Canlı izleme aktif...")

    def open_practice_window(self):
        if self.practice_dialog is None:
            self.practice_dialog = PracticeWindow(self)
        self.practice_dialog.start_session()
        self.practice_dialog.exec()

    def open_saved_words_window(self):
        if self.saved_words_dialog is None:
            self.saved_words_dialog = SavedWordsDialog(self)
        else:
            self.saved_words_dialog.load_data()
        self.saved_words_dialog.exec()

    def on_engine_changed(self):
        new_engine = self.engine_combo.currentData()
        self.config["default_engine"] = new_engine
        ConfigManager.save_config(self.config)
        
        badge_text = "✦ GEMINI AI" if new_engine == "gemini" else "⚡ YEREL ÇEVİRİ"
        badge_color = "#00c3ff" if new_engine == "gemini" else "#00ffaa"
        self.overlay.engine_badge.setText(badge_text)
        self.overlay.engine_badge.setStyleSheet(f"color: {badge_color}; font-size: 10px; font-weight: bold;")

        if self.watcher and self.watcher.isRunning():
            self.watcher.stop()
            self.watcher = None
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
            self.register_hotkeys()

    def closeEvent(self, event):
        """Kullanıcının tercihine göre kapatır, tepsiye küçültür veya sorar."""
        close_pref = self.config.get("close_behavior", "ask")

        if close_pref == "tray":
            event.ignore()
            self.hide_to_tray()
            return
        elif close_pref == "exit":
            self.force_quit()
            event.accept()
            return

        dlg = CloseConfirmDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.chk_remember.isChecked() and dlg.choice:
                self.config["close_behavior"] = dlg.choice
                ConfigManager.save_config(self.config)

            if dlg.choice == "tray":
                event.ignore()
                self.hide_to_tray()
            else:
                self.force_quit()
                event.accept()
        else:
            event.ignore()

    def force_quit(self):
        if self.watcher and self.watcher.isRunning():
            self.watcher.stop()
        if hasattr(self, "area_box") and self.area_box:
            self.area_box.hide()
            self.area_box.close()
        self.overlay.close()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())