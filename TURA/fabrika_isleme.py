import os
import json
import time
import re
import google.generativeai as genai
import sys

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
MY_API_KEY = "AIzaSyBpJTDubNFt1AqxpYNGT4xVH3h1D5UKma8"

# Klasör İsimleri
GIRIS_KLASORU = "ham_kararlar"
CIKIS_KLASORU = "islenmis_veriler"

genai.configure(api_key=MY_API_KEY)

# BU LİSTE HAYAT KURTARIR: Kod sırayla hepsini dener.
# Senin sisteminde çalışan 'models/gemini-2.5-flash' en başa koyuldu.
ADAY_MODELLER = [
    "models/gemini-2.5-flash",
    "gemini-2.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-flash",
    "models/gemini-pro",
    "gemini-pro"
]

# ==============================================================================
# 2. BEDAVA ANALİZ MOTORU (PYTHON REGEX)
# ==============================================================================
def regex_ile_temel_bilgi_cek(metin):
    veri = {}
    
    # Esas No
    esas = re.search(r"(\d{4}/\d+)\s*E\.?", metin)
    veri["esas_no"] = esas.group(1) if esas else "Belirtilmemiş"

    # Karar No
    karar = re.search(r"(\d{4}/\d+)\s*K\.?", metin)
    veri["karar_no"] = karar.group(1) if karar else "Belirtilmemiş"

    # Tarih
    tarih = re.search(r"(\d{2}\.\d{2}\.\d{4})", metin)
    veri["tarih"] = tarih.group(1) if tarih else "Belirtilmemiş"
    
    # Daire
    daire = re.search(r"(\d+\.\s*(Hukuk|Ceza)\s*Dairesi)", metin)
    veri["daire"] = daire.group(1) if daire else "Belirtilmemiş"

    return veri

# ==============================================================================
# 3. AKILLI ANALİZ MOTORU (MULTI-MODEL DESTEKLİ)
# ==============================================================================
def gemini_ile_derin_analiz(metin, temel_bilgiler):
    
    prompt = f"""
    Sen uzman bir hukuk asistanısın. Aşağıdaki mahkeme kararını analiz et.
    Elimizdeki Ön Bilgiler: {temel_bilgiler}

    GÖREVİN:
    1. Metindeki usul detaylarını yoksay.
    2. Kararın 'Hukuki İlkesini' (Emsal değerini) çıkar.
    3. Davanın sonucunu ve türünü belirle.

    İSTENEN ÇIKTI (SADECE JSON FORMATINDA):
    {{
        "konu_etiketleri": ["Kira", "Tahliye", "Usul" gibi anahtar kelimeler],
        "hukuki_ilke": "Karardan çıkan temel hukuk kuralı (Tek cümle).",
        "ozet_hikaye": "Olayın çok kısa özeti.",
        "kritik_uyari": "Varsa süre veya ispatla ilgili kritik nokta.",
        "hukum_sonucu": "ONAMA / BOZMA / RED"
    }}

    KARAR METNİ (Kısaltılmış):
    {metin[:15000]} 
    """

    # --- MODEL DENEME DÖNGÜSÜ ---
    for model_adi in ADAY_MODELLER:
        try:
            # Modeli Hazırla
            model = genai.GenerativeModel(model_adi)
            
            # İsteği Gönder
            response = model.generate_content(prompt)
            
            # Temizlik
            json_str = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_str) # Başarılıysa veriyi döndür ve çık

        except Exception as e:
            hata = str(e)
            
            # HATA ANALİZİ
            if "404" in hata or "not found" in hata:
                # Model bulunamadıysa sessizce diğer modele geç
                continue 
            elif "429" in hata or "quota" in hata:
                print(f"      ⚠️ Kota Doldu ({model_adi}). 30sn bekleniyor...")
                time.sleep(30)
                # Kota dolunca aynı modelle tekrar denemek yerine bir sonrakine şans veriyoruz
                continue
            else:
                # Başka hataysa logla ve devam et
                print(f"      ❌ {model_adi} Hatası: {hata}")
                continue

    # Döngü bitti ve hala sonuç yoksa:
    print("      ❌ HATA: Hiçbir model bu dosyayı işleyemedi.")
    return None

# ==============================================================================
# 4. FABRİKA BANDI (ANA DÖNGÜ)
# ==============================================================================
def fabrikaya_start_ver():
    if not os.path.exists(GIRIS_KLASORU):
        print(f"❌ '{GIRIS_KLASORU}' klasörü bulunamadı!")
        return
    if not os.path.exists(CIKIS_KLASORU):
        os.makedirs(CIKIS_KLASORU)

    dosyalar = [f for f in os.listdir(GIRIS_KLASORU) if f.endswith(".txt")]
    print(f"🏭 Fabrika Başlatıldı. İşlenecek Dosya Sayısı: {len(dosyalar)}\n")

    basarili = 0
    hatali = 0

    for index, dosya_adi in enumerate(dosyalar):
        hedef_json = dosya_adi.replace(".txt", ".json")
        hedef_yol = os.path.join(CIKIS_KLASORU, hedef_json)
        
        # Zaten işlenmişse atla
        if os.path.exists(hedef_yol):
            print(f"⏩ [{index+1}/{len(dosyalar)}] Zaten işlenmiş: {dosya_adi}")
            continue

        print(f"🔄 [{index+1}/{len(dosyalar)}] İşleniyor: {dosya_adi} ...")
        
        try:
            # 1. Dosyayı Oku
            with open(os.path.join(GIRIS_KLASORU, dosya_adi), "r", encoding="utf-8") as f:
                icerik = f.read()

            if len(icerik) < 50:
                print("      ⚠️ Dosya boş, atlanıyor.")
                continue

            # 2. Bedava Analiz
            temel_veri = regex_ile_temel_bilgi_cek(icerik)
            
            # 3. Akıllı Analiz (Otomatik Model Seçimi)
            ai_veri = gemini_ile_derin_analiz(icerik, temel_veri)

            if ai_veri:
                # 4. Kaydet
                final_veri = {
                    "dosya_adi": dosya_adi,
                    "kimlik": temel_veri,
                    "analiz": ai_veri,
                    "islenme_zamani": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                with open(hedef_yol, "w", encoding="utf-8") as f_out:
                    json.dump(final_veri, f_out, ensure_ascii=False, indent=4)
                
                print(f"      ✅ KAYDEDİLDİ!")
                basarili += 1
                time.sleep(2) # Google'ı yormamak için kısa mola
            else:
                hatali += 1

        except Exception as e:
            print(f"      ❌ Dosya Hatası: {e}")
            hatali += 1

    print(f"\n🏁 İŞLEM TAMAMLANDI! Başarılı: {basarili}, Hatalı: {hatali}")

if __name__ == "__main__":
    fabrikaya_start_ver()