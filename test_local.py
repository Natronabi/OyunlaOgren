import time
import argostranslate.package
import argostranslate.translate

def setup_and_test():
    print("Yerel dil paket dizini taranıyor...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    
    # İngilizce -> Türkçe paketini bul
    package_to_install = next(
        (pkg for pkg in available_packages if pkg.from_code == "en" and pkg.to_code == "tr"),
        None
    )

    if package_to_install:
        print("İngilizce-Türkçe paketi indiriliyor ve kuruluyor (bir kerelik)...")
        download_path = package_to_install.download()
        argostranslate.package.install_from_path(download_path)
        print("Model başarıyla kuruldu!")
    else:
        print("İngilizce -> Türkçe paketi bulunamadı!")
        return

    sample_text = "The lament has reshaped the resonance frequencies of this domain."
    print(f"\nOrijinal Metin:\n{sample_text}\n")

    # 1. Çeviri (Belleğe yükleme / Isınma)
    t0 = time.time()
    argostranslate.translate.translate(sample_text, "en", "tr")
    warmup_time = round((time.time() - t0) * 1000, 2)
    print(f"1. Çalıştırma (Model Yükleme): {warmup_time} ms")

    # 2. Çeviri (Saf Yerel Hız)
    t1 = time.time()
    result = argostranslate.translate.translate(sample_text, "en", "tr")
    local_time = round((time.time() - t1) * 1000, 2)
    
    print(f"2. Çalıştırma (Saf Yerel Hız): {local_time} ms")
    print(f"\nÇeviri Çıktısı: {result}")

if __name__ == "__main__":
    setup_and_test()