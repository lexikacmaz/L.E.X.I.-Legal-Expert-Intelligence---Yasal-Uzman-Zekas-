import os
import django
import google.generativeai as genai
import chromadb

# 1. Django Ortamını Yükle
# DİKKAT: 'proje_adi' kısmını kendi klasör adınla değiştir (settings.py'ın olduğu klasör)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HukukProje.settings') 
django.setup()

from core.models import KanunMaddesi, HukukKategori

# 2. API Ayarları (Embeddings için gerekli)
API_KEY = "AIzaSyAiAsM8IIa0LqLlUhfbqVS3RiRE3g_M12Q" # Senin Key
genai.configure(api_key=API_KEY)

# 3. ChromaDB (Offline Veritabanı) Hazırla
client = chromadb.PersistentClient(path="./chroma_db") # Bu klasöre kaydedecek

def verileri_vektorlestir():
    print("🚀 İŞLEM BAŞLIYOR: Kanunlar vektör veritabanına işleniyor...")
    
    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    
    if not kategoriler.exists():
        print("⚠️ HATA: Hiç aktif kategori bulunamadı! Lütfen önce Admin panelinden Kategori ve Kanun ekleyin.")
        return

    for kat in kategoriler:
        print(f"\n📂 Kategori: {kat.isim} ({kat.slug}) işleniyor...")
        
        # Varsa eski koleksiyonu sil, temiz kurulum yap
        try:
            client.delete_collection(name=kat.slug)
        except:
            pass
            
        collection = client.create_collection(name=kat.slug)
        
        # O kategorideki kanunları çek
        kanunlar = KanunMaddesi.objects.filter(kategori=kat)
        
        if not kanunlar.exists():
            print(f"   ↳ Bu kategoride hiç kanun yok, geçiliyor.")
            continue

        ids = []
        documents = []
        metadatas = []
        
        for kanun in kanunlar:
            # Yapay zekanın okuyacağı metin
            icerik = f"KANUN: {kanun.kanun_adi}\nMADDE: {kanun.madde_no}\nİÇERİK: {kanun.icerik}"
            
            ids.append(str(kanun.id))
            documents.append(icerik)
            metadatas.append({"baslik": kanun.kanun_adi, "no": kanun.madde_no})
            
        # Toplu İşlem (Batch Processing)
        print(f"   ↳ {len(documents)} madde Google'a gönderilip vektöre çevriliyor...")
        
        # Google Embeddings kullanarak vektöre çevir
        vectors = []
        batch_size = 20 # 20'şerli paketler halinde yolla
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            try:
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=batch,
                    task_type="retrieval_document"
                )
                vectors.extend(result['embedding'])
            except Exception as e:
                print(f"   ❌ HATA (Batch {i}): {e}")

        # ChromaDB'ye Kaydet
        if len(vectors) == len(documents):
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=vectors,
                metadatas=metadatas
            )
            print(f"   ✅ {len(documents)} madde başarıyla kaydedildi!")
        else:
            print("   ⚠️ Vektör sayısı uyuşmuyor, kayıt yapılamadı.")

    print("\n🏁 TÜM İŞLEMLER BİTTİ! Artık sisteminiz 'Offline Memory' özelliğine sahip.")

if __name__ == "__main__":
    verileri_vektorlestir()