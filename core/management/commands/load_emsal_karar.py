# core/management/commands/load_emsal_karar.py (GÜNCELLENMİŞ VERSİYON - CSV OKUYUCU)

import re
import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from core.models import HukukKategori, EmsalKarar

class Command(BaseCommand):
    help = 'CSV dosyasından Emsal Karar okur, KVKK uyumlu hale getirir ve veritabanına kaydeder.'
    
    # KVKK Regex Tanımları
    patterns = {
        'isim_soyisim': re.compile(r'\b[A-ZÇĞIİÖŞÜ]{2,}\s[A-ZÇĞIİÖŞÜ]{2,}\b', re.UNICODE), 
        'tc_kimlik': re.compile(r'\b\d{11}\b'), 
        'adres_bilgisi': re.compile(r'(adresi|ikametgahı|adresli)\s[^\.]+\.', re.IGNORECASE),
    }

    def anonymize_text(self, text):
        """Metindeki hassas kişisel verileri anonimleştirir (KVKK Uyumlu)."""
        if not text or not isinstance(text, str):
            return ""

        text = self.patterns['tc_kimlik'].sub('***TCKN***', text)
        text = self.patterns['adres_bilgisi'].sub('***ADRES_GİZLİ***', text)
        
        def replace_name(match):
            return '***KİŞİ_GİZLİ***'
        
        text = self.patterns['isim_soyisim'].sub(replace_name, text)
        return text

    def handle(self, *args, **options):
        DOSYA_ADI = 'emsal_kararlar.csv' 
        
        if not os.path.exists(DOSYA_ADI):
            raise CommandError(f"HATA: '{DOSYA_ADI}' dosyası bulunamadı. Lütfen CSV dosyasını ana klasöre yerleştirin.")

        self.stdout.write(self.style.SUCCESS(f'--- {DOSYA_ADI} Yükleme Başlatıldı (CSV & KVKK Filtreli) ---'))

        try:
            # CSV dosyasını okuma (pandas kullanarak)
            df = pd.read_csv(DOSYA_ADI, encoding='utf-8')
        except Exception as e:
            raise CommandError(f"CSV okuma hatası: {e}. Dosya formatını kontrol edin.")

        kategori, _ = HukukKategori.objects.get_or_create(
            isim="Yargıtay Emsal Kararları",
            defaults={'slug': 'emsal-karar'}
        )
        
        kaydedilen_sayi = 0
        
        # DataFrame üzerindeki her satırı işleme
        for index, row in df.iterrows():
            try:
                # CSV'deki kararın tam metnini içeren sütun adı (Bunu kendi CSV dosyanıza göre ayarlayın)
                KARAR_SUTUN_ADI = 'tam_metin' 
                karar_metni = row.get(KARAR_SUTUN_ADI)
                
                if pd.isna(karar_metni):
                    continue

                anonim_metin = self.anonymize_text(karar_metni)
                
                # Diğer bilgileri CSV'den çekme (Eğer varsa)
                daire = row.get('daire', 'Bilinmiyor')
                esas_no = row.get('esas_no', f"CSV_ERR/{index}")
                karar_no = row.get('karar_no', f"KARAR-{index}")

                EmsalKarar.objects.update_or_create(
                    esas_no=esas_no,
                    defaults={
                        'kategori': kategori,
                        'daire': daire,
                        'karar_no': karar_no,
                        'tam_metin': anonim_metin,
                        'ozet': anonim_metin[:500].strip() + '...',
                    }
                )
                kaydedilen_sayi += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Satır {index} işlenirken hata: {e}"))
                
        self.stdout.write(self.style.SUCCESS('=' * 40))
        self.stdout.write(self.style.SUCCESS(f"KVKK Filtreli Yükleme Başarılı. Toplam {kaydedilen_sayi} karar kaydedildi."))
        self.stdout.write(self.style.SUCCESS('=' * 40))