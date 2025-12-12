import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
KAYIT_KLASORU = "ham_kararlar"
if not os.path.exists(KAYIT_KLASORU):
    os.makedirs(KAYIT_KLASORU)

# ==============================================================================
# 2. TARAYICIYI BAŞLAT
# ==============================================================================
print("🚀 Tarayıcı başlatılıyor...")
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.maximize_window()

driver.get("https://karararama.yargitay.gov.tr/")

print("\n" + "="*50)
print("🛑 BEKLENİYOR: Lütfen aramayı yapın ve sonuçlar ekrana gelsin.")
print("Sonuçlar gelince buraya dönüp ENTER'a basın.")
print("="*50 + "\n")

input("👉 Hazır mı? Enter'a bas...")

# ==============================================================================
# 3. AKILLI VERİ ÇEKME (Mükerrer Kontrollü)
# ==============================================================================
print("🤖 Robot devreye girdi. Veriler çekiliyor...")

sayfa_sayisi = 1
toplam_atlanan = 0
toplam_indirilen = 0

while True:
    try:
        # Tablodaki satırları bul
        satirlar = driver.find_elements(By.CSS_SELECTOR, "#detayAramaSonuclar tbody tr")
        
        if not satirlar:
            print("❌ Tabloda satır bulunamadı!")
            break

        print(f"\n📄 Sayfa {sayfa_sayisi} taranıyor... ({len(satirlar)} karar var)")

        for i in range(len(satirlar)):
            try:
                # DOM bayatlamasın diye elementleri yeniden buluyoruz
                guncel_satirlar = driver.find_elements(By.CSS_SELECTOR, "#detayAramaSonuclar tbody tr")
                aktif_satir = guncel_satirlar[i]

                # --- BENZERSİZ KİMLİK OLUŞTURMA ---
                sutunlar = aktif_satir.find_elements(By.TAG_NAME, "td")
                
                # Tablo Yapısı: [0]Sıra [1]Daire [2]Esas [3]Karar [4]Tarih
                if len(sutunlar) > 4:
                    daire = sutunlar[1].text.replace(" ", "").replace(".", "") # "3.Hukuk" -> "3Hukuk"
                    esas = sutunlar[2].text.replace("/", "-")   # "2024/123" -> "2024-123"
                    karar = sutunlar[3].text.replace("/", "-")  # "2024/99" -> "2024-99"
                    
                    # Benzersiz Dosya Adı: "3Hukuk_E2024-123_K2024-99.txt"
                    dosya_adi = f"{daire}_E{esas}_K{karar}.txt"
                else:
                    # Okuyamazsa yedek isim
                    dosya_adi = f"Sayfa{sayfa_sayisi}_Sira{i+1}.txt"

                hedef_yol = os.path.join(KAYIT_KLASORU, dosya_adi)

                # --- KONTROL ANI: BU DOSYA VAR MI? ---
                if os.path.exists(hedef_yol):
                    print(f"   ⏩ ZATEN VAR, GEÇİLDİ: {dosya_adi}")
                    toplam_atlanan += 1
                    continue # Tıklamadan bir sonraki satıra geç

                # --- YOKSA İNDİR ---
                
                # 1. Tıkla
                driver.execute_script("arguments[0].click();", aktif_satir)
                time.sleep(4) # Yükleme beklemesi
                
                # 2. Metni Al
                panel_metni = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".card-scroll"))
                ).text

                if len(panel_metni) < 50:
                    print(f"   ⚠️ İçerik boş, atlandı: {dosya_adi}")
                    continue

                # 3. Kaydet
                with open(hedef_yol, "w", encoding="utf-8") as f:
                    f.write(panel_metni)
                
                print(f"   ✅ İNDİRİLDİ: {dosya_adi}")
                toplam_indirilen += 1

            except Exception as e:
                print(f"   ⚠️ Satır hatası: {e}")

        # --- SONRAKİ SAYFA ---
        try:
            sonraki_buton = driver.find_element(By.CSS_SELECTOR, ".paginate_button.next")
            
            if "disabled" in sonraki_buton.get_attribute("class"):
                print("🏁 Son sayfaya gelindi.")
                break
            
            driver.execute_script("arguments[0].click();", sonraki_buton)
            sayfa_sayisi += 1
            print("⏳ Sonraki sayfa yükleniyor...")
            time.sleep(4) 

        except:
            print("🏁 Başka sayfa yok.")
            break

    except Exception as e:
        print(f"❌ Genel Hata: {e}")
        break

driver.quit()
print("\n" + "="*50)
print(f"🎉 İŞLEM BİTTİ!")
print(f"📥 Yeni İndirilen: {toplam_indirilen}")
print(f"⏭️  Daha Önce İndirilip Atlanan: {toplam_atlanan}")
print("="*50)