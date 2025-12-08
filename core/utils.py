# utils.py (Yeni dosya oluştur)
import requests
from bs4 import BeautifulSoup # Veri çekmek için
from .models import KanunMaddesi, HukukKategori, SistemBildirimi, VeriGuncellemeLog

def mevzuat_guncelleme_kontrolu():
    """
    Bu fonksiyon günde 1 kez çalışır (Celery veya Cron ile).
    Resmi Gazete veya Mevzuat.gov.tr'yi kontrol eder.
    """
    print("🔄 Mevzuat taraması başlıyor...")
    
    # ÖRNEK: Resmi Gazete son başlıkları çekelim (Simülasyon)
    url = "https://www.resmigazete.gov.tr/"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Burada normalde BeautifulSoup ile veriyi ayrıştırırız
            # Şimdilik simüle ediyoruz:
            yeni_veri_bulundu = True 
            
            if yeni_veri_bulundu:
                # 1. Admin'e Bildirim Gönder
                SistemBildirimi.objects.create(
                    baslik="📢 Yeni Mevzuat Yayındı!",
                    mesaj="Resmi Gazete'de bugün yeni kararlar yayınlandı. Lütfen veri tabanını güncelleyiniz veya otomatik işlem onayı veriniz.",
                    seviye="info"
                )
                
                # 2. Log Kaydı
                VeriGuncellemeLog.objects.create(
                    kategori=HukukKategori.objects.first(), # Örnek
                    basarili_mi=True,
                    eklenen_veri_sayisi=5
                )
        else:
            raise Exception("Resmi Gazete sitesine ulaşılamadı.")

    except Exception as e:
        # HATA DURUMUNDA SANA BİLDİRİM
        SistemBildirimi.objects.create(
            baslik="❌ Güncelleme Hatası",
            mesaj=f"Veri çekmeye çalışırken hata oluştu: {str(e)}",
            seviye="danger"
        )
        print(f"Hata: {e}")