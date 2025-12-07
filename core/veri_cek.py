import os
import django
import requests
from bs4 import BeautifulSoup

# Django ayarlarını bu scriptte kullanabilmek için:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HukukProje.settings') # Proje adın farklıysa düzelt
django.setup()

from core.models import HukukKategori, KanunMaddesi # 'panel' senin app adın olmalı

def tck_cek():
    # Örnek olarak Türk Ceza Kanunu Linki (Mevzuat.gov genelde doc verir ama html versiyonu bulup parsellemek daha kolaydır, burada örnek bir mantık kuruyorum)
    # Not: Gerçek mevzuat.gov.tr yapısı karmaşıktır, genelde oradan metni kopyalayıp bir txt dosyasına yapıştırıp oradan okutmak daha temizdir.
    # Ancak biz requests ile deneyelim.
    
    url = "https://www.mevzuat.gov.tr/MevzuatMetin/1.5.5237.pdf" # PDF zor işlenir.
    # Bu yüzden strateji değişikliği: HTML kaynaklardan çekmek daha mantıklı.
    # Örn: Tbmm veya resmigazete linkleri.
    
    print("Mevzuat çekme işlemi karmaşık olduğu için önce Kategori oluşturalım...")
    
    # 1. Kategori Oluştur
    kategori, created = HukukKategori.objects.get_or_create(
        isim="Ceza Hukuku",
        defaults={'slug': 'ceza-hukuku'}
    )
    
    # SENARYO: Elimizde temizlenmiş bir metin dosyası olduğunu varsayalım veya
    # basit bir web sayfasından çekelim.
    
    print(f"{kategori.isim} kategorisi hazır.")
    print("Şimdilik manuel örnek veri ekliyorum (Otomasyon için kaynak site yapısı incelenmeli).")

    # Örnek Veri Girişi
    KanunMaddesi.objects.get_or_create(
        kategori=kategori,
        kanun_no="5237",
        kanun_adi="Türk Ceza Kanunu",
        madde_no="Madde 1",
        icerik="Ceza Kanununun amacı; kişi hak ve özgürlüklerini, kamu düzen ve güvenliğini, hukuk devletini, kamu sağlığını ve çevreyi, toplum barışını korumak, suç işlenmesini önlemektir."
    )
    
    print("Örnek madde eklendi.")

if __name__ == "__main__":
    tck_cek()