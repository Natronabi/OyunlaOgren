import sys
from PyQt6.QtWidgets import QApplication
from ui.overlay import TranslationOverlay

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = TranslationOverlay()
    overlay.show()

    # RPG / Hikaye ağırlıklı upuzun paragraf ve 5 kelimelik analiz
    heavy_rpg_data = {
        "engine": "gemini",
        "translated_text": (
            "Kadim harabelerin derinliklerinde yankılanan bu fısıltılar, yalnızca mühürlenmiş "
            "olan kadim muhafızın uyanışını değil; aynı zamanda krallığın sınırlarını koruyan "
            "tüm eterik kalkanların geri dönülemez bir biçimde parçalanmaya başladığını haber veriyor. "
            "Sığınak tamamen çökmeden önce geçidi terk etmek zorundayız!"
        ),
        "vocabulary": [
            {"word": "whisper", "meaning": "fısıltı", "level": "B1"},
            {"word": "dormant", "meaning": "uykuda olan, hareketsiz", "level": "B2"},
            {"word": "inexorably", "meaning": "kaçınılmaz bir biçimde", "level": "C1"},
            {"word": "etheric", "meaning": "eterik, ruhani/enerjisel", "level": "C2"},
            {"word": "sanctuary", "meaning": "sığınak, kutsal alan", "level": "B2"}
        ]
    }

    overlay.update_content(heavy_rpg_data)

    sys.exit(app.exec())