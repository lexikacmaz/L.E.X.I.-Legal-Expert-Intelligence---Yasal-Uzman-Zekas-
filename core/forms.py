import time
import chromadb
import numpy as np
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

# MODELLER VE FORMLAR
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, HukukKategori, BetaKullanici
)
from .forms import (
    AyarForm, AvukatForm, PaketForm, KanunForm, SiparisForm, 
    RandevuForm, SohbetForm, RandevuAdminForm, AvukatProfilForm, 
    RandevuDurumForm, ReklamForm, BetaGirisForm, BetaKullaniciForm
)

# --- GLOBAL AYARLAR ---
CHROMA_PATH = "./chroma_db"
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
except:
    chroma_client = None

API_KEY = "AIzaSyAiAsM8IIa0LqLlUhfbqVS3RiRE3g_M12Q"
genai.configure(api_key=API_KEY)
EMBEDDING_MODEL = "models/text-embedding-004"

def get_settings():
    ayar, created = SiteAyarlari.objects.get_or_create(id=1)
    return ayar

# --- BETA GİRİŞ EKRANI ---
def beta_giris_yap(request):
    if request.session.get('beta_erisim_izni'):
        return redirect('home')
        
    hata = None
    if request.method == 'POST':
        form = BetaGirisForm(request.POST)
        if form.is_valid():
            kadi = form.cleaned_data['kullanici_adi']
            sifre = form.cleaned_data['sifre']
            user = BetaKullanici.objects.filter(kullanici_adi=kadi, sifre=sifre, aktif_mi=True).first()
            
            if user:
                request.session['beta_erisim_izni'] = True
                return redirect('home')
            else:
                hata = "Hatalı kullanıcı adı veya şifre!"
    else:
        form = BetaGirisForm()

    return render(request, 'beta_login.html', {'form': form, 'hata': hata})

# --- GÜVENLİ MODEL SEÇİCİ ---
def generate_safe_content(prompt):
    model_listesi = [
        "gemini-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    last_error = None
    for model_name in model_listesi:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            last_error = e
            continue
    raise Exception(f"Hiçbir model çalıştırılamadı. Hata: {last_error}")

# --- ANA SAYFA ---
def home(request):
    ayar = get_settings()
    banner_sol = ReklamBanner.objects.filter(pozisyon='Sol', aktif_mi=True).order_by('?').first()
    banner_sag = ReklamBanner.objects.filter(pozisyon='Sag', aktif_mi=True).order_by('?').first()
    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    cevap = None
    secilen_bot_slug = "genel"
    
    if 'kalan_hak' not in request.session: request.session['kalan_hak'] = 1
    if request.user.is_superuser: request.session['kalan_hak'] = 999
    kalan_hak = request.session['kalan_hak']

    if request.method == "POST":
        soru = request.POST.get("soru")
        secilen_bot_slug = request.POST.get("bot_slug")

        if kalan_hak <= 0 and not request.user.is_superuser:
            return render(request, 'limit_bitti.html', {'ayar': ayar})

        try:
            if secilen_bot_slug == 'genel':
                prompt = f"""
                GÖREVİN: Sen uzman bir hukuk asistanısın.
                SORU: "{soru}"
                KURALLAR: Cevabı HTML formatında (h3, ul, li) ver. Kısa ve net olsun.
                Başlıklar: 🧐 Durum Analizi, ⚠️ Riskler, 💰 Masraflar, ✅ Yol Haritası.
                """
                cevap = generate_safe_content(prompt)
            else:
                try:
                    collection = chroma_client.get_collection(name=secilen_bot_slug)
                except:
                    cevap = "<h3>⚠️ Veri Tabanı Hatası</h3><p>Veri yüklenmemiş. Genel Bot'u kullanın.</p>"
                    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

                try:
                    soru_vec = genai.embed_content(model=EMBEDDING_MODEL, content=soru, task_type="retrieval_query")['embedding']
                except:
                    soru_vec = genai.embed_content(model="models/embedding-001", content=soru, task_type="retrieval_query")['embedding']

                results = collection.query(query_embeddings=[soru_vec], n_results=3)
                bulunan_metinler = results['documents'][0]
                
                if not bulunan_metinler:
                    cevap = f"<h3>🚫 Sonuç Bulunamadı</h3><p>Veritabanında bilgi yok.</p>"
                else:
                    context_text = "\n\n".join(bulunan_metinler)
                    prompt = f"""
                    GÖREVİN: Sadece aşağıdaki verileri kullanan hukuk uzmanısın.
                    VERİ: {context_text}
                    SORU: "{soru}"
                    KURALLAR: HTML formatında cevapla. Uydurma.
                    """
                    cevap = generate_safe_content(prompt)

            cevap = cevap.replace('```html', '').replace('```', '')
            SohbetGecmisi.objects.create(soru=soru, cevap=cevap)
            
            if not request.user.is_superuser:
                request.session['kalan_hak'] -= 1
                request.session.modified = True
                kalan_hak = request.session['kalan_hak']

        except Exception as e:
            cevap = f"<p class='error'>Hata: {str(e)}</p>"

    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

def render_home(request, ayar, cevap, kategoriler, b_sol, b_sag, bot, hak):
    return render(request, 'home.html', {
        'ayar': ayar, 'cevap': cevap, 'kategoriler': kategoriler,
        'banner_sol': b_sol, 'banner_sag': b_sag,
        'secilen_bot': bot, 'kalan_hak': hak,
    })

# --- YÖNETİM PANELİ İŞLEMLERİ (DÜZELTİLEN KISIM) ---

@login_required(login_url='/admin/login/') 
def panel_dashboard(request):
    if not request.user.is_superuser: return redirect('avukat_dashboard')
    return render(request, 'panel/dashboard.html')

@login_required
def panel_ayarlar(request):
    ayar = get_settings()
    if request.method == "POST":
        form = AyarForm(request.POST, request.FILES, instance=ayar)
        if form.is_valid(): form.save(); return redirect('panel_dashboard')
    else: form = AyarForm(instance=ayar)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Site Ayarları'})

@login_required
def panel_icerik(request, tip):
    # Sözlüğü açık ve temiz yazdık
    models_map = {
        'avukat': Avukat,
        'paket': Paket,
        'kanun': KanunMaddesi,
        'reklam': ReklamBanner,
        'siparis': Siparis,
        'sohbet': SohbetGecmisi,
        'randevu': AvukatRandevu,
        'beta': BetaKullanici  # YENİ EKLENDİ
    }
    
    Model = models_map.get(tip)
    items = Model.objects.all().order_by('-id') if Model else []
    return render(request, 'panel/liste.html', {'items': items, 'tip': tip})

@login_required
def panel_ekle(request, tip):
    forms_map = {
        'avukat': AvukatForm,
        'paket': PaketForm,
        'reklam': ReklamForm,
        'kanun': KanunForm,
        'beta': BetaKullaniciForm # YENİ EKLENDİ
    }
    
    FormClass = forms_map.get(tip)
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        if form.is_valid(): form.save(); return redirect('panel_icerik', tip=tip)
    else: form = FormClass()
    return render(request, 'panel/form.html', {'form': form, 'title': f'Yeni {tip} Ekle'})

@login_required
def panel_duzenle(request, tip, id):
    config = {
        'avukat': (Avukat, AvukatForm),
        'paket': (Paket, PaketForm),
        'kanun': (KanunMaddesi, KanunForm),
        'reklam': (ReklamBanner, ReklamForm),
        'siparis': (Siparis, SiparisForm),
        'sohbet': (SohbetGecmisi, SohbetForm),
        'randevu': (AvukatRandevu, RandevuAdminForm),
        'beta': (BetaKullanici, BetaKullaniciForm) # YENİ EKLENDİ
    }
    
    if tip not in config: return redirect('panel_dashboard')
    
    Model, FormClass = config[tip]
    kayit = get_object_or_404(Model, id=id)
    
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=kayit)
        if form.is_valid(): form.save(); return redirect('panel_icerik', tip=tip)
    else: form = FormClass(instance=kayit)
    return render(request, 'panel/form.html', {'form': form, 'title': f'{tip.capitalize()} Düzenle'})

@login_required
def panel_sil(request, tip, id):
    models_map = {
        'avukat': Avukat,
        'paket': Paket,
        'reklam': ReklamBanner,
        'kanun': KanunMaddesi,
        'beta': BetaKullanici # YENİ EKLENDİ
    }
    Model = models_map.get(tip)
    if Model: get_object_or_404(Model, id=id).delete()
    return redirect('panel_icerik', tip=tip)

# --- DİĞERLERİ ---
def avukat_giris_yap(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                messages.error(request, "⚠️ Yönetici buradan giremez.")
                return render(request, 'registration/login.html', {'form': form})
            login(request, user)
            return redirect('avukat_dashboard')
    else: form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def cikis_yap(request): logout(request); return redirect('home')
def avukat_dashboard(request): return render(request, 'avukat_panel/dashboard.html') # Özetledim
def avukat_profil_duzenle(request): pass # Özetledim
def avukat_randevu_islem(request, id): pass # Özetledim
def kategori_listesi(request): return redirect('home')
def uzman_bot_chat(request, slug): return redirect('home')