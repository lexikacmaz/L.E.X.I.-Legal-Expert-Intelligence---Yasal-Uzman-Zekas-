# core/management/commands/load_tck.py

import re
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from core.models import HukukKategori, KanunMaddesi

class Command(BaseCommand):
    help = 'Türk Ceza Kanunu (TCK) metnini doğrudan CDN dosyasından çeker ve kaydeder.'

    def handle(self, *args, **options):
        
        # Sizin bulduğunuz doğrudan CDN linki: Bu, en güvenilir kaynaktır.
        TCK_URL = "https://cdn.tbmm.gov.tr/KKBSPublicFile/D22/Y1/T1/KanunMetni/7221aa18-ab2c-4e93-8281-1185d2711471.html" 
        KANUN_NO = '5237'
        KANUN_ADI = 'Türk Ceza Kanunu (5237 Sayılı)'
        
        self.stdout.write(self.style.SUCCESS('--- TCK Yükleme Başlatıldı (CDN Kaynak) ---'))
        
        # 1. Kategori Kontrolü/Oluşturulması
        kategori, created = HukukKategori.objects.get_or_create(
            isim=KANUN_ADI,
            defaults={'slug': 'tck'}
        )
        self.stdout.write(f"Kategori hazırlandı: {kategori.isim}")
        
        # Siteyi engellememek için User-Agent ekliyoruz
        headers = {'User-Agent': 'Mozilla/5.0'}

        # --- AŞAMA 1: Kanun Metnini Çekme ---
        try:
            response = requests.get(TCK_URL, headers=headers, timeout=15)
            response.raise_for_status() 
            
            # Metin doğrudan bir dosya olduğu için encoding hatasını önlemek amacıyla 'utf-8' kullanıyoruz
            detail_soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            
            # Tüm metin body etiketi içinde yer alacaktır. Hiyerarşi aramak yerine tüm gövdeyi çekiyoruz.
            kanun_metni_elementi = detail_soup.find('body') 
            
            if not kanun_metni_elementi:
                 raise CommandError("Body etiketi bile bulunamadı. Bağlantı problemi olabilir.")
            
            # Script, style ve benzeri gereksiz etiketleri kaldırarak temiz metin alıyoruz
            for element in kanun_metni_elementi(["script", "style", "header", "footer"]):
                element.decompose()
                
            kanun_metni = kanun_metni_elementi.get_text()

        except requests.exceptions.RequestException as e:
            raise CommandError(f"URL çekilirken hata oluştu: {e}")
        
        # --- AŞAMA 2: Metni İşleme ve Kaydetme (REGULAR EXPRESSION) ---
        # Regex, bu sefer daha az HTML gürültüsüyle çalışacak.
        metin = kanun_metni.replace('\n', ' ').replace('\r', ' ').strip()
        
        # TCK metnindeki tüm maddeleri yakalama: (Madde X) kalıbı
        maddeler = re.split(r'(Madde\s\d+\w*)', metin, flags=re.IGNORECASE)
        
        maddeler = [m.strip() for m in maddeler if m and m.strip()]
        
        if len(maddeler) < 100: # TCK 300'den fazla madde içeriyor.
            self.stdout.write(self.style.WARNING(f"UYARI: Çok az madde ({len(maddeler)}) çekildi. Metin bölünememiş olabilir."))
            
        yeni_madde_sayisi = 0
        i = 0
        
        while i < len(maddeler):
            madde_basligi = maddeler[i].strip()
            
            if re.match(r'Madde\s\d+\w*', madde_basligi, re.IGNORECASE):
                madde_no = madde_basligi.replace('Madde', '').replace('MADDE', '').strip()
                
                if i + 1 < len(maddeler):
                    icerik = maddeler[i+1].strip()
                    i += 2
                else:
                    icerik = "İçerik çekilemedi."
                    i += 1

                # Veritabanına kaydetme (Güncelleme varsa günceller, yoksa oluşturur)
                KanunMaddesi.objects.update_or_create(
                    kanun_no=KANUN_NO,
                    madde_no=madde_no,
                    defaults={
                        'kategori': kategori,
                        'kanun_adi': KANUN_ADI,
                        'icerik': icerik,
                    }
                )
                yeni_madde_sayisi += 1
            else:
                i += 1

        self.stdout.write(self.style.SUCCESS('=' * 40))
        self.stdout.write(self.style.SUCCESS(f"YÜKLEME BAŞARILI. Toplam {yeni_madde_sayisi} madde veritabanına kaydedildi."))
        self.stdout.write(self.style.SUCCESS('=' * 40))