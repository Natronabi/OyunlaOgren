import os
from typing import Dict, Any
from core.ai_translator import AITranslator

class TranslatorManager:
    """
    Hem çevrimdışı (Argos) hem bulut (Gemini) çeviri motorlarını
    tek bir merkezden yöneten hibrit çeviri sınıfı.
    """
    def __init__(self, default_engine: str = "local"):
        # "local" veya "gemini"
        self.active_engine = default_engine
        
        self._gemini_engine = None
        self._argos_ready = False

        # Başlangıçta seçilen motoru hazırla
        if self.active_engine == "local":
            self._init_local()
        elif self.active_engine == "gemini":
            self._init_gemini()

    def _init_local(self):
        """Yerel ArgosTranslate motorunu doğrular."""
        try:
            import argostranslate.translate
            self._argos_module = argostranslate.translate
            self._argos_ready = True
        except ImportError:
            print("[TranslatorManager] argostranslate kütüphanesi bulunamadı!")
            self._argos_ready = False

    def _init_gemini(self):
        """Gemini motorunu dinamik olarak yükler."""
        if self._gemini_engine is None:
            try:
                self._gemini_engine = AITranslator()
            except Exception as e:
                print(f"[TranslatorManager] Gemini başlatılamadı: {e}")
                self._gemini_engine = None

    def set_engine(self, engine_name: str):
        """Motoru anlık olarak değiştirir ('local' veya 'gemini')."""
        if engine_name not in ["local", "gemini"]:
            raise ValueError("Geçersiz motor! Sadece 'local' veya 'gemini' seçilebilir.")
        
        self.active_engine = engine_name
        if engine_name == "local" and not self._argos_ready:
            self._init_local()
        elif engine_name == "gemini" and self._gemini_engine is None:
            self._init_gemini()

    def translate(self, text: str) -> Dict[str, Any]:
        """
        Aktif motora göre metni çevirir ve standart format döner:
        {
            "engine": "local" | "gemini",
            "translated_text": str,
            "vocabulary": list
        }
        """
        if not text or not text.strip():
            return {
                "engine": self.active_engine,
                "translated_text": "",
                "vocabulary": []
            }

        # 1. YEREL ÇEVİRİ
        if self.active_engine == "local":
            if not self._argos_ready:
                self._init_local()
            
            try:
                translated = self._argos_module.translate(text, "en", "tr")
                return {
                    "engine": "local",
                    "translated_text": translated,
                    "vocabulary": []  # Yerel motor kelime analizi yapmaz, 0ms çevirir
                }
            except Exception as e:
                return {
                    "engine": "local",
                    "translated_text": f"[Yerel Çeviri Hatası: {e}]",
                    "vocabulary": []
                }

        # 2. BULUT (GEMINI) ÇEVİRİ
        elif self.active_engine == "gemini":
            if self._gemini_engine is None:
                self._init_gemini()

            if self._gemini_engine is None:
                return {
                    "engine": "gemini",
                    "translated_text": "[Hata: Gemini API anahtarı veya motoru hazır değil!]",
                    "vocabulary": []
                }

            result = self._gemini_engine.translate(text)
            return {
                "engine": "gemini",
                "translated_text": result.get("translated_text", ""),
                "vocabulary": result.get("vocabulary", [])
            }