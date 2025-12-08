import os
import django
import google.generativeai as genai
import chromadb
from dotenv import load_dotenv
from tqdm import tqdm  # İlerleme çubuğu kütüphanesi
import time

# 1. Ayarları Yükle
load_dotenv()

# 2. Django Kurulumu
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HukukProje.settings')
django.setup()

from core.models import KanunMaddesi, HukukKategori, EmsalKarar

# 3. API Kontrolü
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("❌ HATA: API Anahtarı .env dosyasında bulunamadı!")
    exit()

try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"❌ API Hatası: {e}")
    exit()

# 4. Veritabanı Bağlantısı
client = chromadb.PersistentClient(path="./chroma_db")

def verileri_vektorlestir():
    print("\n" + "█"*60)
    print("🚀  L.E.X.I - YAPAY ZEKA HAFIZASI OLUŞTURULUYOR")
    print("█"*60 + "\n")

    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    if not kategoriler.exists():
        print("⚠️ HATA: Yüklenecek kategori bulunamadı. Önce 'python manage.py yukle_kira_full' komutunu çalıştırın.")
        return

    toplam_basarili = 0

    for kat in kategoriler:
        print(f"📂 KATEGORİ: {kat.isim} ({kat.slug}) Hazırlanıyor...")
        
        # Koleksiyonu Sıfırla
        try:
            client.delete_collection(name=kat.slug)
        except:
            pass
        collection = client.create_collection(name=kat.slug)

        # Verileri Çek
        kanunlar = KanunMaddesi.objects.filter(kategori=kat)
        emsaller = EmsalKarar.objects.all() # Gerekirse filtrele

        ids = []
        documents = []
        metadatas = []

        # Kanunları Hazırla
        for kanun in kanunlar:
            text = f"KANUN: {kanun.kanun_adi}\nNO: {kanun.madde_no}\nİÇERİK: {kanun.icerik}"
            ids.append(f"kanun_{kanun.id}")
            documents.append(text)
            metadatas.append({"tip": "kanun", "baslik": kanun.madde_no})

        # Emsal Kararları Hazırla (Sadece Kira Hukuku ise hepsini ekle)
        if kat.slug == "kira-hukuku":
            for emsal in emsaller:
                text = f"YARGITAY KARARI\nBAŞLIK: {emsal.baslik}\nÖZET: {emsal.ozet}"
                ids.append(f"emsal_{emsal.id}")
                documents.append(text)
                metadatas.append({"tip": "emsal", "baslik": emsal.baslik})

        total_items = len(documents)
        if total_items == 0:
            print("   ⚠️ Veri yok, geçiliyor.\n")
            continue

        print(f"   ↳ {total_items} adet veri işlenmek üzere Google'a gönderiliyor...")
        
        # --- İLERLEME ÇUBUĞU İLE YÜKLEME ---
        batch_size = 10
        vectors = []
        
        # TQDM: İlerleme çubuğunu burada başlatıyoruz
        pbar = tqdm(total=total_items, desc="   ⚡ İşleniyor", unit="veri", colour="green")
        
        for i in range(0, total_items, batch_size):
            batch_docs = documents[i:i+batch_size]
            try:
                # Google'dan Vektör Al
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=batch_docs,
                    task_type="retrieval_document"
                )
                vectors.extend(result['embedding'])
                
                # Çubuğu ilerlet
                pbar.update(len(batch_docs))
                
            except Exception as e:
                pbar.write(f"   ❌ HATA (Batch {i}): {e}") # Hata olursa çubuğu bozmadan yaz
        
        pbar.close()

        # ChromaDB'ye Kaydet
        if len(vectors) == len(documents):
            print("   💾 Hafızaya kaydediliyor...", end="")
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=vectors,
                metadatas=metadatas
            )
            print(" ✅")
            toplam_basarili += len(documents)
        else:
            print(f"\n   ⚠️ DİKKAT: Eksik veri var ({len(documents)} veri -> {len(vectors)} vektör).")

        print("-" * 40 + "\n")

    print(f"🏁 İŞLEM TAMAMLANDI! Toplam {toplam_basarili} hukuki bilgi L.E.X.I hafızasına yüklendi.")
    print("👉 Şimdi 'python manage.py runserver' yazarak siteyi açabilirsin.")

if __name__ == "__main__":
    verileri_vektorlestir()