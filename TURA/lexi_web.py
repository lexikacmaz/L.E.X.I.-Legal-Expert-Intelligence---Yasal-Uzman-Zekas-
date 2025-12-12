import streamlit as st
import chromadb
import google.generativeai as genai
import time

# ==============================================================================
# 1. AYARLAR
# ==============================================================================
st.set_page_config(page_title="LEXI - AI Hukuk", page_icon="⚖️", layout="wide")

MY_API_KEY = "AIzaSyBpJTDubNFt1AqxpYNGT4xVH3h1D5UKma8" # <--- ANAHTARINI YAPISTIR
DB_YOLU = "lexi_beyin_db"

genai.configure(api_key=MY_API_KEY)

# SENİN SİSTEMİNDE ÇALIŞAN GARANTİ MODEL LİSTESİ
# Kod sırayla bunları deneyecek.
ADAY_MODELLER = [
    "models/gemini-2.5-flash", 
    "gemini-2.5-flash",
    "models/gemini-1.5-flash",
    "gemini-1.5-flash",
    "models/gemini-pro"
]

# ==============================================================================
# 2. FONKSİYONLAR
# ==============================================================================
def google_embedding_func(metinler):
    model = "models/text-embedding-004"
    vektorler = []
    for metin in metinler:
        try:
            result = genai.embed_content(
                model=model,
                content=metin,
                task_type="retrieval_query",
                title="Soru"
            )
            vektorler.append(result['embedding'])
        except:
            vektorler.append([0]*768)
    return vektorler

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __call__(self, input: list[str]) -> list[list[float]]:
        return google_embedding_func(input)

@st.cache_resource
def veritabanini_yukle():
    try:
        client = chromadb.PersistentClient(path=DB_YOLU)
        collection = client.get_collection(
            name="emsal_kararlar",
            embedding_function=GeminiEmbeddingFunction()
        )
        return collection
    except Exception as e:
        st.error(f"Veritabanı hatası: {e}")
        return None

# ==============================================================================
# 3. YAN MENÜ & BAŞLIK
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/924/924915.png", width=80)
    st.title("LEXI v1.0")
    st.info("Bu sistem, yüklediğiniz Yargıtay Emsal Kararları üzerinden çalışır.")
    
    # Model Durumu
    st.write("---")
    st.caption(f"Veritabanı: {DB_YOLU}")

st.title("⚖️ LEXI: Yapay Zeka Hukuk Asistanı")
st.markdown("Sorunuzu sorun, emsal kararlara dayalı cevap alın.")

# ==============================================================================
# 4. CHAT MOTORU
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Hukuki sorunuzu buraya yazın (Örn: Kira artışı sınırı nedir?)")

if prompt:
    # Kullanıcı mesajını ekle
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 1. ADIM: Emsal Bul
        collection = veritabanini_yukle()
        if collection:
            sonuclar = collection.query(query_texts=[prompt], n_results=3)
            
            baglam = ""
            kaynaklar = []
            
            # Emsalleri Birleştir
            for i, doc in enumerate(sonuclar['documents'][0]):
                meta = sonuclar['metadatas'][0][i]
                baglam += f"\n--- KARAR {i+1} ---\n{doc}\n"
                kaynaklar.append(f"**Karar {i+1}:** Esas: {meta['esas_no']} | Tarih: {meta['tarih']}")
            
            # 2. ADIM: Doğru Modeli Bul ve Cevapla
            model_calisti = False
            
            # Tüm modelleri sırayla dene
            for model_adi in ADAY_MODELLER:
                if model_calisti: break
                
                try:
                    ai_model = genai.GenerativeModel(model_adi)
                    
                    ai_prompt = f"""
                    Sen profesyonel bir hukukçusun. Kullanıcının sorusunu AŞAĞIDAKİ KAYNAKLARA GÖRE cevapla.
                    
                    KAYNAKLAR:
                    {baglam}
                    
                    SORU: {prompt}
                    
                    KURALLAR:
                    1. Hukuki ve resmi bir dil kullan.
                    2. Cevabın sonunda kaynak göster.
                    """
                    
                    # Cevabı üret (Streaming)
                    response = ai_model.generate_content(ai_prompt, stream=True)
                    
                    for chunk in response:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    model_calisti = True # Başardık, döngüden çık
                    
                except Exception as e:
                    # Bu model çalışmadıysa sessizce diğerine geç
                    continue
            
            if not model_calisti:
                st.error("❌ Üzgünüm, şu an tüm yapay zeka modelleri meşgul veya kotanız dolmuş olabilir.")
            else:
                # Kaynakları göster
                with st.expander("📚 Kullanılan Emsal Kararlar"):
                    for k in kaynaklar:
                        st.markdown(f"- {k}")

    # Geçmişe kaydet
    st.session_state.messages.append({"role": "assistant", "content": full_response})