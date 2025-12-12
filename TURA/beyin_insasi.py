import os
import json
import chromadb
import google.generativeai as genai
from chromadb.utils import embedding_functions

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
MY_API_KEY = "AIzaSyBpJTDubNFt1AqxpYNGT4xVH3h1D5UKma8"
VERI_KLASORU = "islenmis_veriler"
DB_YOLU = "lexi_beyin_db" # Veritabanının kaydedileceği klasör

genai.configure(api_key=MY_API_KEY)

# ==============================================================================
# 2. EMBEDDING (VEKTÖR) FONKSİYONU
# ==============================================================================
# Google'ın kendi Embedding modelini kullanacağız.
# Bu fonksiyon metni alır, [0.1, 0.5, -0.2 ...] şeklinde sayılara çevirir.
def google_embedding_func(metinler):
    # ChromaDB liste bekler, biz de liste olarak göndeririz
    model = "models/text-embedding-004" # Google'ın en iyi embedding modeli
    
    vektorler = []
    for metin in metinler:
        try:
            # Satır satır embedding alıyoruz (Batch işlemi de yapılabilir ama bu daha güvenli)
            result = genai.embed_content(
                model=model,
                content=metin,
                task_type="retrieval_document",
                title="Emsal Karar"
            )
            vektorler.append(result['embedding'])
        except Exception as e:
            print(f"❌ Embedding Hatası: {e}")
            # Hata olursa boş vektör dönmemek için dummy (sıfır) vektör verilebilir 
            # veya o kayıt atlanabilir. Şimdilik hatayı basıp geçiyoruz.
            vektorler.append([0]*768) 
            
    return vektorler

# ChromaDB için özel sınıf
class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        return google_embedding_func(input)

# ==============================================================================
# 3. VERİTABANI OLUŞTURMA VE YÜKLEME
# ==============================================================================
def veritabani_kur():
    print("🧠 LEXI'nin Beyni İnşa Ediliyor...")
    
    # ChromaDB İstemcisi (Diske kaydeder, böylece her seferinde tekrar kurmayız)
    client = chromadb.PersistentClient(path=DB_YOLU)
    
    # Koleksiyon (Tablo) Oluştur
    # Eğer varsa silip baştan oluşturuyoruz (Temiz kurulum için)
    try:
        client.delete_collection(name="emsal_kararlar")
    except:
        pass
        
    collection = client.create_collection(
        name="emsal_kararlar",
        embedding_function=GeminiEmbeddingFunction()
    )

    # Dosyaları Oku
    dosyalar = [f for f in os.listdir(VERI_KLASORU) if f.endswith(".json")]
    print(f"📂 Toplam {len(dosyalar)} adet işlenmiş karar bulundu. Yükleniyor...")

    ids = []
    documents = [] # Arama yapılacak metin
    metadatas = [] # Yan bilgiler (Tarih, Esas No vb.)

    for dosya_adi in dosyalar:
        with open(os.path.join(VERI_KLASORU, dosya_adi), "r", encoding="utf-8") as f:
            veri = json.load(f)

        # --- KRİTİK NOKTA: Arama yapılacak metni birleştiriyoruz ---
        # Yapay zeka bu metin üzerinden benzerlik kuracak.
        arama_metni = f"""
        Konu: {", ".join(veri['analiz'].get('konu_etiketleri', []))}
        Hukuki İlke: {veri['analiz'].get('hukuki_ilke', '')}
        Özet Hikaye: {veri['analiz'].get('ozet_hikaye', '')}
        Kritik Uyarı: {veri['analiz'].get('kritik_uyari', '')}
        """
        
        # Listelere ekle
        ids.append(veri['dosya_adi'])
        documents.append(arama_metni)
        
        # Metadata (Filtreleme için gerekli)
        metadatas.append({
            "esas_no": veri['kimlik'].get('esas_no', ''),
            "tarih": veri['kimlik'].get('tarih', ''),
            "hukum": veri['analiz'].get('hukum_sonucu', '')
        })

    # Veritabanına Ekle (Batch halinde)
    if ids:
        print("⏳ Vektörler oluşturuluyor (Bu işlem Google'a bağlanır, biraz sürebilir)...")
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ {len(ids)} karar başarıyla veritabanına gömüldü!")
    else:
        print("❌ Yüklenecek veri bulunamadı.")

    return collection

# ==============================================================================
# 4. SORGULAMA (CHAT) TESTİ
# ==============================================================================
def soru_sor(collection):
    print("\n" + "="*50)
    print("💬 LEXI SİSTEMİ HAZIR! (Çıkmak için 'q' bas)")
    print("="*50)

    while True:
        soru = input("\nSorunuz: ")
        if soru.lower() == 'q':
            break
            
        print("🔍 Veritabanında en benzer emsaller aranıyor...")
        
        # Veritabanında ara
        results = collection.query(
            query_texts=[soru],
            n_results=2 # En benzer 2 kararı getir
        )

        print("\n📢 BULUNAN EMSALLER:")
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            dosya_id = results['ids'][0][i]
            
            print(f"\n--- SONUÇ {i+1} ({dosya_id}) ---")
            print(f"📌 Esas: {metadata['esas_no']} | Tarih: {metadata['tarih']}")
            print(f"📝 İçerik Özeti: {doc.strip()[:300]}...") # İlk 300 karakter
            print("-" * 30)

if __name__ == "__main__":
    # Eğer veritabanı klasörü boşsa kur, doluysa sadece yükle
    db_koleksiyonu = veritabani_kur()
    
    # Soru sorma döngüsüne gir
    soru_sor(db_koleksiyonu)