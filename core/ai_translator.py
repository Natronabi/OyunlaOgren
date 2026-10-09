import os
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Gemini SDK
from google import genai
from google.genai import types

# NVIDIA / OpenAI-Compatible SDK
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Model Tanımları & Rehber
MODEL_DESCRIPTIONS = {
    # Gemini Modelleri
    "gemini-2.5-flash": {
        "provider": "gemini",
        "tag": "⚡ Google Gemini En Hızlı",
        "desc": "Google'ın ultra düşük gecikmeli, akıcı oyun çeviri modeli."
    },
    "gemini-1.5-flash": {
        "provider": "gemini",
        "tag": "⚡ Google Gemini Hızlı & Stabil",
        "desc": "Aksiyon anlarındaki hızlı altyazılar için ideal."
    },
    "gemini-2.5-pro": {
        "provider": "gemini",
        "tag": "🧠 Google Gemini Edebi & Lore",
        "desc": "Karmaşık RPG hikayeleri ve diyaloglar için en yüksek zeka seviyesi."
    },
    
    # NVIDIA NIM Modelleri (build.nvidia.com)
    "meta/llama-3.1-70b-instruct": {
        "provider": "nvidia",
        "tag": "🟢 NVIDIA NIM - Llama 3.1 70B",
        "desc": "NVIDIA sunucularında barındırılan devasa açık kaynak model. Çeviri kalitesi olağanüstü."
    },
    "meta/llama-3.1-8b-instruct": {
        "provider": "nvidia",
        "tag": "⚡ NVIDIA NIM - Llama 3.1 8B",
        "desc": "NVIDIA TensorRT ile hızlandırılmış hafif ve hızlı yerelleştirme modeli."
    },
    "deepseek-ai/deepseek-r1": {
        "provider": "nvidia",
        "tag": "🧠 NVIDIA NIM - DeepSeek R1",
        "desc": "Derin düşünme ve bağlam analizi konusunda uzman yeni nesil akıl yürütme modeli."
    },
    "mistralai/mistral-large-2-instruct": {
        "provider": "nvidia",
        "tag": "🏰 NVIDIA NIM - Mistral Large 2",
        "desc": "Avrupa dilleri ve çok dilli çeviride lider Mistral mimarisi."
    }
}

class GeminiTranslator:
    """Evrensel AI Çevirici (Google Gemini + NVIDIA NIM / OpenAI Uyumlu)"""
    def __init__(self, api_key: str = "", nvidia_key: str = "", model_name: str = "gemini-1.5-flash"):
        self.gemini_key = api_key
        self.nvidia_key = nvidia_key
        self.model_name = model_name
        
        self.gemini_client = None
        self.nvidia_client = None

        if self.gemini_key:
            self.configure_gemini(self.gemini_key)
        if self.nvidia_key:
            self.configure_nvidia(self.nvidia_key)

    def configure(self, gemini_key: str):
        return self.configure_gemini(gemini_key)

    def configure_gemini(self, key: str):
        self.gemini_key = key
        try:
            self.gemini_client = genai.Client(api_key=key)
            return True, "Gemini Hazır"
        except Exception as e:
            self.gemini_client = None
            return False, f"Gemini Hatası: {e}"

    def configure_nvidia(self, key: str):
        self.nvidia_key = key
        if not OpenAI:
            return False, "openai paketi yüklü değil (pip install openai)"
        try:
            self.nvidia_client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=key
            )
            return True, "NVIDIA NIM Hazır"
        except Exception as e:
            self.nvidia_client = None
            return False, f"NVIDIA Hatası: {e}"

    def list_available_models(self):
        """Aktif anahtarlara göre erişilebilir tüm modelleri birleştirir."""
        available = []

        # 1. Gemini Modelleri
        if self.gemini_client:
            try:
                for m in self.gemini_client.models.list():
                    m_name = m.name.replace("models/", "") if hasattr(m, "name") else str(m)
                    if "gemini" in m_name.lower() and "embedding" not in m_name.lower():
                        available.append(m_name)
            except Exception:
                available.extend(["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro"])
        else:
            available.extend(["gemini-2.5-flash", "gemini-1.5-flash"])

        # 2. NVIDIA NIM Modelleri
        nvidia_defaults = [
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
            "deepseek-ai/deepseek-r1",
            "mistralai/mistral-large-2-instruct"
        ]
        available.extend(nvidia_defaults)

        return sorted(list(set(available)))

    def translate_single(self, text: str, model_name: str = None) -> dict:
        target_model = model_name or self.model_name
        info = MODEL_DESCRIPTIONS.get(target_model, {})
        provider = info.get("provider", "gemini" if "gemini" in target_model else "nvidia")

        prompt = f"""
Sen profesyonel bir oyun yerelleştirme uzmanı ve dil eğitmenisin.
Aşağıdaki İngilizce oyun metnini Türkçeye doğal, oyunun atmosferine uygun şekilde çevir.
Metindeki en kritik B1-C2 seviye kelimeleri çıkar.

Cevabını SADECE geçerli bir JSON formatında döndür:
{{
  "translated_text": "Türkçe çeviri",
  "vocabulary": [
    {{"word": "kelime", "meaning": "anlamı", "level": "B2"}}
  ]
}}

İngilizce Metin:
{text}
"""
        start_time = time.time()

        # NVIDIA NIM ÜZERİNDEN ÇAĞRI
        if provider == "nvidia":
            if not self.nvidia_client:
                return {
                    "model": target_model,
                    "translated_text": "[Hata: NVIDIA API Key girilmedi]",
                    "vocabulary": [],
                    "elapsed": 0.0,
                    "success": False
                }
            try:
                response = self.nvidia_client.chat.completions.create(
                    model=target_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    top_p=0.7,
                    max_tokens=1024
                )
                elapsed = round(time.time() - start_time, 2)
                raw_text = response.choices[0].message.content.strip()
                return self._parse_json_result(target_model, raw_text, elapsed)
            except Exception as e:
                elapsed = round(time.time() - start_time, 2)
                return {"model": target_model, "translated_text": f"NVIDIA Hatası: {e}", "vocabulary": [], "elapsed": elapsed, "success": False}

        # GEMINI ÜZERİNDEN ÇAĞRI
        else:
            if not self.gemini_client:
                return {
                    "model": target_model,
                    "translated_text": "[Hata: Gemini API Key girilmedi]",
                    "vocabulary": [],
                    "elapsed": 0.0,
                    "success": False
                }
            try:
                response = self.gemini_client.models.generate_content(
                    model=target_model,
                    contents=prompt
                )
                elapsed = round(time.time() - start_time, 2)
                raw_text = response.text.strip()
                return self._parse_json_result(target_model, raw_text, elapsed)
            except Exception as e:
                elapsed = round(time.time() - start_time, 2)
                err_text = self._format_error_message(e, "Gemini")
                return {"model": target_model, "translated_text": err_text, "vocabulary": [], "elapsed": elapsed, "success": False}

    # === TAM BURAYA EKLİYORSUN (Sınıfın içine, 4 boşluk girintili) ===
    def _format_error_message(self, error: Exception, provider: str) -> str:
        err_str = str(error).lower()
        if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
            return (
                "⚠️ [KOTA SINIRINA ULAŞILDI (429)]\n"
                "Ücretsiz API istek limitiniz geçici olarak doldu. "
                "Lütfen 1-2 dakika bekleyip tekrar deneyin veya Flash / 8B gibi hafif modellere geçin."
            )
        elif "api_key" in err_str or "unauthenticated" in err_str or "invalid" in err_str:
            return f"❌ [GEÇERSİZ API KEY] {provider.upper()} API anahtarınız hatalı veya süresi dolmuş."
        return f"❌ [{provider.upper()} HATASI]: {error}"
        

    def _parse_json_result(self, model: str, raw_text: str, elapsed: float) -> dict:
        try:
            clean = raw_text
            if clean.startswith("```json"): clean = clean[7:]
            elif clean.startswith("```"): clean = clean[3:]
            if clean.endswith("```"): clean = clean[:-3]
            parsed = json.loads(clean.strip())
            return {
                "model": model,
                "translated_text": parsed.get("translated_text", ""),
                "vocabulary": parsed.get("vocabulary", []),
                "elapsed": elapsed,
                "success": True
            }
        except Exception:
            return {
                "model": model,
                "translated_text": raw_text,
                "vocabulary": [],
                "elapsed": elapsed,
                "success": True
            }

    def benchmark_models(self, text: str, selected_models: list) -> list:
        results = []
        with ThreadPoolExecutor(max_workers=min(len(selected_models), 12)) as executor:
            futures = [executor.submit(self.translate_single, text, m) for m in selected_models]
            for f in futures:
                results.append(f.result())
        return results

# Geriye dönük uyumluluk alias
AITranslator = GeminiTranslator