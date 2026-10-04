# OyunÇevirmen (GameLingo)

Oyun içi diyalogları ve altyazıları gerçek zamanlı yakalayan, yapay zeka destekli İngilizce -> Türkçe ekran çevirmeni ve kelime öğrenme asistanı.

MORT gibi mevcut araçların karmaşık arayüzü, zayıf OCR performansı ve tek pencere kısıtlamasına alternatif olarak; özellikle Wuthering Waves gibi hareketli, partiküllü arka planlara sahip oyunlarda yüksek doğrulukla çalışmak üzere tasarlanmıştır.

---

## Öne Çıkan Özellikler

- **Gelişmiş Görüntü Ön İşleme (OpenCV):**
  - Bicubic 2x upscaling ile düşük çözünürlüklü altyazıların netleştirilmesi.
  - CLAHE (Kontrast Sınırlı Adaptif Histogram Eşitleme) ve Otsu ikili eşikleme ile dinamik oyun arka planlarından arındırma.
  - Morfolojik parazit temizleme.
- **Hafif ve Güçlü Yerel OCR (RapidOCR):**
  - ONNX Runtime tabanlı derin öğrenme modeli ile stilize ve gölgeli oyun fontlarında sıfıra yakın gecikme ve yüksek doğruluk.
- **Bağımsız Çoklu Katmanlar (Multi-Overlay):**
  - Ekranda birden fazla bağımsız alan seçimi ve her alana özel şeffaf çeviri balonları.
- **Tıklanabilir Kelimeler ve Sözlük Havuzu:**
  - Çeviri penceresinde bilinmeyen kelimelere tıklandığında cümlenin bağlamıyla birlikte SQLite veritabanına kaydetme.
- **Oyun Sonrası Tekrar Modu (SRS):**
  - Kaydedilen kelimelerle aralıklı tekrar algoritması (SM-2) destekli mini alıştırmalar.
- **Yapay Zeka Destekli Doğal Çeviri:**
  - Gemini 1.5 Flash entegrasyonu ile JSON tabanlı yapılandırılmış ve hızlı çeviri.

---

## Mimari ve Teknoloji Yığını

- **Ekran Yakalama:** mss
- **Görüntü İşleme:** OpenCV, NumPy
- **OCR Motoru:** RapidOCR (ONNX Runtime)
- **Yapay Zeka:** Google Gemini 1.5 Flash
- **Arayüz (GUI):** PyQt6
- **Veritabanı:** SQLite

---

## Kurulum ve Çalıştırma

1. Depoyu klonlayın:
   git clone https://github.com/Natronabi/GameLingoTranslator.git
   cd GameLingoTranslator

2. Sanal ortamı aktif edin:
   .\venv\Scripts\Activate.ps1

3. Bağımlılıkları yükleyin:
   pip install -r requirements.txt

4. Çekirdek testi çalıştırın:
   python test_core.py