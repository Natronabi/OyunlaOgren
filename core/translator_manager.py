import os
from typing import Dict, Any

try:
    from core.ai_translator import GeminiTranslator as AITranslator
except ImportError:
    try:
        from core.ai_translator import AITranslator
    except ImportError:
        AITranslator = None


class TranslatorManager:
    """
    Hem çevrimdışı (Argos) hem bulut (Gemini) çeviri motorlarını
    tek bir merkezden yöneten hibrit çeviri sınıfı.
    """
    def __init__(self, default_engine: str = "local"):
        self.active_engine = default_engine
        self._gemini_engine = None
        self._argos_translation = None
        self._argos_ready = False

        if self.active_engine == "local":
            self._init_local()
        elif self.active_engine == "gemini":
            self._init_gemini()

    def _init_local(self):
        """Yerel ArgosTranslate motorunu ve kurulu en->tr dil paketini bağlar."""
        try:
            import argostranslate.translate
            installed_languages = argostranslate.translate.get_installed_languages()
            
            from_lang = next(filter(lambda x: x.code == "en", installed_languages), None)
            to_lang = next(filter(lambda x: x.code == "tr", installed_languages), None)

            if from_lang and to_lang:
                self._argos_translation = from_lang.get_translation(to_lang)
                self._argos_ready = True
                print("[TranslatorManager] ✓ ArgosTranslate (en -> tr) çeviri motoru hazır.")
            else:
                print("[TranslatorManager] HATA: en -> tr dil paketi kurulu görünmüyor!")
                self._argos_ready = False
        except Exception as e:
            print(f"[TranslatorManager] HATA: ArgosTranslate yüklenemedi: {e}")
            self._argos_ready = False

    def _init_gemini(self):
        """Gemini motorunu dinamik olarak yükler."""
        if self._gemini_engine is None and AITranslator is not None:
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

    def translate_text_only(self, text: str) -> str:
        """Doğrudan Türkçe metin string'i döndürür."""
        if not text or not text.strip():
            return ""

        if not self._argos_ready or self._argos_translation is None:
            self._init_local()

        if self._argos_translation:
            try:
                return self._argos_translation.translate(text.strip())
            except Exception as e:
                print(f"[TranslatorManager] Çeviri hatası: {e}")
                return f"[Çeviri hatası: {e}]"
        return "[Yerel çeviri paketi hazır değil]"

    def translate(self, text: str) -> Dict[str, Any]:
        """Standart sözlük çıktısı."""
        if not text or not text.strip():
            return {
                "engine": self.active_engine,
                "translated_text": "",
                "vocabulary": []
            }

        # 1. YEREL ÇEVİRİ
        if self.active_engine == "local":
            translated = self.translate_text_only(text)
            return {
                "engine": "local",
                "translated_text": translated,
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