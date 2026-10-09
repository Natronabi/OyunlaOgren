from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QClipboard
from core.ai_translator import GeminiTranslator

class BenchmarkRunnerThread(QThread):
    single_result_ready = pyqtSignal(dict)
    all_finished = pyqtSignal()

    def __init__(self, translator: GeminiTranslator, text: str, models: list):
        super().__init__()
        self.translator = translator
        self.text = text
        self.models = models

    def run(self):
        # Modelleri eşzamanlı çalıştırırken sonuç geldikçe tek tek arayüze bas
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(self.models), 12)) as executor:
            futures = [executor.submit(self.translator.translate_single, self.text, m) for m in self.models]
            for f in futures:
                res = f.result()
                self.single_result_ready.emit(res)
        self.all_finished.emit()


class FullscreenBenchmarkWindow(QMainWindow):
    def __init__(self, translator: GeminiTranslator, initial_text: str, selected_models: list, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.test_text = initial_text
        self.selected_models = selected_models
        self.results_map = {}

        # === TAM BURAYA EKLİYORSUN (8 boşluk girintili) ===
        self.cooldown_remaining = 0
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self._tick_cooldown)
        # ==================================================

        self.setWindowTitle("GameLingo - AI Model Benchmark & Çeviri Laboratuvarı")
        self.setStyleSheet(""" ... """)

        self.init_ui()
        self.start_benchmark_process()
        

        self.init_ui()
        self.start_benchmark_process()

    def init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # ÜST BAR: Bilgi, Test Cümlesi ve Yeniden Çalıştır
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        lbl_title = QLabel("⚔️ Model Laboratuvarı")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00c3ff;")
        top_bar.addWidget(lbl_title)

        self.input_text = QLineEdit(self)
        self.input_text.setText(self.test_text)
        self.input_text.setPlaceholderText("Karşılaştırılacak İngilizce oyun metnini buraya yazın...")
        top_bar.addWidget(self.input_text, stretch=1)

        self.btn_retest = QPushButton("⚡ Yeniden Test Et")
        self.btn_retest.setFixedHeight(36)
        self.btn_retest.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retest.setStyleSheet("""
            QPushButton {
                background-color: #00ffaa;
                color: #05140b;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 0 16px;
            }
            QPushButton:hover { background-color: #33ffbb; }
        """)
        self.btn_retest.clicked.connect(self.start_benchmark_process)
        top_bar.addWidget(self.btn_retest)

        self.btn_close = QPushButton("Pencereyi Kapat")
        self.btn_close.setFixedHeight(36)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #242432;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 0 16px;
                border: 1px solid #3a3a4e;
            }
            QPushButton:hover { background-color: #323246; }
        """)
        self.btn_close.clicked.connect(self.close)
        top_bar.addWidget(self.btn_close)

        main_layout.addLayout(top_bar)

        # KONTROL BİLGİ ŞERİDİ
        self.status_bar_lbl = QLabel(f"Seçili Modeller: {len(self.selected_models)} | İstekler gönderiliyor...")
        self.status_bar_lbl.setStyleSheet("color: #7d7d92; font-size: 11px;")
        main_layout.addWidget(self.status_bar_lbl)

        # YATAY KAYDIRILABİLİR ALAN (HORIZONTAL SCROLL)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.columns_container = QWidget()
        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(0, 10, 0, 10)
        self.columns_layout.setSpacing(16)
        self.columns_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.columns_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

    def start_benchmark_process(self):
        text = self.input_text.text().strip()
        if not text:
            QMessageBox.warning(self, "Uyarı", "Lütfen test edilecek bir metin girin.")
            return

        self.btn_retest.setEnabled(False)
        self.btn_retest.setText("⏳ Modeller Yanıt Veriyor...")
        self.status_bar_lbl.setText(f"Test yürütülüyor ({len(self.selected_models)} model devrede)...")

        # Önceki kartları temizle
        while self.columns_layout.count():
            item = self.columns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Boş yükleme kartlarını hemen yerleştir (placeholder)
        self.cards = {}
        for m in self.selected_models:
            card = self.create_placeholder_card(m)
            self.columns_layout.addWidget(card)
            self.cards[m] = card

        # İş parçacığını başlat
        self.worker = BenchmarkRunnerThread(self.translator, text, self.selected_models)
        self.worker.single_result_ready.connect(self.update_card_with_result)
        self.worker.all_finished.connect(self.on_all_finished)
        self.worker.start()

    def create_placeholder_card(self, model_name: str) -> QFrame:
        card = QFrame()
        card.setFixedWidth(340)
        card.setStyleSheet("""
            QFrame {
                background-color: #151520;
                border: 1px solid #282838;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        lay = QVBoxLayout(card)
        lay.setSpacing(10)

        # Üst Model Başlığı
        title = QLabel(model_name)
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #00c3ff;")
        lay.addWidget(title)

        status = QLabel("⏳ Yanıt bekleniyor...")
        status.setObjectName("status_lbl")
        status.setStyleSheet("color: #ffd700; font-size: 11px;")
        lay.addWidget(status)

        lay.addStretch()
        return card

    def update_card_with_result(self, res: dict):
        model_name = res["model"]
        card = self.cards.get(model_name)
        if not card:
            return

        # Kart içeriğini gerçek verilerle doldur
        lay = card.layout()
        while lay.count() > 1:
            item = lay.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        elapsed = res["elapsed"]
        speed_color = "#00ffaa" if elapsed < 0.7 else ("#ffd700" if elapsed < 1.5 else "#ff4757")

        # Hız Rozeti
        speed_lbl = QLabel(f"⏱ Tepki Süresi: {elapsed} saniye")
        speed_lbl.setStyleSheet(f"color: {speed_color}; font-weight: bold; font-size: 12px;")
        lay.addWidget(speed_lbl)

        # Çeviri Başlığı ve Metni
        lay.addWidget(QLabel("<b>Türkçe Çeviri:</b>"))
        trans_box = QLabel(res.get("translated_text", ""))
        trans_box.setWordWrap(True)
        trans_box.setStyleSheet("""
            QLabel {
                background-color: #1e1e2c;
                border: 1px solid #323244;
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
                font-size: 13px;
            }
        """)
        lay.addWidget(trans_box)

        # Kelime Tahlilleri (Varsa)
        vocabs = res.get("vocabulary", [])
        if vocabs:
            lay.addWidget(QLabel("<b>Çıkarılan Seviyeli Kelimeler:</b>"))
            v_container = QVBoxLayout()
            v_container.setSpacing(4)
            for v in vocabs:
                word_html = f"<span style='color:#00e5ff; font-weight:bold;'>{v.get('word','')}</span> " \
                            f"<span style='color:#ffd700; font-size:10px;'>[{v.get('level','B1')}]</span>: " \
                            f"<span style='color:#c0c0d0;'>{v.get('meaning','')}</span>"
                lbl_v = QLabel(word_html)
                lbl_v.setWordWrap(True)
                v_container.addWidget(lbl_v)
            lay.addLayout(v_container)

        lay.addStretch()

        # Çeviriyi Panoya Kopyala Butonu
        btn_copy = QPushButton("📋 Metni Kopyala")
        btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #242436;
                color: #a0a0b8;
                border: 1px solid #36364c;
                border-radius: 5px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #313148;
                color: #ffffff;
            }
        """)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(res.get("translated_text", "")))
        lay.addWidget(btn_copy)

    def on_all_finished(self):
        self.status_bar_lbl.setText("Tüm modellerin analizi tamamlandı. Kartları sağa kaydırarak inceleyebilirsiniz.")
        # 12 saniyelik kota soğuma sayacını başlat
        self.cooldown_remaining = 12
        self.btn_retest.setEnabled(False)
        self.btn_retest.setText(f"⏳ Kota Koruması ({self.cooldown_remaining}s)")
        self.cooldown_timer.start(1000)

    def _tick_cooldown(self):
        self.cooldown_remaining -= 1
        if self.cooldown_remaining <= 0:
            self.cooldown_timer.stop()
            self.btn_retest.setEnabled(True)
            self.btn_retest.setText("⚡ Yeniden Test Et")
        else:
            self.btn_retest.setText(f"⏳ Kota Koruması ({self.cooldown_remaining}s)")