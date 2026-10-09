from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QScrollArea,
    QFrame, QMessageBox, QDialog, QTextBrowser
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

from core.ai_translator import GeminiTranslator, MODEL_DESCRIPTIONS
from ui.fullscreen_benchmark_window import FullscreenBenchmarkWindow


def create_eye_icon(closed: bool = False, color: str = "#8e8e9f") -> QIcon:
    """Saf 2D minimalist göz / kapalı göz vektörel çizimi."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = painter.pen()
    pen.setColor(QColor(color))
    pen.setWidth(2)
    painter.setPen(pen)

    painter.drawArc(4, 9, 24, 14, 30 * 16, 120 * 16)
    painter.drawArc(4, 9, 24, 14, 210 * 16, 120 * 16)

    if not closed:
        painter.setBrush(QColor(color))
        painter.drawEllipse(13, 13, 6, 6)
    else:
        painter.drawLine(6, 6, 26, 26)

    painter.end()
    return QIcon(pixmap)


class QuotaGuideDialog(QDialog):
    """Kullanıcıyı API limitleri ve kota tasarrufu konusunda bilgilendiren kart."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI API Limitleri & Kota Tasarrufu Rehberi")
        self.setFixedSize(480, 360)
        self.setStyleSheet("""
            QDialog { background-color: #121218; }
            QLabel { color: #ffffff; }
            QTextBrowser {
                background-color: #181824;
                border: 1px solid #2e2e42;
                border-radius: 6px;
                color: #d0d0dc;
                font-size: 12px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("🛡️ Ücretsiz API Katmanları ve Limit Rehberi")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00c3ff;")
        layout.addWidget(title)

        browser = QTextBrowser()
        browser.setHtml("""
        <h4 style="color:#00ffaa; margin-bottom:4px;">1. Google Gemini API (Ücretsiz Plan):</h4>
        <ul>
            <li><b>Gemini 1.5 / 2.5 Flash:</b> Dakikada <b>15 istek (RPM)</b>, günde <b>1.500 istek</b>. Oyun içi hızlı çeviriler için en verimli ve kotası en bol modeldir.</li>
            <li><b>Gemini Pro (1.5 / 2.5 Pro):</b> Dakikada yalnızca <b>2 ila 5 istek</b>! Üst üste çoklu test yaparsanız hemen <i>429 Too Many Requests</i> hatası verir.</li>
        </ul>

        <h4 style="color:#00e5ff; margin-bottom:4px;">2. NVIDIA NIM API:</h4>
        <ul>
            <li>Hesap oluşturulduğunda verilen <b>1.000 ücretsiz krediyle</b> çalışır.</li>
            <li><b>Llama 3.1 8B:</b> Düşük kredi harcar ve hızlıdır.</li>
            <li><b>Llama 3.1 70B & DeepSeek R1:</b> Yüksek zeka ve edebi kalite sunar, testlerde dikkatli kullanılmalıdır.</li>
        </ul>

        <h4 style="color:#ffd700; margin-bottom:4px;">💡 Kota Tasarrufu İpuçları:</h4>
        <p>Aynı anda 2-4 model karşılaştırmak en sağlıklısıdır. Testler arasına 10-15 saniye koymak dakikalık hız sınırına takılmanızı önler.</p>
        """)
        layout.addWidget(browser)

        btn_close = QPushButton("Anladım", self)
        btn_close.setStyleSheet("background-color: #242436; color: #fff; border-radius: 4px; padding: 6px;")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)
from PyQt6.QtWidgets import QCheckBox

class HighQuotaWarningDialog(QDialog):
    """Çoklu model testinde kullanıcıyı uyaran ve 'tekrar gösterme' seçeneği olan minimalist diyalog."""
    def __init__(self, model_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kota Uyarısı")
        self.setFixedSize(380, 180)
        self.setStyleSheet("""
            QDialog { background-color: #161622; }
            QLabel { color: #dcdce6; font-size: 12px; }
            QCheckBox { color: #8e8e9f; font-size: 11px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QPushButton {
                background-color: #00c3ff;
                color: #000;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton#cancelBtn {
                background-color: #262636;
                color: #fff;
                border: 1px solid #3c3c50;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(12)

        lbl_msg = QLabel(
            f"Aynı anda <b>{model_count} farklı model</b> test edilecek.<br><br>"
            "Ücretsiz API planlarında eşzamanlı çok fazla istek göndermek "
            "dakikalık hız sınırına (429) takılmanıza neden olabilir. Devam edilsin mi?"
        )
        lbl_msg.setWordWrap(True)
        lay.addWidget(lbl_msg)

        self.cb_dont_show = QCheckBox("Bu uyarıyı bir daha gösterme")
        lay.addWidget(self.cb_dont_show)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("Yine de Devam Et")
        self.btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        lay.addLayout(btn_row)

    def dont_show_again(self) -> bool:
        return self.cb_dont_show.isChecked()

class GeminiBenchmarkTab(QWidget):
    config_updated = pyqtSignal(str, str, str)

    def __init__(self, current_api_key="", current_nvidia_key="", current_model="gemini-1.5-flash", parent=None):
        super().__init__(parent)
        self.api_key = current_api_key
        self.nvidia_key = current_nvidia_key
        self.selected_model = current_model
        
        self.cooldown_remaining = 0
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self._tick_cooldown)

        self.translator = GeminiTranslator(
            api_key=self.api_key,
            nvidia_key=self.nvidia_key,
            model_name=self.selected_model
        )

        self.init_ui()
        if self.api_key or self.nvidia_key:
            self.fetch_models()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. API ANAHTARLARI KARTI
        keys_card = QFrame(self)
        keys_card.setStyleSheet("background-color: #161622; border: 1px solid #2a2a3a; border-radius: 6px; padding: 6px;")
        keys_layout = QVBoxLayout(keys_card)
        keys_layout.setContentsMargins(8, 8, 8, 8)
        keys_layout.setSpacing(6)

        # Üst Başlık & Rehber Butonu
        k_header = QHBoxLayout()
        lbl_k_title = QLabel("AI API Yapılandırması")
        lbl_k_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
        
        btn_guide = QPushButton("ⓘ Ücretsiz Limitler & İpuçları")
        btn_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guide.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #00c3ff;
                border: 1px solid #00c3ff;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #112836; }
        """)
        btn_guide.clicked.connect(lambda: QuotaGuideDialog(self).exec())

        k_header.addWidget(lbl_k_title)
        k_header.addStretch()
        k_header.addWidget(btn_guide)
        keys_layout.addLayout(k_header)

        # Gemini
        gem_box = QHBoxLayout()
        lbl_gem = QLabel("Google Gemini API:")
        lbl_gem.setFixedWidth(120)
        lbl_gem.setStyleSheet("color: #b0b0c0; font-size: 11px;")
        self.key_input = QLineEdit(keys_card)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setText(self.api_key)
        self.key_input.setPlaceholderText("AIzaSy...")
        self.btn_show_key = QPushButton(keys_card)
        self.btn_show_key.setFixedSize(30, 26)
        self.btn_show_key.setIcon(create_eye_icon(closed=True))
        self.btn_show_key.clicked.connect(self.toggle_key_visibility)
        gem_box.addWidget(lbl_gem)
        gem_box.addWidget(self.key_input)
        gem_box.addWidget(self.btn_show_key)
        keys_layout.addLayout(gem_box)

        # NVIDIA
        nv_box = QHBoxLayout()
        lbl_nv = QLabel("NVIDIA NIM API:")
        lbl_nv.setFixedWidth(120)
        lbl_nv.setStyleSheet("color: #b0b0c0; font-size: 11px;")
        self.nv_key_input = QLineEdit(keys_card)
        self.nv_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.nv_key_input.setText(self.nvidia_key)
        self.nv_key_input.setPlaceholderText("nvapi-...")
        self.btn_show_nv_key = QPushButton(keys_card)
        self.btn_show_nv_key.setFixedSize(30, 26)
        self.btn_show_nv_key.setIcon(create_eye_icon(closed=True))
        self.btn_show_nv_key.clicked.connect(self.toggle_nv_key_visibility)
        nv_box.addWidget(lbl_nv)
        nv_box.addWidget(self.nv_key_input)
        nv_box.addWidget(self.btn_show_nv_key)
        keys_layout.addLayout(nv_box)

        self.btn_save_key = QPushButton("💾 Anahtarları Kaydet & Modelleri Getir", keys_card)
        self.btn_save_key.setStyleSheet("background-color: #00c3ff; color: #000; font-weight: bold; border-radius: 4px; padding: 6px; font-size: 11px;")
        self.btn_save_key.clicked.connect(self.fetch_models)
        keys_layout.addWidget(self.btn_save_key)

        layout.addWidget(keys_card)

        # 2. MODEL LİSTESİ VE MODEL REHBERİ
        model_selection_row = QHBoxLayout()

        left_box = QVBoxLayout()
        lbl_list_info = QLabel("Aktif AI Modelleri (Karşılaştırmak istediklerinizi işaretleyin):")
        lbl_list_info.setStyleSheet("color: #b0b0b8; font-size: 11px;")

        self.model_list = QListWidget(self)
        self.model_list.setFixedHeight(130)
        self.model_list.itemClicked.connect(self.on_model_item_clicked)
        left_box.addWidget(lbl_list_info)
        left_box.addWidget(self.model_list)
        model_selection_row.addLayout(left_box, stretch=3)

        self.guide_card = QFrame(self)
        self.guide_card.setStyleSheet("background-color: #161622; border: 1px solid #2a2a3a; border-radius: 6px; padding: 8px;")
        guide_layout = QVBoxLayout(self.guide_card)
        guide_layout.setContentsMargins(6, 6, 6, 6)

        self.lbl_guide_title = QLabel("Model Rehberi", self.guide_card)
        self.lbl_guide_title.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 12px;")
        self.lbl_guide_desc = QLabel("Listeden bir modele tıkladığınızda özellikleri ve kota maliyeti burada gösterilir.", self.guide_card)
        self.lbl_guide_desc.setWordWrap(True)
        self.lbl_guide_desc.setStyleSheet("color: #cccccc; font-size: 11px;")

        self.btn_set_active = QPushButton("Bu Modeli Varsayılan Yap", self.guide_card)
        self.btn_set_active.setStyleSheet("background-color: #252536; color: #fff; border: 1px solid #44445a; border-radius: 4px; padding: 4px;")
        self.btn_set_active.clicked.connect(self.set_active_model)

        guide_layout.addWidget(self.lbl_guide_title)
        guide_layout.addWidget(self.lbl_guide_desc)
        guide_layout.addStretch()
        guide_layout.addWidget(self.btn_set_active)

        model_selection_row.addWidget(self.guide_card, stretch=2)
        layout.addLayout(model_selection_row)

       
    def toggle_key_visibility(self):
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_key.setIcon(create_eye_icon(closed=False, color="#00c3ff"))
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_key.setIcon(create_eye_icon(closed=True, color="#8e8e9f"))

    def toggle_nv_key_visibility(self):
        if self.nv_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.nv_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_nv_key.setIcon(create_eye_icon(closed=False, color="#00ffaa"))
        else:
            self.nv_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_nv_key.setIcon(create_eye_icon(closed=True, color="#8e8e9f"))

    def fetch_models(self):
        g_key = self.key_input.text().strip()
        nv_key = self.nv_key_input.text().strip()

        if not g_key and not nv_key:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir API anahtarı (Google Gemini veya NVIDIA NIM) girin.")
            return

        self.api_key = g_key
        self.nvidia_key = nv_key

        if g_key: self.translator.configure_gemini(g_key)
        if nv_key: self.translator.configure_nvidia(nv_key)

        models = self.translator.list_available_models()
        self.model_list.blockSignals(True)
        self.model_list.clear()

        for m in models:
            item = QListWidgetItem(self.model_list)
            info = MODEL_DESCRIPTIONS.get(m, {})
            tag = info.get("tag", "")

            item.setText(f"{m}  {tag}".strip())
            item.setData(Qt.ItemDataRole.UserRole, m)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            if m in ["gemini-1.5-flash", "meta/llama-3.1-8b-instruct"]:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            self.model_list.addItem(item)

        self.model_list.blockSignals(False)
        self.config_updated.emit(self.api_key, self.nvidia_key, self.selected_model)
        self.update_quota_indicator()
        QMessageBox.information(self, "Başarılı", f"Kullanılabilir {len(models)} model listelendi!")

    def on_model_item_clicked(self, item: QListWidgetItem):
        m_name = item.data(Qt.ItemDataRole.UserRole)
        info = MODEL_DESCRIPTIONS.get(m_name, {
            "tag": "🌐 Model",
            "desc": "Tepki süresi ve çeviri tutarlılığını Tam Ekran Laboratuvar üzerinden kıyaslayabilirsiniz."
        })
        self.lbl_guide_title.setText(f"{m_name}\n{info.get('tag', '')}")
        self.lbl_guide_desc.setText(info.get("desc", ""))


    def set_active_model(self):
        curr_item = self.model_list.currentItem()
        if not curr_item: return
        m_name = curr_item.data(Qt.ItemDataRole.UserRole)
        self.selected_model = m_name
        self.translator.model_name = m_name
        self.config_updated.emit(self.api_key, self.nvidia_key, self.selected_model)
        QMessageBox.information(self, "Başarılı", f"Varsayılan çeviri modeli güncellendi:\n{m_name}")

    def get_checked_models(self):
        checked = []
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.data(Qt.ItemDataRole.UserRole))
        return checked

    def start_benchmark(self):
        if self.cooldown_remaining > 0:
            QMessageBox.warning(self, "Kota Koruması Aktif", f"Lütfen dakikalık API kotanızı korumak için {self.cooldown_remaining} saniye bekleyin.")
            return

        selected = self.get_checked_models()
        if len(selected) < 2:
            QMessageBox.warning(self, "Seçim Yetersiz", "Karşılaştırma yapabilmek için en az 2 model işaretleyin.")
            return
        if len(selected) > 12:
            QMessageBox.warning(self, "Sınır Aşıldı", "Kota koruması nedeniyle aynı anda en fazla 12 model seçebilirsiniz.")
            return

        text = self.test_text_input.text().strip()
        if not text:
            QMessageBox.warning(self, "Metin Boş", "Lütfen test edilecek bir metin girin.")
            return

        # 4 veya daha fazla model seçildiğinde açılan akıllı onay penceresi
        from core.config_manager import ConfigManager
        cfg = ConfigManager.load_config()
        dont_show = cfg.get("suppress_quota_warning", False)

        if len(selected) >= 4 and not dont_show:
            dlg = HighQuotaWarningDialog(len(selected), self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return  # Kullanıcı iptal etti
            
            if dlg.dont_show_again():
                cfg["suppress_quota_warning"] = True
                ConfigManager.save_config(cfg)

        # 15 Saniyelik Cooldown Başlat
        self._start_cooldown(15)

        self.fullscreen_lab = FullscreenBenchmarkWindow(
            translator=self.translator,
            initial_text=text,
            selected_models=selected,
            parent=self.window()
        )
        self.fullscreen_lab.showMaximized()

    def _start_cooldown(self, seconds: int):
        self.cooldown_remaining = seconds
        self.btn_run_bench.setEnabled(False)
        self.btn_run_bench.setText(f"⏳ Kota Soğuması ({self.cooldown_remaining}s)")
        self.btn_run_bench.setStyleSheet("background-color: #2c2c3a; color: #8e8e9f; font-weight: bold; border-radius: 4px; padding: 6px 14px;")
        self.cooldown_timer.start(1000)

    def _tick_cooldown(self):
        self.cooldown_remaining -= 1
        if self.cooldown_remaining <= 0:
            self.cooldown_timer.stop()
            self.btn_run_bench.setEnabled(True)
            self.btn_run_bench.setText("⛶ Tam Ekran Laboratuvarda Karşılaştır")
            self.btn_run_bench.setStyleSheet("background-color: #00ffaa; color: #000; font-weight: bold; border-radius: 4px; padding: 6px 14px;")
        else:
            self.btn_run_bench.setText(f"⏳ Kota Soğuması ({self.cooldown_remaining}s)")