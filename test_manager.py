import time
import json
from core.translator_manager import TranslatorManager

def test():
    manager = TranslatorManager(default_engine="local")
    dialogue = "The anomaly has breached our containment field. Fall back immediately!"
    
    print(f"Orijinal Metin:\n{dialogue}\n")

    # 1. Test: Yerel Motor (Hız Odaklı)
    print("--- [1] YEREL MOTOR TESTİ ---")
    t0 = time.time()
    local_res = manager.translate(dialogue)
    local_time = round((time.time() - t0) * 1000, 2)
    print(json.dumps(local_res, ensure_ascii=False, indent=2))
    print(f"Yerel Süre: {local_time} ms\n")

    # 2. Test: Motoru Gemini'ye Geçir (Analiz Odaklı)
    print("--- [2] GEMINI MOTOR TESTİ ---")
    manager.set_engine("gemini")
    t1 = time.time()
    gemini_res = manager.translate(dialogue)
    gemini_time = round((time.time() - t1) * 1000, 2)
    print(json.dumps(gemini_res, ensure_ascii=False, indent=2))
    print(f"Gemini Süre: {gemini_time} ms")

if __name__ == "__main__":
    test()