import os
import re
import pandas as pd
import docx  # docx kütüphanesi
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import HukukKategori, KanunMaddesi, EmsalKarar

class Command(BaseCommand):
    help = 'Kira Hukuku Verilerini (DOCX ve CSV) Yükler'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('--- 🚀 SİSTEM BAŞLATILIYOR: Kira Hukuku Entegrasyonu ---'))

        # 1. KATEGORİ OLUŞTURMA
        kategori, created = HukukKategori.objects.get_or_create(
            slug="kira-hukuku",
            defaults={
                "isim": "Kira Hukuku",
                "ikon": "🏠",
                "aciklama": "Konut ve çatılı işyeri kiraları (TBK 299-356), tahliye, tespit ve uyarlama davaları.",
                "ai_talimati": "Sen uzman bir kira hukuku avukatısın. Cevaplarını sadece Türk Borçlar Kanunu (TBK) ve Yargıtay içtihatlarına dayandır.",
                "aktif_mi": True
            }
        )
        self.stdout.write(f"📂 Kategori Hazır: {kategori.isim}")

        # 2. DOCX DOSYASINDAN KANUNLARI OKUMA (Kritik Bölüm)
        docx_path = os.path.join(settings.BASE_DIR, 'kira.docx')
        
        if os.path.exists(docx_path):
            self.stdout.write(f"📄 'kira.docx' bulundu, okunuyor...")
            
            try:
                doc = docx.Document(docx_path)
                full_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                
                # Temizlik: Eski kanun maddelerini silelim (Temiz kurulum)
                silinen, _ = KanunMaddesi.objects.filter(kategori=kategori).delete()
                self.stdout.write(f"🧹 Temizlik: Eski {silinen} madde silindi.")

                madde_sayisi = 0
                current_baslik = ""
                
                for i, line in enumerate(full_text):
                    # Satır "MADDE" ile başlıyorsa (Örn: MADDE 299-)
                    if line.upper().startswith("MADDE"):
                        
                        # Madde Numarasını Ayıkla
                        match = re.search(r"MADDE\s+(\d+)", line, re.IGNORECASE)
                        madde_no = f"MADDE {match.group(1)}" if match else "MADDE ???"
                        
                        # İçeriği temizle
                        icerik = re.sub(r"^MADDE\s+\d+\s*[-–]\s*", "", line).strip()
                        
                        # Başlığı bul (Bir önceki satır genelde başlıktır)
                        if i > 0 and not full_text[i-1].upper().startswith("MADDE"):
                            current_baslik = full_text[i-1]
                        
                        # Kaydet
                        KanunMaddesi.objects.create(
                            kategori=kategori,
                            kanun_adi="Türk Borçlar Kanunu",
                            madde_no=madde_no,
                            icerik=f"{current_baslik}\n\n{icerik}"
                        )
                        madde_sayisi += 1

                self.stdout.write(self.style.SUCCESS(f'✅ Mevzuat Tamam: {madde_sayisi} adet TBK maddesi başarıyla işlendi.'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Word Dosyası Okunamadı: {e}"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠️ HATA: '{docx_path}' bulunamadı. Lütfen dosyayı ana dizine koyun."))

        # 3. CSV DOSYASINI OKUMA (Hata Olsa Bile Devam Et)
        csv_path = os.path.join(settings.BASE_DIR, 'emsal_kararlar.csv')
        
        if os.path.exists(csv_path):
            self.stdout.write("📊 'emsal_kararlar.csv' kontrol ediliyor...")
            try:
                df = pd.read_csv(csv_path, encoding='utf-8')
                
                # Dosya boş mu kontrolü
                if df.empty:
                    self.stdout.write(self.style.WARNING("⚠️ CSV dosyası boş, atlanıyor."))
                else:
                    sayac_karar = 0
                    for index, row in df.iterrows():
                        # İlk sütunu al (Genelde metin buradadır)
                        raw_metin = str(row.iloc[0])
                        if len(raw_metin) < 20: continue 

                        EmsalKarar.objects.update_or_create(
                            baslik=f"Yargıtay Emsal Karar #{index+1}",
                            defaults={"ozet": raw_metin[:1000] + "..."}
                        )
                        sayac_karar += 1
                    
                    self.stdout.write(self.style.SUCCESS(f'✅ İçtihatlar Tamam: {sayac_karar} karar yüklendi.'))

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ CSV Okunamadı (Önemli değil, atlanıyor): {e}"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ CSV dosyası yok, sadece kanun maddeleri ile devam ediliyor."))

        self.stdout.write(self.style.SUCCESS('🎉 VERİ YÜKLEME TAMAMLANDI!'))