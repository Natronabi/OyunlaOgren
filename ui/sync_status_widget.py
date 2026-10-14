import socket
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt

class SyncStatusWidget(QWidget):
    def __init__(self, db, cloud_sync, parent=None):
        super().__init__(parent)
        self.db = db
        self.cloud_sync = cloud_sync

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)

        self.lbl_status = QLabel("Bulut kontrol ediliyor...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.layout.addWidget(self.lbl_status)

        # 5 saniyede bir durumu kontrol et
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_status)
        self.timer.start(5000)
        self.check_status()

    def has_internet(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    def check_status(self):
        unsynced_count = self.db.get_unsynced_count()
        online = self.has_internet() and self.cloud_sync.is_configured()

        if online:
            if unsynced_count > 0:
                self.lbl_status.setText(f"🟡 {unsynced_count} kelime eşitleniyor...")
                self.lbl_status.setStyleSheet("color: #F1C40F; font-size: 11px; font-weight: bold;")
                self.cloud_sync.flush_unsynced(self.db)
            else:
                self.lbl_status.setText("🟢 Senkronize edildi")
                self.lbl_status.setStyleSheet("color: #2ECC71; font-size: 11px;")
        else:
            if unsynced_count > 0:
                self.lbl_status.setText(f"🔴 {unsynced_count} kayıt eşitlenmedi (İnterneti kontrol edin)")
                self.lbl_status.setStyleSheet("color: #E74C3C; font-size: 11px; font-weight: bold;")
            else:
                self.lbl_status.setText("⚪ Çevrimdışı")
                self.lbl_status.setStyleSheet("color: #7F8C8D; font-size: 11px;")