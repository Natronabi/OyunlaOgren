import time
import json
from core.ai_translator import AITranslator

def run_test(model_name: str):
    print(f"\n==============================")
    print(f"Test Edilen Model: {model_name}")
    print(f"==============================")
    
    translator = AITranslator(model_name=model_name)
    sample_dialogue = "The lament has reshaped the resonance frequencies of this domain. Brace yourselves, an anomaly is approaching!"

    # 1. İstek (Bağlantı kurma + Isınma)
    t0 = time.time()
    translator.translate(sample_dialogue)
    warmup_time = round((time.time() - t0) * 1000, 2)
    print(f"1. İstek (Bağlantı Kurulumu): {warmup_time} ms")

    # 2. İstek (Asıl Çalışma Gecikmesi)
    t1 = time.time()
    res = translator.translate(sample_dialogue)
    hot_time = round((time.time() - t1) * 1000, 2)
    print(f"2. İstek (Saf API Hızı): {hot_time} ms")

    print("\nÖrnek Çıktı:")
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # Sırayla test etmek istediğin modeli buraya yaz:
    candidate = "models/gemini-flash-latest"
    run_test(candidate)