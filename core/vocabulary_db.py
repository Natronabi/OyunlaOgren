import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vocabulary.db")

class VocabularyDB:
    # Agresif seyrekleşen SRS gün aralıkları:
    # Seviye 0: Hemen (Aynı gün)
    # Seviye 1: 1 gün sonra
    # Seviye 2: 4 gün sonra
    # Seviye 3: 12 gün sonra
    # Seviye 4: 30 gün (1 ay) sonra
    # Seviye 5: 90 gün (3 ay) sonra -> Ustalaşıldı
    SRS_INTERVALS = {
        0: 0,
        1: 1,
        2: 4,
        3: 12,
        4: 30,
        5: 90
    }

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    meaning TEXT NOT NULL,
                    level TEXT DEFAULT 'B1',
                    game_title TEXT DEFAULT 'Genel',
                    context_sentence TEXT DEFAULT '',
                    srs_stage INTEGER DEFAULT 0,
                    interval_days INTEGER DEFAULT 0,
                    next_review_date TEXT NOT NULL,
                    times_correct INTEGER DEFAULT 0,
                    times_wrong INTEGER DEFAULT 0,
                    mastered INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_word(self, word: str, meaning: str, level: str = "B1", game_title: str = "Oyun", context_sentence: str = "") -> bool:
        """Yeni kelime ekler veya zaten varsa bağlamını günceller."""
        word_clean = word.strip().lower()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vocabulary WHERE word = ?", (word_clean,))
            row = cursor.fetchone()
            
            if row:
                # Zaten varsa sadece bağlamı ve anlamı tazele
                cursor.execute("""
                    UPDATE vocabulary 
                    SET meaning = ?, context_sentence = ?, game_title = ?
                    WHERE id = ?
                """, (meaning, context_sentence, game_title, row["id"]))
                conn.commit()
                return False
            else:
                cursor.execute("""
                    INSERT INTO vocabulary (
                        word, meaning, level, game_title, context_sentence,
                        srs_stage, interval_days, next_review_date,
                        times_correct, times_wrong, mastered, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 0, 0, 0, ?)
                """, (word_clean, meaning, level, game_title, context_sentence, today_str, today_str))
                conn.commit()
                return True

    def get_review_words(self, limit: int = 15):
        """Bugün tekrar edilmesi gereken kelimeleri getirir."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM vocabulary 
                WHERE next_review_date <= ? AND mastered = 0
                ORDER BY srs_stage ASC, next_review_date ASC
                LIMIT ?
            """, (today_str, limit))
            return [dict(r) for r in cursor.fetchall()]

    def record_answer(self, word_id: int, is_correct: bool):
        """Kullanıcının test cevabına göre agresif SRS takvimini hesaplar."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
            item = cursor.fetchone()
            if not item:
                return

            stage = item["srs_stage"]
            correct_cnt = item["times_correct"]
            wrong_cnt = item["times_wrong"]
            mastered = 0

            if is_correct:
                stage = min(5, stage + 1)
                correct_cnt += 1
                if stage >= 5:
                    mastered = 1  # 5. aşamaya varan ustalaşmış sayılır
            else:
                stage = 1  # Yanlışta hemen 1. seviyeye düşür
                wrong_cnt += 1

            interval = self.SRS_INTERVALS.get(stage, 1)
            next_date = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")

            cursor.execute("""
                UPDATE vocabulary 
                SET srs_stage = ?, interval_days = ?, next_review_date = ?,
                    times_correct = ?, times_wrong = ?, mastered = ?
                WHERE id = ?
            """, (stage, interval, next_date, correct_cnt, wrong_cnt, mastered, word_id))
            conn.commit()