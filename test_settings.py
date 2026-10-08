import sys
from PyQt6.QtWidgets import QApplication
from ui.overlay import TranslationOverlay
from ui.settings_dialog import SettingsDialog
from core.config_manager import ConfigManager

if __name__ == "__main__":
    app = QApplication(sys.argv)

    cfg = ConfigManager.load_config()

    overlay = TranslationOverlay(config=cfg)
    overlay.move(400, 100)
    overlay.show()
    overlay.update_content({
        "engine": "gemini",
        "original_text": "What do these whispers echoing in the dark ruins mean?",
        "translated_text": "Karanlık harabelerde yankılanan bu fısıltılar ne anlama geliyor?",
        "vocabulary": [
            {"word": "whisper", "meaning": "fısıltı", "level": "B1"},
            {"word": "ruins", "meaning": "harabeler", "level": "B2"}
        ]
    })

    dialog = SettingsDialog(current_config=cfg)
    dialog.move(400, 280)
    dialog.settings_changed.connect(overlay.update_settings)
    dialog.show()

    sys.exit(app.exec())