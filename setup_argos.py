import sys
import argostranslate.package
import argostranslate.translate

print("[1/4] Paket dizini güncelleniyor (İnternet bağlantısı gerekiyor)...")
try:
    argostranslate.package.update_package_index()
except Exception as e:
    print(f"HATA: Paket dizini alınamadı: {e}")
    sys.exit(1)

print("[2/4] Mevcut diller taranıyor...")
available_packages = argostranslate.package.get_available_packages()

package_to_install = None
for pkg in available_packages:
    if pkg.from_code == "en" and pkg.to_code == "tr":
        package_to_install = pkg
        break

if not package_to_install:
    print("HATA: İngilizce -> Türkçe (en->tr) paketi listede bulunamadı!")
    sys.exit(1)

print("[3/4] en -> tr dil paketi indiriliyor (Yaklaşık 50-60 MB)...")
download_path = package_to_install.download()

print("[4/4] Paket sisteme kuruluyor...")
argostranslate.package.install_from_path(download_path)

print("\n--- TEST EDİLİYOR ---")
try:
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(filter(lambda x: x.code == "en", installed_languages))
    to_lang = next(filter(lambda x: x.code == "tr", installed_languages))
    translation = from_lang.get_translation(to_lang)
    sample_text = "Press any key to continue"
    print(f"Orijinal: {sample_text}")
    print(f"Çeviri  : {translation.translate(sample_text)}")
    print("\n✓ BAŞARILI: Yerel çeviri motoru sorunsuz kuruldu ve çalışıyor!")
except Exception as e:
    print(f"Test sırasında hata: {e}")