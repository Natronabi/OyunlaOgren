from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from core.quiz_engine import QuizEngine, QuizQuestion
from core.vocabulary_db import VocabularyDB


class PracticeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GameLingo - Pratik ve Kelime Tekrarı")
        self.setFixedSize(620, 680)
        self.setStyleSheet("background-color: #121218; color: #ffffff;")

        self.db = VocabularyDB()
        self.engine = QuizEngine(self.db)
        
        self.questions = []
        self.current_q_index = 0
        self.hearts = 5
        self.selected_choice = None
        self.scramble_selected = []
        self.first_match_btn = None
        self.matched_count = 0
        self.target_matches = 0
        self.match_pairs = {}
        self.choice_buttons = []

        self.init_ui()
        self.start_session()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(16)

        top_bar = QHBoxLayout()
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #777788; font-size: 16px; border: none; font-weight: bold;
            }
            QPushButton:hover { color: #ff5555; }
        """)
        self.close_btn.clicked.connect(self.close)
        top_bar.addWidget(self.close_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #242432;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #58cc02;
                border-radius: 6px;
            }
        """)
        top_bar.addWidget(self.progress_bar, stretch=1)

        self.lbl_hearts = QLabel("❤️ 5")
        self.lbl_hearts.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff4b4b; padding-left: 8px;")
        top_bar.addWidget(self.lbl_hearts)

        self.main_layout.addLayout(top_bar)

        self.card_area = QWidget()
        self.card_layout = QVBoxLayout(self.card_area)
        self.card_layout.setContentsMargins(0, 10, 0, 10)
        self.card_layout.setSpacing(14)

        # HTML etiketlerini (<b> vb.) düzgün render etmesi için RichText formatı açıldı
        self.lbl_prompt = QLabel("Soru yükleniyor...")
        self.lbl_prompt.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_prompt.setWordWrap(True)
        self.lbl_prompt.setStyleSheet("font-size: 18px; font-weight: 600; color: #f0f0f5; line-height: 1.4;")
        self.card_layout.addWidget(self.lbl_prompt)

        self.interactive_container = QWidget()
        self.interactive_layout = QVBoxLayout(self.interactive_container)
        self.interactive_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.addWidget(self.interactive_container)

        self.main_layout.addWidget(self.card_area, stretch=1)

        self.bottom_banner = QFrame()
        self.bottom_banner.setFixedHeight(95)
        self.bottom_layout = QHBoxLayout(self.bottom_banner)
        self.bottom_layout.setContentsMargins(20, 10, 20, 10)

        self.banner_text_box = QVBoxLayout()
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 17px; font-weight: bold;")
        self.lbl_substatus = QLabel("")
        self.lbl_substatus.setStyleSheet("font-size: 12px; color: #dddddd;")
        self.banner_text_box.addWidget(self.lbl_status)
        self.banner_text_box.addWidget(self.lbl_substatus)
        self.bottom_layout.addLayout(self.banner_text_box, stretch=1)

        self.action_btn = QPushButton("KONTROL ET")
        self.action_btn.setFixedSize(140, 44)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self.handle_action_click)
        self.bottom_layout.addWidget(self.action_btn)

        self.reset_bottom_banner()
        self.main_layout.addWidget(self.bottom_banner)

    def reset_bottom_banner(self):
        self.bottom_banner.setStyleSheet("background-color: transparent; border-top: 1px solid #22222e;")
        self.lbl_status.setText("")
        self.lbl_substatus.setText("")
        self.action_btn.setText("KONTROL ET")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #58cc02;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background-color: #61e002; }
            QPushButton:disabled { background-color: #2b2b38; color: #666677; }
        """)
        self.action_btn.setEnabled(False)

    def start_session(self):
        self.questions = self.engine.generate_quiz_session(question_count=8)
        self.current_q_index = 0
        self.hearts = 5
        self.lbl_hearts.setText(f"❤️ {self.hearts}")

        if not self.questions:
            self.lbl_prompt.setText("Tebrikler! Şu an tekrar edilmesi gereken kelime bulunmuyor veya kelime listeniz boş.")
            self.interactive_container.hide()
            self.bottom_banner.hide()
            return

        self.interactive_container.show()
        self.bottom_banner.show()
        self.progress_bar.setRange(0, len(self.questions))
        self.progress_bar.setValue(0)
        self.show_question()

    def show_question(self):
        self.reset_bottom_banner()
        self.clear_interactive_layout()

        if self.current_q_index >= len(self.questions):
            self.show_completion_screen()
            return

        self.progress_bar.setValue(self.current_q_index)
        q: QuizQuestion = self.questions[self.current_q_index]
        self.lbl_prompt.setText(q.prompt)
        self.lbl_prompt.setTextFormat(Qt.TextFormat.RichText)

        if q.q_type == "choice":
            self.build_choice_ui(q)
        elif q.q_type == "scramble":
            self.build_scramble_ui(q)
        elif q.q_type == "match":
            self.build_match_ui(q)

    def clear_interactive_layout(self):
        while self.interactive_layout.count():
            item = self.interactive_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

    def build_choice_ui(self, q: QuizQuestion):
        self.selected_choice = None
        self.choice_buttons = []

        grid = QGridLayout()
        grid.setSpacing(10)

        btn_style = """
            QPushButton {
                background-color: #1a1a24;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: 500;
                padding: 14px;
                border: 2px solid #2e2e42;
                border-radius: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #242436;
                border: 2px solid #00c3ff;
            }
        """

        for idx, opt in enumerate(q.options):
            btn = QPushButton(f"{chr(65+idx)})  {opt}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, text=opt, b=btn: self.select_choice(text, b))
            grid.addWidget(btn, idx // 2, idx % 2)
            self.choice_buttons.append(btn)

        self.interactive_layout.addLayout(grid)

    def select_choice(self, text: str, clicked_btn: QPushButton):
        self.selected_choice = text
        self.action_btn.setEnabled(True)

        for btn in self.choice_buttons:
            if btn == clicked_btn:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a2c3a;
                        color: #00c3ff;
                        font-size: 14px;
                        font-weight: bold;
                        padding: 14px;
                        border: 2px solid #00c3ff;
                        border-radius: 12px;
                        text-align: left;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1a1a24;
                        color: #888899;
                        font-size: 14px;
                        padding: 14px;
                        border: 2px solid #242436;
                        border-radius: 12px;
                        text-align: left;
                    }
                """)

    def build_scramble_ui(self, q: QuizQuestion):
        self.scramble_selected = []
        
        self.slot_area = QFrame()
        self.slot_area.setMinimumHeight(60)
        self.slot_area.setStyleSheet("background-color: #171722; border: 1px dashed #3a3a52; border-radius: 10px;")
        self.slot_layout = QHBoxLayout(self.slot_area)
        self.slot_layout.setContentsMargins(10, 8, 10, 8)
        self.slot_layout.setSpacing(6)
        self.interactive_layout.addWidget(self.slot_area)

        self.interactive_layout.addSpacing(16)

        self.bank_area = QWidget()
        self.bank_layout = QHBoxLayout(self.bank_area)
        self.bank_layout.setSpacing(8)

        token_style = """
            QPushButton {
                background-color: #242436;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 14px;
                border: 1px solid #3d3d58;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2e2e48; border-color: #00c3ff; }
        """

        for word in q.options:
            btn = QPushButton(word)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(token_style)
            btn.clicked.connect(lambda _, w=word, b=btn: self.on_token_clicked(w, b))
            self.bank_layout.addWidget(btn)

        self.interactive_layout.addWidget(self.bank_area)

    def on_token_clicked(self, word: str, btn: QPushButton):
        btn.setEnabled(False)
        btn.setStyleSheet("background-color: #181822; color: #444455; border: 1px solid #222230; border-radius: 8px;")

        slot_btn = QPushButton(word)
        slot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        slot_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
            }
        """)
        
        self.scramble_selected.append(word)
        self.action_btn.setEnabled(True)

        def remove_from_slot():
            if word in self.scramble_selected:
                self.scramble_selected.remove(word)
            slot_btn.deleteLater()
            btn.setEnabled(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #242436;
                    color: #ffffff;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 10px 14px;
                    border: 1px solid #3d3d58;
                    border-radius: 8px;
                }
            """)
            if not self.scramble_selected:
                self.action_btn.setEnabled(False)

        slot_btn.clicked.connect(remove_from_slot)
        self.slot_layout.addWidget(slot_btn)

    def build_match_ui(self, q: QuizQuestion):
        import random

        self.match_pairs = q.extra.get("pairs", {})
        self.first_match_btn = None
        self.matched_count = 0
        self.target_matches = len(self.match_pairs)

        # Ana iki sütunlu düzen: Sol İngilizce, Sağ Türkçe
        cols_container = QHBoxLayout()
        cols_container.setSpacing(20)

        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(10)
        right_vbox = QVBoxLayout()
        right_vbox.setSpacing(10)

        # Sol taraf için İngilizce kelimeler, sağ taraf için Türkçe karşılıklar
        english_words = list(self.match_pairs.keys())
        turkish_words = list(self.match_pairs.values())

        # Her iki sütunu da kendi içinde rastgele karıştır
        random.shuffle(english_words)
        random.shuffle(turkish_words)

        style = """
            QPushButton {
                background-color: #1a1a26;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 13px;
                border: 2px solid #323248;
                border-radius: 10px;
                text-align: center;
            }
            QPushButton:hover {
                border-color: #00c3ff;
                background-color: #222234;
            }
        """

        # Sol Sütun (İngilizce)
        for en_word in english_words:
            btn = QPushButton(en_word)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(style)
            btn.clicked.connect(lambda _, t=en_word, b=btn: self.on_match_click(t, b))
            left_vbox.addWidget(btn)

        # Sağ Sütun (Türkçe)
        for tr_word in turkish_words:
            btn = QPushButton(tr_word)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(style)
            btn.clicked.connect(lambda _, t=tr_word, b=btn: self.on_match_click(t, b))
            right_vbox.addWidget(btn)

        cols_container.addLayout(left_vbox, stretch=1)
        cols_container.addLayout(right_vbox, stretch=1)
        self.interactive_layout.addLayout(cols_container)

    def on_match_click(self, token: str, btn: QPushButton):
        if not self.first_match_btn:
            self.first_match_btn = (token, btn)
            btn.setStyleSheet("background-color: #1c3042; border: 2px solid #00c3ff; border-radius: 10px;")
            return

        prev_token, prev_btn = self.first_match_btn
        if prev_btn == btn:
            return

        is_pair = (
            self.match_pairs.get(prev_token) == token or 
            self.match_pairs.get(token) == prev_token
        )

        if is_pair:
            success_style = "background-color: #1a3824; border: 2px solid #58cc02; color: #58cc02; border-radius: 10px;"
            prev_btn.setStyleSheet(success_style)
            btn.setStyleSheet(success_style)
            prev_btn.setEnabled(False)
            btn.setEnabled(False)
            self.matched_count += 1

            if self.matched_count >= self.target_matches:
                self.show_feedback(True, "Tüm çiftleri başarıyla eşleştirdiniz!")
        else:
            prev_btn.setStyleSheet("background-color: #1a1a26; border: 2px solid #323248; border-radius: 10px;")

        self.first_match_btn = None

    def handle_action_click(self):
        if self.action_btn.text() == "DEVAM ET":
            self.current_q_index += 1
            self.show_question()
            return

        q: QuizQuestion = self.questions[self.current_q_index]
        is_correct = False

        if q.q_type == "choice":
            is_correct = (self.selected_choice == q.target)
        elif q.q_type == "scramble":
            assembled = " ".join(self.scramble_selected)
            is_correct = (assembled.strip().lower() == q.target.strip().lower())
        elif q.q_type == "match":
            is_correct = True

        if q.word_id > 0:
            self.db.update_word_progress(q.word_id, is_correct)

        if is_correct:
            self.show_feedback(True, "Harika! Doğru cevap.")
        else:
            self.hearts -= 1
            self.lbl_hearts.setText(f"❤️ {self.hearts}")
            self.show_feedback(False, f"Doğru Cevap: {q.target}")

            if self.hearts <= 0:
                self.show_game_over()

    def show_feedback(self, is_correct: bool, message: str):
        if is_correct:
            self.bottom_banner.setStyleSheet("background-color: #16301e; border-top: 2px solid #58cc02;")
            self.lbl_status.setText("Harika!")
            self.lbl_status.setStyleSheet("color: #58cc02; font-weight: bold; font-size: 18px;")
            self.lbl_substatus.setText(message)
            self.action_btn.setStyleSheet("background-color: #58cc02; color: #ffffff; font-weight: bold; border-radius: 10px;")
        else:
            self.bottom_banner.setStyleSheet("background-color: #38181a; border-top: 2px solid #ff4b4b;")
            self.lbl_status.setText("Yanlış...")
            self.lbl_status.setStyleSheet("color: #ff4b4b; font-weight: bold; font-size: 18px;")
            self.lbl_substatus.setText(message)
            self.action_btn.setStyleSheet("background-color: #ff4b4b; color: #ffffff; font-weight: bold; border-radius: 10px;")

        self.action_btn.setText("DEVAM ET")
        self.action_btn.setEnabled(True)

    def show_game_over(self):
        self.lbl_prompt.setText("Canlarınız tükendi! Biraz dinlenip kelimeleri tekrar gözden geçirin.")
        self.lbl_prompt.setTextFormat(Qt.TextFormat.PlainText)
        self.clear_interactive_layout()
        self.action_btn.setText("KAPAT")
        try:
            self.action_btn.clicked.disconnect()
        except Exception:
            pass
        self.action_btn.clicked.connect(self.close)

    def show_completion_screen(self):
        self.progress_bar.setValue(len(self.questions))
        self.lbl_prompt.setText("🎉 Tebrikler! Bugünkü pratik seansını başarıyla tamamladınız.")
        self.lbl_prompt.setTextFormat(Qt.TextFormat.PlainText)
        self.clear_interactive_layout()
        self.bottom_banner.setStyleSheet("background-color: #16301e; border-top: 2px solid #58cc02;")
        self.lbl_status.setText("Seans Tamamlandı")
        self.lbl_status.setStyleSheet("color: #58cc02; font-weight: bold; font-size: 18px;")
        self.lbl_substatus.setText("Kelimelerinizin aralıklı tekrar seviyeleri güncellendi.")
        self.action_btn.setText("BİTİR")
        try:
            self.action_btn.clicked.disconnect()
        except Exception:
            pass
        self.action_btn.clicked.connect(self.close)