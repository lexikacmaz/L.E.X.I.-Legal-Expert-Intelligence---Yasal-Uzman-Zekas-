import google.generativeai as genai

API_KEY = "AIzaSyA8HzrxpyLDSdVBRQMc24SLHGiNSMMdYbo" # Senin Key
genai.configure(api_key=API_KEY)

print("🔍 Google API Bağlantısı Test Ediliyor...")

try:
    print("📋 Kullanılabilir Modeller:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   👉 {m.name}")
            
    # Test mesajı gönderelim (En garantisi gemini-pro ile)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Merhaba, çalışıyor musun?")
    print(f"\n✅ Test Başarılı! Cevap: {response.text}")
    
except Exception as e:
    print(f"\n❌ HATA: {e}")