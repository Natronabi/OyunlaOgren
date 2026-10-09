import json
import os

DEFAULT_CONFIG = {
    # Görünüm
    "enable_bg": True,
    "bg_color": "18, 18, 24",
    "bg_opacity": 0.90,
    "text_color": "#ffffff",
    "text_opacity": 1.0,
    "font_size": 13,
    "font_family": "Segoe UI",
    "border_radius": 8,
    "overlay_width": 420,
    "overlay_height": 130,
    "show_original_text": False,  # Varsayılan olarak kapalı

    # Motor ve AI
    "default_engine": "local",
    "ocr_interval": 0.5,
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash",

    # Kısayollar
    "hotkey_select": "F9",
    "hotkey_toggle": "F10",
    "hotkey_overlay": "F11",
    "hotkey_save_interactive": "F7",

    # Kelime Kartları
    "show_vocab": True,
    "show_vocab_level": True,
    "vocab_max_count": 3,
    "layout_mode": "bottom_words"
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