import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import DavaAnalizi, HukukKategori  # GÜNCELLENDİ: Yeni model isimleri

class Command(BaseCommand):
    help = 'TURA sisteminden gelen JSON verilerini veritabanına senkronize eder.'

    def handle(self, *args, **options):
        # TURA klasörünün yolunu bulmaya çalışalım
        base_dir = settings.BASE_DIR
        
        # Varsayım: TURA klasörü proje klasörünün bir üstünde veya yanındadır.
        # Kendi bilgisayarınızdaki tam yolu buraya yazmanız en garantisidir.
        # Örn: folder_path = r"C:\Users\vatan\Desktop\HukukAI\TURA\islenmis_veriler"
        
        # Otomatik bulmayı deneyelim:
        folder_path = os.path.join(base_dir, '..', '..', 'TURA', 'islenmis_veriler')
        
        # Eğer yukarıdaki yol çalışmazsa, kullanıcıya not düşelim:
        if not os.path.exists(folder_path):
             # Alternatif yol (proje klasörünün hemen içinde olabilir)
            folder_path = os.path.join(base_dir, '..', 'TURA', 'islenmis_veriler')
            
        if not os.path.exists(folder_path):
            self.stdout.write(self.style.ERROR(f"KLASÖR BULUNAMADI: {folder_path}"))
            self.stdout.write(self.style.WARNING("Lütfen sync_tura.py dosyasını açıp 'folder_path' değişkenine TURA/islenmis_veriler klasörünün tam yolunu yapıştırın."))
            return

        # "Kira Hukuku" Kategorisini (Eski LegalBlock) seçelim veya oluşturalım
        kira_kategori, created = HukukKategori.objects.get_or_create(
            slug='kira-hukuku',
            defaults={
                'isim': 'Kira Hukuku', 
                'aciklama': 'Kira tespit, tahliye ve uyarlama davaları analizleri.',
                'ikon': '🏠',
                'aktif_mi': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Yeni Kategori Oluşturuldu: Kira Hukuku"))

        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        self.stdout.write(f"Toplam {len(files)} JSON dosyası taranıyor...")

        added_count = 0
        updated_count = 0

        for filename in files:
            file_path = os.path.join(folder_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # JSON parçalama
                    kimlik = data.get('kimlik', {})
                    analiz = data.get('analiz', {})
                    
                    # Başlık oluşturma (Daire + Esas No)
                    daire = kimlik.get('daire', 'Belirsiz Daire')
                    esas = kimlik.get('esas_no', '')
                    karar = kimlik.get('karar_no', '')
                    baslik = f"{daire} - E:{esas} K:{karar}"

                    # update_or_create: Varsa güncelle, yoksa yarat
                    # Yeni modelimiz DavaAnalizi'ni kullanıyoruz
                    obj, created = DavaAnalizi.objects.update_or_create(
                        dosya_adi=data.get('dosya_adi', filename),
                        defaults={
                            'kategori': kira_kategori,
                            'daire': daire,
                            'esas_no': esas,
                            'karar_no': karar,
                            'karar_tarihi': kimlik.get('tarih', ''),
                            
                            'baslik': baslik, # Yeni modelde başlık alanı zorunlu olabilir
                            
                            'konu_etiketleri': analiz.get('konu_etiketleri', []),
                            'hukuki_ilke': analiz.get('hukuki_ilke', ''),
                            'ozet_hikaye': analiz.get('ozet_hikaye', ''),
                            'kritik_uyari': analiz.get('kritik_uyari', ''),
                            'hukum_sonucu': analiz.get('hukum_sonucu', ''),
                        }
                    )
                    
                    if created:
                        added_count += 1
                    else:
                        updated_count += 1
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Hata ({filename}): {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ İŞLEM TAMAMLANDI!"))
        self.stdout.write(f"Eklenen: {added_count}")
        self.stdout.write(f"Güncellenen: {updated_count}")