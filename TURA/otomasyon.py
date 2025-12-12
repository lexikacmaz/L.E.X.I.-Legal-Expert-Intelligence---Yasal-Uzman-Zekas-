import os
import json
import time
import re
import google.generativeai as genai

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
MY_API_KEY = "BURAYA_GEMINI_API_KEY_YAZILACAK"

# Klasör İsimleri
GIRIS_KLASORU = "ham_kararlar"
CIKIS_KLASORU = "islenmis_veriler"

# Gemini Ayarı
genai.configure(api_key=MY_API_KEY)
# Çalışan modelini buraya yaz (1.5 Flash veya Pro)
MODEL_ADI = "models/gemini-1.5-flash" 

# ==============================================================================
# 2. BEDAVA ANALİZ MOTORU (REGEX)
# ==============================================================================
def regex_ile_temel_bilgi_cek(metin):
    veri = {}
    
    # Esas No (Örn: 2024/123 E.)
    esas = re.search(r"(\d{4}/\d+)\s*E\.", metin)
    veri["esas_no"] = esas.group(1) if esas else "Belirtilmemiş"

    # Karar No (Örn: 2024/99 K.)
    karar = re.search(r"(\d{4}/\d+)\s*K\.", metin)
    veri["karar_no"] = karar.group(1) if karar else "Belirtilmemiş"

    # Tarih (Örn: 10.05.2025)
    tarih = re.search(r"(\d{2}\.\d{2}\.\d{4})", metin)
    veri["tarih"] = tarih.group(1) if tarih else "Belirtilmemiş"
    
    # Hüküm (Kaba Taslak)
    if "REDDİNE" in metin: veri["hukum_tipi"] = "RED"
    elif "ONANMASINA" in metin: veri["hukum_tipi"] = "ONAMA"
    elif "BOZULMASINA" in metin: veri["hukum_tipi"] = "BOZMA"
    else: veri["hukum_tipi"] = "DİĞER"

    return veri

# ==============================================================================
# 3. AKILLI ANALİZ MOTORU (GEMINI AI)
# ==============================================================================
def gemini_ile_derin_analiz(metin, temel_bilgiler):
    model = genai.GenerativeModel(MODEL_ADI)
    
    # AI'ya sadece metnin gerekli kısmını ve Regex ile bulduğumuz ipuçlarını veriyoruz
    prompt = f"""
    Sen hukuk asistanısın. Aşağıdaki kararı analiz et.
    Bulunan Ön Bilgiler: {temel_bilgiler}

    İSTENEN ÇIKTI (SADECE JSON):
    {{
        "konu_etiketleri": ["Kira", "Tahliye", "Temerrüt" vb.],
        "hukuki_ilke": "Kararın emsal niteliğindeki özeti (tek cümle)",
        "ozet_hikaye": "Olayın kısa hikayesi",
        "kritik_uyari": "Varsa usul hatası veya süre vurgusu"
    }}

    KARAR METNİ:
    {metin[:10000]} 
    """
    # Not: Metnin ilk 10.000 karakterini alıyoruz ki token sınırı aşılmasın (Tasarruf)

    try:
        response = model.generate_content(prompt)
        # Temizlik
        json_str = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"   ⚠️ AI Analiz Hatası: {e}")
        return {"hata": "AI Analizi Yapılamadı", "detay": str(e)}

# ==============================================================================
# 4. FABRİKA BANDI (ANA DÖNGÜ)
# ==============================================================================
def sistemi_calistir():
    # Klasörleri kontrol et, yoksa oluştur
    if not os.path.exists(GIRIS_KLASORU):
        os.makedirs(GIRIS_KLASORU)
        print(f"📁 '{GIRIS_KLASORU}' klasörü oluşturuldu. Lütfen içine .txt dosyaları atın!")
        return

    if not os.path.exists(CIKIS_KLASORU):
        os.makedirs(CIKIS_KLASORU)

    # Dosyaları Listele
    dosyalar = [f for f in os.listdir(GIRIS_KLASORU) if f.endswith(".txt")]
    
    print(f"🏭 Fabrika Çalışıyor... Toplam {len(dosyalar)} dosya işlenecek.\n")

    for i, dosya_adi in enumerate(dosyalar):
        print(f"🔄 [{i+1}/{len(dosyalar)}] İşleniyor: {dosya_adi} ...")
        
        try:
            # 1. Dosyayı Oku
            yol = os.path.join(GIRIS_KLASORU, dosya_adi)
            with open(yol, "r", encoding="utf-8") as f:
                icerik = f.read()

            # 2. Bedava Analiz (Regex)
            temel_veri = regex_ile_temel_bilgi_cek(icerik)
            
            # 3. Ücretli/Limitli Analiz (AI)
            # Hız limiti yememek için her dosyada 4 saniye mola veriyoruz (Free Tier Dostu)
            time.sleep(4) 
            ai_veri = gemini_ile_derin_analiz(icerik, temel_veri)

            # 4. Verileri Birleştir
            final_veri = {
                "dosya_adi": dosya_adi,
                "teknik_bilgiler": temel_veri,
                "ai_analizi": ai_veri
            }

            # 5. Kaydet
            cikti_adi = dosya_adi.replace(".txt", ".json")
            cikti_yol = os.path.join(CIKIS_KLASORU, cikti_adi)
            
            with open(cikti_yol, "w", encoding="utf-8") as f_out:
                json.dump(final_veri, f_out, ensure_ascii=False, indent=4)
            
            print(f"   ✅ Kaydedildi: {cikti_adi}")

        except Exception as e:
            print(f"   ❌ Kritik Hata: {dosya_adi} işlenemedi. Sebebi: {e}")

    print("\n🏁 TÜM İŞLEMLER TAMAMLANDI! Çıktı klasörünü kontrol et.")

if __name__ == "__main__":
    sistemi_calistir