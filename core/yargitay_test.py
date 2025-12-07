# yargitay_test.py (GÜNCELLENMİŞ KOD)

import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Yargıtay Hukuk Genel Kurulu Kararları Arama Sayfası
YARGITAY_URL = "https://www.google.com"
try:
    # 1. WebDriver'ı Otomatik Başlatma (Selenium Manager kullanılarak)
    # Artık driver.exe dosyasına ihtiyaç duyulmayacak.
    driver = webdriver.Chrome() 
    
    # 2. Sayfayı Açma
    print(f"-> Yargıtay sayfası açılıyor: {YARGITAY_URL}")
    driver.get(YARGITAY_URL)
    
    # Sayfanın yüklenmesi için bekleme 
    time.sleep(5) 
    
    # 3. Sayfa Başlığını ve URL'yi Yazdırma (Başarılı Bağlantı Kontrolü)
    print(f"-> BAŞARI: Başlık: {driver.title}")
    print(f"-> Güncel URL: {driver.current_url}")
    
    # 4. Ekran Görüntüsü Alma (Kontrol için)
    driver.save_screenshot("yargitay_giris.png")
    print("-> Ekran görüntüsü alındı: yargitay_giris.png")
    
    # 5. Kodu Kapama
    driver.quit()
    print("-> İşlem Tamamlandı.")

except Exception as e:
    print(f"\nBeklenmeyen bir hata oluştu: {e}")
    print("\nLütfen Chrome tarayıcınızın güncel olduğundan emin olun.")