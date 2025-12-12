import chromadb
import google.generativeai as genai

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
MY_API_KEY = "AIzaSyBpJTDubNFt1AqxpYNGT4xVH3h1D5UKma8"
DB_YOLU = "lexi_beyin_db"

genai.configure(api_key=MY_API_KEY)

# ==============================================================================
# 2. EMBEDDING FONKSİYONU (Beyinle Aynı Olmalı)
# ==============================================================================
def google_embedding_func(metinler):
    model = "models/text-embedding-004"
    vektorler = []
    for metin in metinler:
        try:
            result = genai.embed_content(
                model=model,
                content=metin,
                task_type="retrieval_query", # Burası 'query' oldu çünkü soru soruyoruz
                title="Soru"
            )
            vektorler.append(result['embedding'])
        except:
            vektorler.append([0]*768)
    return vektorler

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        return google_embedding_func(input)

# ==============================================================================
# 3. MANTIKSAL ÇIKARIM MOTORU (RAG)
# ==============================================================================
def lexi_baslat():
    # Veritabanına Bağlan
    client = chromadb.PersistentClient(path=DB_YOLU)
    collection = client.get_collection(
        name="emsal_kararlar",
        embedding_function=GeminiEmbeddingFunction()
    )
    
    # Konuşma Modeli (Cevabı yazacak olan)
    model = genai.GenerativeModel("gemini-1.5-flash") # Veya 'gemini-pro'

    print("\n" + "="*60)
    print("⚖️  LEXI: HUKUK ASİSTANI DEVREDE (Çıkış için 'q')")
    print("="*60)

    while True:
        soru = input("\n👤 Sorunuz: ")
        if soru.lower() == 'q': break
        
        print("🔍 Emsaller taranıyor ve analiz ediliyor...")

        # 1. ADIM: Emsal Bul (Retrieval)
        sonuclar = collection.query(query_texts=[soru], n_results=3)
        
        # Bulunanları birleştirip tek bir metin yapıyoruz
        bulunan_bilgiler = ""
        for i, doc in enumerate(sonuclar['documents'][0]):
            meta = sonuclar['metadatas'][0][i]
            bulunan_bilgiler += f"\n--- EMSAL {i+1} (Esas: {meta['esas_no']}) ---\n{doc}\n"

        # 2. ADIM: Cevap Yazdır (Generation)
        prompt = f"""
        Sen 'LEXI' adında profesyonel bir hukuk asistanısın.
        Kullanıcının sorusunu, SADECE aşağıda verilen 'BULUNAN EMSAL KARARLAR' ışığında cevapla.
        
        KURALLAR:
        1. Asla kendi kafandan kanun uydurma. Sadece verilen metinlere sadık kal.
        2. Cevabın sonunda, dayandığın emsal kararın Esas Numarasını parantez içinde belirt. (Örn: Yargıtay 3. HD 2014/2897 E.)
        3. Hukuki, ciddi ama anlaşılır bir dil kullan.
        4. Eğer emsallerde cevap yoksa, "Veritabanımdaki emsallerde bu konu hakkında bilgi bulunamadı" de.

        BULUNAN EMSAL KARARLAR:
        {bulunan_bilgiler}

        KULLANICI SORUSU:
        {soru}
        """
        
        try:
            cevap = model.generate_content(prompt)
            print("\n🤖 LEXI'NİN CEVABI:")
            print("-" * 60)
            print(cevap.text)
            print("-" * 60)
        except Exception as e:
            print(f"❌ Cevap oluşturulamadı: {e}")

if __name__ == "__main__":
    lexi_baslat()