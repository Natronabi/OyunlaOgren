from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QWidget, QLineEdit, 
    QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from core.vocabulary_db import VocabularyDB


class SavedWordsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Kaydedilen Kelimeler ve Cümleler")
        self.setFixedSize(580, 620)
        self.setStyleSheet("""
            QDialog {
                background-color: #14141c;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #1e1e28;
                color: #ffffff;
                border: 1px solid #333346;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #00c3ff; }
            QTabWidget::pane {
                border: 1px solid #282838;
                background-color: #171722;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #1c1c28;
                color: #9999aa;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #252536;
                color: #00c3ff;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 13px;
            }
            QListWidget::item {
                background-color: #1e1e2c;
                margin-bottom: 6px;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2c2c3e;
            }
            QListWidget::item:hover {
                background-color: #262638;
                border-color: #00c3ff;
            }
            QListWidget::item:selected {
                background-color: #2b2b42;
                border: 1px solid #00c3ff;
                color: #ffffff;
            }
        """)

        self.db = VocabularyDB()
        self.all_items = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Üst Arama Çubuğu
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("🔍 Kelime veya çeviri ara...")
        self.search_box.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_box)

        # Sekmeler
        self.tabs = QTabWidget(self)

        # 1. Kelimeler Sekmesi
        self.words_tab = QWidget()
        w_layout = QVBoxLayout(self.words_tab)
        w_layout.setContentsMargins(8, 8, 8, 8)
        self.words_list = QListWidget()
        self.words_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        w_layout.addWidget(self.words_list)
        self.tabs.addTab(self.words_tab, "Kelimeler")

        # 2. Cümleler Sekmesi
        self.sentences_tab = QWidget()
        s_layout = QVBoxLayout(self.sentences_tab)
        s_layout.setContentsMargins(8, 8, 8, 8)
        self.sentences_list = QListWidget()
        self.sentences_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        s_layout.addWidget(self.sentences_list)
        self.tabs.addTab(self.sentences_tab, "Kaydedilen Yazılar / Cümleler")

        layout.addWidget(self.tabs)

        # Alt Butonlar
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.btn_select_all = QPushButton("☑ Tümünü Seç")
        self.btn_select_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: #20202e;
                color: #00c3ff;
                border: 1px solid #333348;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #28283c; border-color: #00c3ff; }
        """)
        self.btn_select_all.clicked.connect(self.toggle_select_all)
        bottom_row.addWidget(self.btn_select_all)

        self.del_btn = QPushButton("🗑 Seçilenleri Sil")
        self.del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton {
                background-color: #38181c;
                color: #ff5566;
                border: 1px solid #58242a;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4a2026; border-color: #ff5566; }
        """)
        self.del_btn.clicked.connect(self.delete_selected)
        bottom_row.addWidget(self.del_btn)

        bottom_row.addStretch()

        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #242434;
                color: #cccccc;
                border: 1px solid #3d3d52;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #303046; color: #ffffff; }
        """)
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)

        layout.addLayout(bottom_row)

    def _get_active_list(self) -> QListWidget:
        return self.words_list if self.tabs.currentIndex() == 0 else self.sentences_list

    def toggle_select_all(self):
        active_list = self._get_active_list()
        if not active_list.count():
            return

        # Zaten hepsi seçiliyse seçimi kaldır, değilse tümünü seç
        if len(active_list.selectedItems()) == active_list.count():
            active_list.clearSelection()
        else:
            active_list.selectAll()

    def load_data(self):
        self.all_items = self.db.get_all_words()
        self.filter_items()

    def filter_items(self):
        search_txt = self.search_box.text().strip().lower()

        self.words_list.clear()
        self.sentences_list.clear()

        for item in self.all_items:
            w = item.get("word", "")
            m = item.get("meaning", "")
            lvl = item.get("level", "B1")
            streak = item.get("streak", 0)

            if search_txt and (search_txt not in w.lower() and search_txt not in m.lower()):
                continue

            list_item = QListWidgetItem()
            list_item.setData(Qt.ItemDataRole.UserRole, item.get("id"))

            if lvl == "Cümle":
                list_item.setText(f"📄 {w}\n➜ {m}")
                self.sentences_list.addItem(list_item)
            else:
                list_item.setText(f"✦ {w}  [{lvl}]  (Tekrar: {streak})\n➜ {m}")
                self.words_list.addItem(list_item)

    def delete_selected(self):
        active_list = self._get_active_list()
        selected_items = active_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Bilgi", "Lütfen silmek için en az bir öğe seçin.")
            return

        count = len(selected_items)
        confirm = QMessageBox.question(
            self,
            "Silme Onayı",
            f"Seçili {count} adet kaydı sözlükten kalıcı olarak silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        ids_to_delete = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ids_to_delete)
            cursor.execute(f"DELETE FROM words WHERE id IN ({placeholders})", ids_to_delete)
            conn.commit()
            conn.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme işlemi sırasında hata oluştu: {e}")