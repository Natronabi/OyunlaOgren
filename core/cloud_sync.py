import os
from datetime import datetime
try:
    from supabase import create_client, Client
except ImportError:
    Client = None

from core.vocabulary_db import VocabularyDB

class CloudSyncManager:
    """PC Yerel SQLite ile Supabase Bulutu Arasında Çift Yönlü Eşitleme Motoru."""

    def __init__(self, supabase_url: str = "", supabase_key: str = "", user_id: str = "default_user"):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.user_id = user_id
        self.client: Client = None

        if self.supabase_url and self.supabase_key and Client:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                print(f"[UYARI] Supabase bağlantısı kurulamadı: {e}")

    def is_configured(self) -> bool:
        return self.client is not None

    def push_word(self, word_data: dict) -> bool:
        """Yeni eklenen kelimeyi anında buluta yollar."""
        if not self.is_configured():
            return False

        try:
            payload = {
                "user_id": self.user_id,
                "word": word_data["word"],
                "meaning": word_data["meaning"],
                "level": word_data.get("level", "B1"),
                "game_title": word_data.get("game_title", "Genel"),
                "context_sentence": word_data.get("context_sentence", ""),
                "srs_stage": word_data.get("srs_stage", 0),
                "interval_days": word_data.get("interval_days", 0),
                "next_review_date": word_data.get("next_review_date", datetime.now().strftime("%Y-%m-%d")),
                "times_correct": word_data.get("times_correct", 0),
                "times_wrong": word_data.get("times_wrong", 0),
                "mastered": bool(word_data.get("mastered", 0))
            }
            # upsert: varsa güncelle, yoksa ekle
            self.client.table("user_vocabulary").upsert(payload, on_conflict="user_id,word").execute()
            return True
        except Exception as e:
            print(f"[BULUT HATA] Kelime buluta iletilemedi: {e}")
            return False

    def sync_all(self, local_db: VocabularyDB) -> dict:
        """Telefonda yapılan alıştırmaları PC'ye çeker, PC'dekileri buluta gönderir."""
        if not self.is_configured():
            return {"status": "error", "message": "Bulut bağlantısı yapılandırılmamış."}

        try:
            # 1. Buluttaki en güncel kelimeleri al
            res = self.client.table("user_vocabulary").select("*").eq("user_id", self.user_id).execute()
            remote_words = res.data or []

            # 2. Yerel veritabanına işle
            with local_db.get_connection() as conn:
                cursor = conn.cursor()
                for rw in remote_words:
                    cursor.execute("""
                        INSERT INTO vocabulary (
                            word, meaning, level, game_title, context_sentence,
                            srs_stage, interval_days, next_review_date,
                            times_correct, times_wrong, mastered, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(word) DO UPDATE SET
                            meaning = excluded.meaning,
                            srs_stage = excluded.srs_stage,
                            interval_days = excluded.interval_days,
                            next_review_date = excluded.next_review_date,
                            times_correct = excluded.times_correct,
                            times_wrong = excluded.times_wrong,
                            mastered = excluded.mastered
                    """, (
                        rw["word"], rw["meaning"], rw.get("level", "B1"),
                        rw.get("game_title", "Genel"), rw.get("context_sentence", ""),
                        rw.get("srs_stage", 0), rw.get("interval_days", 0),
                        rw.get("next_review_date", ""), rw.get("times_correct", 0),
                        rw.get("times_wrong", 0), 1 if rw.get("mastered") else 0,
                        rw.get("created_at", datetime.now().strftime("%Y-%m-%d"))
                    ))
                conn.commit()

            return {"status": "success", "count": len(remote_words)}
        except Exception as e:
            return {"status": "error", "message": str(e)}