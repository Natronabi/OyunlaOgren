import os
import json
import google.generativeai as genai

class AITranslator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY bulunamadı! Lütfen ortam değişkenini ayarlayın.")
        
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3
            },
            system_instruction=(
                "Sen video oyunları için uzman bir yerelleştirme ve dil öğrenme asistanısın. "
                "Sana verilen İngilizce oyun metnini bağlama uygun, doğal ve edebi bir Türkçe ile çevir. "
                "Ayrıca metindeki orta-ileri seviye (B1, B2, C1, C2) anahtar kelimeleri analiz et. "
                "Cevabı MUTLAKA şu JSON şemasında döndür:\n"
                "{\n"
                '  "translated_text": "Doğal Türkçe çeviri",\n'
                '  "vocabulary": [\n'
                '    {"word": "kelimenin kök hali", "meaning": "Türkçe karşılığı", "level": "B2"}\n'
                "  ]\n"
                "}"
            )
        )

    def translate(self, text: str) -> dict:
        if not text or not text.strip():
            return {"translated_text": "", "vocabulary": []}

        try:
            prompt = f"Translate and analyze this game text:\n\n{text}"
            response = self.model.generate_content(prompt)
            data = json.loads(response.text)
            return data
        except Exception as e:
            return {
                "translated_text": f"[Çeviri Hatası: {str(e)}]",
                "vocabulary": []
            }