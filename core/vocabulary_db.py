import sqlite3
import os
from datetime import datetime, timedelta


class VocabularyDB:
    def __init__(self, db_path: str = "data/vocabulary.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    meaning TEXT NOT NULL,
                    level TEXT DEFAULT 'B1',
                    game_title TEXT DEFAULT 'Oyun',
                    context_sentence TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    repetition_level INTEGER DEFAULT 0,
                    streak_count INTEGER DEFAULT 0,
                    next_review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_reviewed TIMESTAMP
                )
            """)

            cursor.execute("PRAGMA table_info(vocabulary)")
            columns = [col[1] for col in cursor.fetchall()]

            new_columns = {
                "repetition_level": "INTEGER DEFAULT 0",
                "streak_count": "INTEGER DEFAULT 0",
                "next_review_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "last_reviewed": "TIMESTAMP"
            }

            for col_name, col_def in new_columns.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE vocabulary ADD COLUMN {col_name} {col_def}")

            conn.commit()

    def add_word(self, word: str, meaning: str, level: str = "B1", 
                 game_title: str = "Oyun", context_sentence: str = ""):
        clean_word = word.strip().lower()
        if not clean_word:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO vocabulary 
                (word, meaning, level, game_title, context_sentence, created_at, next_review_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET
                    meaning = excluded.meaning,
                    level = excluded.level,
                    context_sentence = CASE 
                        WHEN length(excluded.context_sentence) > 0 THEN excluded.context_sentence 
                        ELSE vocabulary.context_sentence 
                    END
            """, (clean_word, meaning.strip(), level, game_title, context_sentence.strip(), now, now))
            conn.commit()
            return True

    def get_review_words(self, limit: int = 15) -> list:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT * FROM vocabulary 
                WHERE next_review_date <= ? OR next_review_date IS NULL
                ORDER BY repetition_level ASC, next_review_date ASC
                LIMIT ?
            """, (now, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_words(self) -> list:
        """Tüm kelime havuzunu döner (çeldiriciler ve soru oluşturma için)."""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocabulary ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_word_progress(self, word_id: int, is_correct: bool):
        intervals = {
            0: timedelta(hours=4),
            1: timedelta(days=1),
            2: timedelta(days=3),
            3: timedelta(days=7),
            4: timedelta(days=14),
            5: timedelta(days=30)
        }

        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT repetition_level, streak_count FROM vocabulary WHERE id = ?", (word_id,))
            row = cursor.fetchone()
            if not row:
                return

            rep_level = row["repetition_level"] or 0
            streak = row["streak_count"] or 0
            now = datetime.now()

            if is_correct:
                rep_level = min(rep_level + 1, 5)
                streak += 1
                next_date = now + intervals.get(rep_level, timedelta(days=30))
            else:
                rep_level = max(rep_level - 1, 0)
                streak = 0
                next_date = now + timedelta(hours=1)

            cursor.execute("""
                UPDATE vocabulary 
                SET repetition_level = ?,
                    streak_count = ?,
                    next_review_date = ?,
                    last_reviewed = ?
                WHERE id = ?
            """, (
                rep_level,
                streak,
                next_date.strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
                word_id
            ))
            conn.commit()