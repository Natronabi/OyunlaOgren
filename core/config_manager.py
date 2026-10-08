import json
import os

DEFAULT_CONFIG = {
    "font_family": "Segoe UI",
    "font_size": 13,
    "text_color": "#ffffff",
    "bg_color": "18, 18, 24",
    "bg_opacity": 0.88,
    "border_color": "rgba(255, 255, 255, 0.15)",
    "border_radius": 8,
    "default_engine": "local",
    "ocr_interval": 0.5,
    "favorite_fonts": ["Segoe UI", "Arial", "Consolas"],
    "layout_mode": "bottom_words",
    "show_vocab": True,
    "vocab_max_count": 2,
    "show_vocab_level": True,
    "show_original_text": False  # Orijinal metin görünürlüğü
}

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config() -> dict:
        if not os.path.exists(CONFIG_FILE):
            ConfigManager.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config_data: dict):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager Hatası] Ayarlar kaydedilemedi: {e}")