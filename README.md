# GameLingo Translator 🎮📖

GameLingo Translator, oyun içi altyazıları ve metinleri gerçek zamanlı olarak yakalayan, yapay zeka destekli (Gemini) İngilizce → Türkçe ekran çevirmeni ve kelime öğrenme asistanıdır.

## Temel Özellikler (Planlanan)
- **Oyun Dostu OCR:** Wuthering Waves gibi hareketli ve partiküllü arka planlara özel görüntü ön işleme (OpenCV) ve hızlı yerel OCR (RapidOCR).
- **Bağımsız Çoklu Katmanlar (Multi-Overlay):** Farklı ekran alanları (diyalog, görev listesi vb.) için bağımsız şeffaf çeviri balonları.
- **Tıklanabilir Kelimeler:** Çevirideki bilmediğin kelimelere tıklayarak doğrudan kişisel sözlüğüne kaydetme.
- **SRS & Alıştırma Modu:** Oyunu kapattıktan sonra kaydedilen kelimelerle aralıklı tekrar (SM-2) testleri çözme.
- **Düşük Gecikme:** `gemini-1.5-flash` entegrasyonu ile saniyenin altında hızlı ve bağlama uygun çeviri.

## Geliştirme Ortamı
```bash
python -m venv venv
source venv/bin/activate  # Windows için: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py