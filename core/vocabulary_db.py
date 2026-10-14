import sqlite3
import os
from datetime import datetime, timedelta
from core.cloud_sync import CloudSyncManager


class VocabularyDB:
    def __init__(self, db_path: str = "data/vocabulary.db"):
        self.db_path = db_path
        self.cloud_sync = CloudSyncManager()
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
                    last_reviewed TIMESTAMP,
                    is_synced INTEGER DEFAULT 0
                )
            """)

            cursor.execute("PRAGMA table_info(vocabulary)")
            columns = [col[1] for col in cursor.fetchall()]

            new_columns = {
                "repetition_level": "INTEGER DEFAULT 0",
                "streak_count": "INTEGER DEFAULT 0",
                "next_review_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "last_reviewed": "TIMESTAMP",
                "is_synced": "INTEGER DEFAULT 0"
            }

            for col_name, col_def in new_columns.items():
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE vocabulary ADD COLUMN {col_name} {col_def}")

            conn.commit()

    def add_word(self, word: str, meaning: str, level: str = "B1", 
                 game_title: str = "Oyun", context_sentence: str = "") -> bool:
        clean_word = word.strip().lower()
        if not clean_word:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vocabulary 
                (word, meaning, level, game_title, context_sentence, created_at, next_review_date, is_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(word) DO UPDATE SET
                    meaning = excluded.meaning,
                    level = excluded.level,
                    is_synced = 0,
                    context_sentence = CASE 
                        WHEN length(excluded.context_sentence) > 0 THEN excluded.context_sentence 
                        ELSE vocabulary.context_sentence 
                    END
            """, (clean_word, meaning.strip(), level, game_title, context_sentence.strip(), now_str, now_str))
            conn.commit()

        # Firestore'a asenkron gönder, başarılı olursa yerelde is_synced=1 yap
        self.cloud_sync.push_word({
            "word": clean_word,
            "meaning": meaning.strip(),
            "level": level,
            "game_title": game_title,
            "context_sentence": context_sentence.strip(),
            "srs_stage": 0,
            "next_review_date": now_str
        }, on_success=lambda: self.mark_as_synced([clean_word]))
        return True

    def mark_as_synced(self, words: list):
        if not words:
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in words)
            cursor.execute(f"UPDATE vocabulary SET is_synced = 1 WHERE word IN ({placeholders})", words)
            conn.commit()

    def get_unsynced_count(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE is_synced = 0")
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_unsynced_words(self) -> list:
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vocabulary WHERE is_synced = 0")
            return [dict(row) for row in cursor.fetchall()]

    def delete_words(self, words: list) -> bool:
        if not words:
            return False

        clean_words = [w.strip().lower() for w in words]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in clean_words)
            cursor.execute(f"DELETE FROM vocabulary WHERE word IN ({placeholders})", clean_words)
            conn.commit()

        self.cloud_sync.delete_words(clean_words)
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
            cursor.execute("SELECT word, meaning, repetition_level, streak_count FROM vocabulary WHERE id = ?", (word_id,))
            row = cursor.fetchone()
            if not row:
                return

            word_val = row["word"]
            meaning_val = row["meaning"]
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

            next_date_str = next_date.strftime("%Y-%m-%d %H:%M:%S")
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                UPDATE vocabulary 
                SET repetition_level = ?,
                    streak_count = ?,
                    next_review_date = ?,
                    last_reviewed = ?,
                    is_synced = 0
                WHERE id = ?
            """, (rep_level, streak, next_date_str, now_str, word_id))
            conn.commit()

        self.cloud_sync.push_word({
            "word": word_val,
            "meaning": meaning_val,
            "srs_stage": rep_level,
            "streak_count": streak,
            "next_review_date": next_date_str
        }, on_success=lambda: self.mark_as_synced([word_val]))