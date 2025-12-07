import time
import requests
import feedparser
import google.generativeai as genai
from django.core.management.base import BaseCommand
from core.models import KanunMaddesi

# API AYARLARI
API_KEY = "AIzaSyCkgzc7kNT8vNhHjC_PDPJtliwN9oPphNk"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

class Command(BaseCommand):
    help = 'Sadece resmi ve emsal kararları tarar, isimleri sansürler.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🛡️ Hukuk Botu V6.0 (KVKK Korumalı & Resmi) Başlatılıyor...'))

        # 1. KAYNAKLAR (Sadece Hukuk ve Gündem Kategorileri)
        kaynaklar = [
            "https://www.haberturk.com/rss/gundem.xml",
            "https://www.sozcu.com.tr/rss/gundem.xml",
            "https://www.cumhuriyet.com.tr/rss/turkiye",
            "https://www.karar.com/rss/gundem/rss.xml",
            "https://www.gazeteduvar.com.tr/rss"
        ]
        
        # 2. ANAHTAR KELİME FİLTRESİ (Sadece Gerçek Davaları Al)
        # Haber başlığında bunlardan biri yoksa çöpe at.
        resmi_kelimeler = [
            "Yargıtay", "Danıştay", "Anayasa Mahkemesi", "AYM", 
            "Resmi Gazete", "Emsal Karar", "Mahkeme", "Dava", 
            "Savcılık", "İddianame", "Beraat", "Tahliye", "Hüküm",
            "Yargı", "Kanun", "Düzenleme", "Tazminat", "Nafaka"
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        
        while True:
            toplam_eklenen = 0
            
            for rss_url in kaynaklar:
                try:
                    # Requests ile veriyi çek
                    try:
                        response = requests.get(rss_url, headers=headers, timeout=10)
                    except:
                        continue # Bağlantı hatası varsa sessizce geç

                    if response.status_code != 200: continue

                    feed = feedparser.parse(response.content)
                    if not feed.entries: continue
                    
                    self.stdout.write(f"📡 Taranıyor: {rss_url} ({len(feed.entries)} başlık)")

                    # Son 3 haberi kontrol et
                    for entry in feed.entries[:3]: 
                        baslik = entry.title
                        ozet_ham = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                        
                        # --- FİLTRE 1: KONU KONTROLÜ ---
                        # Başlıkta veya Özette "Yargıtay, Mahkeme, Karar" geçiyor mu?
                        # Geçmiyorsa bu bir siyaset veya magazin haberidir, atla.
                        metin_toplam = (baslik + " " + ozet_ham).lower()
                        if not any(k.lower() in metin_toplam for k in resmi_kelimeler):
                            # self.stdout.write(f"   🗑️ Hukuki değil: {baslik[:30]}...")
                            continue

                        # Veritabanı Kontrolü (Zaten varsa geç)
                        if KanunMaddesi.objects.filter(madde_no__icontains=baslik[:50]).exists():
                            continue

                        self.stdout.write(f"   ⚖️ İNCELENİYOR: {baslik[:50]}...")

                        # --- FİLTRE 2: GEMINI SANSÜR VE ANALİZ ---
                        prompt = f"""
                        Aşağıdaki metin gerçek bir haberden alınmıştır.
                        BAŞLIK: "{baslik}"
                        ÖZET: "{ozet_ham}"
                        
                        GÖREVLERİN (Çok Önemli):
                        1. GİZLİLİK VE SANSÜR: Metindeki tüm gerçek kişi isimlerini (Ahmet, Mehmet vb.), kurum adlarını (X Şirketi vb.) ve şehirleri sil. Onların yerine "Davacı", "Davalı", "İşveren", "Sanık" gibi hukuki sıfatlar kullan. ASLA GERÇEK İSİM YAZMA.
                        2. ANALİZ: Bu haberi bir "Emsal Karar Özeti" haline getir.
                        3. FORMAT: Sadece Hukuk ve Emsal Karar niteliği taşıyorsa işle. Siyasetçilerin atışmasıysa "İPTAL" yaz.
                        
                        ÇIKTI FORMATI:
                        KONU: ... (Örn: Kira Hukuku - Yargıtay Kararı)
                        İÇERİK: ... (Anonimleştirilmiş, temiz hukuk metni)
                        """
                        
                        try:
                            res = model.generate_content(prompt)
                            cevap = res.text.strip()
                            
                            if "İPTAL" in cevap:
                                self.stdout.write("   🚫 Siyasi/Gereksiz içerik, atlandı.")
                                continue
                            
                            konu = "Emsal Karar"
                            icerik = cevap
                            
                            if "KONU:" in cevap:
                                parts = cevap.split("İÇERİK:")
                                if len(parts) > 1:
                                    konu = parts[0].replace("KONU:", "").strip()
                                    icerik = parts[1].strip()

                            # KAYDET
                            KanunMaddesi.objects.create(
                                madde_no=baslik[:90], # Başlığı referans no gibi kullan
                                konu=konu[:190],
                                icerik=icerik
                            )
                            toplam_eklenen += 1
                            self.stdout.write(self.style.SUCCESS(f"   💾 GÜVENLİ VE ANONİM KAYIT YAPILDI!"))
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"   YZ Hatası: {e}"))

                except Exception as e:
                    pass # Hata olursa akışı bozma, diğer kaynağa geç
            
            if toplam_eklenen == 0:
                self.stdout.write("💤 Yeni emsal karar yok. 15 dakika bekleniyor...")
                time.sleep(900)
            else:
                self.stdout.write(self.style.SUCCESS(f"🚀 {toplam_eklenen} yeni emsal karar eklendi!"))
                time.sleep(900)