import os
import threading
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore


class CloudSyncManager:
    """PC Yerel SQLite ile Firebase Firestore Arasında Çift Yönlü Eşitleme Motoru."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CloudSyncManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, key_filename: str = "serviceAccountKey.json"):
        if self._initialized:
            return

        self.db = None
        self.is_connected = False
        self._init_firebase(key_filename)
        self._initialized = True

    def _init_firebase(self, key_filename: str):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        key_path = os.path.join(base_dir, key_filename)

        if not os.path.exists(key_path):
            print(f"[UYARI] {key_filename} bulunamadı. Bulut senkronizasyonu devre dışı.")
            return

        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.is_connected = True
            print("[CloudSync] Firebase Firestore bulut bağlantısı başarılı.")
        except Exception as e:
            print(f"[BULUT HATA] Firebase başlatılamadı: {e}")
            self.is_connected = False

    def is_configured(self) -> bool:
        return self.is_connected and self.db is not None

    def push_word(self, word_data: dict, on_success=None) -> bool:
        if not self.is_configured():
            return False

        threading.Thread(target=self._push_word_worker, args=(word_data, on_success), daemon=True).start()
        return True

    def _push_word_worker(self, word_data: dict, on_success=None):
        try:
            word_key = word_data["word"].strip().lower()
            doc_ref = self.db.collection("vocabulary").document(word_key)

            payload = {
                "word": word_data["word"],
                "meaning": word_data["meaning"],
                "level": word_data.get("level", "B1"),
                "game_title": word_data.get("game_title", "Genel"),
                "context_sentence": word_data.get("context_sentence", ""),
                "srs_stage": word_data.get("srs_stage", 0),
                "streak_count": word_data.get("streak_count", 0),
                "interval_days": word_data.get("interval_days", 0),
                "next_review_date": word_data.get("next_review_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "times_correct": word_data.get("times_correct", 0),
                "times_wrong": word_data.get("times_wrong", 0),
                "mastered": bool(word_data.get("mastered", 0)),
                "updated_at": datetime.now().isoformat()
            }

            doc_ref.set(payload, merge=True)
            print(f"[CloudSync] Firestore'a eşitlendi: {word_data['word']}")
            if on_success:
                on_success()
        except Exception as e:
            print(f"[BULUT HATA] Kelime buluta iletilemedi ({word_data.get('word')}): {e}")

    def flush_unsynced(self, local_db):
        """İnternet aktif olduğunda SQLite'ta bekleyen (is_synced=0) tüm kayıtları Firestore'a aktarır."""
        unsynced = local_db.get_unsynced_words()
        if not unsynced or not self.is_configured():
            return

        def _batch_worker():
            synced_words = []
            try:
                batch = self.db.batch()
                for item in unsynced:
                    w_key = item["word"].strip().lower()
                    doc_ref = self.db.collection("vocabulary").document(w_key)
                    batch.set(doc_ref, {
                        "word": item["word"],
                        "meaning": item["meaning"],
                        "level": item.get("level", "B1"),
                        "game_title": item.get("game_title", "Oyun"),
                        "context_sentence": item.get("context_sentence", ""),
                        "srs_stage": item.get("repetition_level", 0),
                        "streak_count": item.get("streak_count", 0),
                        "next_review_date": item.get("next_review_date", ""),
                        "updated_at": datetime.now().isoformat()
                    }, merge=True)
                    synced_words.append(w_key)

                batch.commit()
                local_db.mark_as_synced(synced_words)
                print(f"[CloudSync] Bekleyen {len(synced_words)} kelime buluta aktarıldı.")
            except Exception as e:
                print(f"[BULUT HATA] Toplu eşitleme başarısız: {e}")

        threading.Thread(target=_batch_worker, daemon=True).start()

    def delete_words(self, words: list):
        if not self.is_configured() or not words:
            return

        threading.Thread(target=self._delete_words_worker, args=(words,), daemon=True).start()

    def _delete_words_worker(self, words: list):
        try:
            batch = self.db.batch()
            for w in words:
                word_key = w.strip().lower()
                doc_ref = self.db.collection("vocabulary").document(word_key)
                batch.delete(doc_ref)
            batch.commit()
            print(f"[CloudSync] {len(words)} kayıt Firestore'dan silindi.")
        except Exception as e:
            print(f"[BULUT HATA] Toplu silme hatası: {e}")

    def sync_all(self, local_db) -> dict:
        if not self.is_configured():
            return {"status": "error", "message": "Bulut bağlantısı yapılandırılmamış."}

        try:
            docs = self.db.collection("vocabulary").stream()
            remote_words = [d.to_dict() for d in docs]

            with local_db.get_connection() as conn:
                cursor = conn.cursor()
                for rw in remote_words:
                    cursor.execute("""
                        INSERT INTO vocabulary (
                            word, meaning, level, game_title, context_sentence,
                            repetition_level, streak_count, next_review_date,
                            created_at, is_synced
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        ON CONFLICT(word) DO UPDATE SET
                            meaning = excluded.meaning,
                            repetition_level = excluded.repetition_level,
                            streak_count = excluded.streak_count,
                            next_review_date = excluded.next_review_date,
                            is_synced = 1
                    """, (
                        rw["word"], rw["meaning"], rw.get("level", "B1"),
                        rw.get("game_title", "Genel"), rw.get("context_sentence", ""),
                        rw.get("srs_stage", 0), rw.get("streak_count", 0),
                        rw.get("next_review_date", ""),
                        rw.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    ))
                conn.commit()

            return {"status": "success", "count": len(remote_words)}
        except Exception as e:
            return {"status": "error", "message": str(e)}