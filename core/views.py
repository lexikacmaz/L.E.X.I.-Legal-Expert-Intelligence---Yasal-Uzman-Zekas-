import time
import chromadb
import numpy as np
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, HukukKategori
)
from .forms import (
    AyarForm, AvukatForm, PaketForm, KanunForm, SiparisForm, 
    RandevuForm, SohbetForm, RandevuAdminForm, AvukatProfilForm, 
    RandevuDurumForm, ReklamForm
)

# --- GLOBAL AYARLAR ---
CHROMA_PATH = "./chroma_db"
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
except:
    chroma_client = None

API_KEY = "AIzaSyAiAsM8IIa0LqLlUhfbqVS3RiRE3g_M12Q"
genai.configure(api_key=API_KEY)

# Embedding Modeli
EMBEDDING_MODEL = "models/text-embedding-004"

def get_settings():
    ayar, created = SiteAyarlari.objects.get_or_create(id=1)
    return ayar

# --- GÜVENLİ MODEL SEÇİCİ (Senin Listenle Güncellendi) ---
def generate_safe_content(prompt):
    """
    Senin API anahtarının desteklediği EN YENİ ve EN HIZLI modelleri dener.
    """
    model_listesi = [
        "gemini-2.5-flash",          # EN YENİ & HIZLI (Öncelikli)
        "gemini-2.0-flash",          # Çok Hızlı
        "gemini-flash-latest",       # Stabil Hızlı
        "models/gemini-2.5-flash",   # Alternatif isimlendirme
        "models/gemini-flash-latest" # Alternatif isimlendirme
    ]

    last_error = None

    for model_name in model_listesi:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            last_error = e
            continue # Bir sonraki modeli dene
    
    # Hiçbiri çalışmazsa hatayı fırlat
    raise Exception(f"Hiçbir model çalıştırılamadı. Son hata: {last_error}")

# --- ANA FONKSİYON (HOME) ---
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
            # --- SENARYO 1: GENEL BOT (HIZLI MOD) ---
            if secilen_bot_slug == 'genel':
                prompt = f"""
                GÖREVİN: Sen uzman, samimi ve net konuşan bir hukuk asistanısın.
                SORU: "{soru}"
                KURALLAR:
                1. Cevabı HTML formatında ver (h3, ul, li).
                2. Yanıtın kısa, net ve anlaşılır olsun (Hap Bilgi).
                3. Başlıklar: 🧐 Durum Analizi, ⚠️ Riskler, 💰 Masraflar, ✅ Yol Haritası.
                """
                cevap = generate_safe_content(prompt)

            # --- SENARYO 2: ÖZEL BOTLAR (GÜVENLİ & DATABASE MODU) ---
            else:
                try:
                    collection = chroma_client.get_collection(name=secilen_bot_slug)
                except:
                    cevap = "<h3>⚠️ Veri Tabanı Hatası</h3><p>Bu uzmanlık alanı için veri yüklenmemiş. Lütfen Genel Bot'u kullanın.</p>"
                    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

                # Embedding (Vektöre Çevirme)
                try:
                    soru_vec = genai.embed_content(
                        model=EMBEDDING_MODEL,
                        content=soru,
                        task_type="retrieval_query"
                    )['embedding']
                except:
                    # Fallback Embedding
                    soru_vec = genai.embed_content(
                        model="models/embedding-001",
                        content=soru,
                        task_type="retrieval_query"
                    )['embedding']

                # Veritabanında Ara
                results = collection.query(
                    query_embeddings=[soru_vec],
                    n_results=3
                )

                bulunan_metinler = results['documents'][0]
                
                if not bulunan_metinler:
                    cevap = f"<h3>🚫 Sonuç Bulunamadı</h3><p>Bu soru, <strong>{secilen_bot_slug.upper()}</strong> veritabanımızda yer almıyor.</p>"
                else:
                    context_text = "\n\n".join(bulunan_metinler)
                    prompt = f"""
                    GÖREVİN: Sen sadece aşağıdaki verileri kullanan sıkı bir hukuk uzmanısın.
                    
                    VERİTABANI BİLGİSİ: {context_text}
                    KULLANICI SORUSU: "{soru}"
                    
                    KURALLAR:
                    1. Cevabı SADECE yukarıdaki veritabanı bilgisine göre ver.
                    2. HTML formatında (h3, p, ul) çıktı ver.
                    3. Başlıklar: 🧐 Durum Analizi, ⚠️ Riskler, 💰 Masraflar, ✅ Yol Haritası.
                    4. Asla veritabanında olmayan bir şeyi uydurma.
                    """
                    cevap = generate_safe_content(prompt)

            cevap = cevap.replace('```html', '').replace('```', '')
            SohbetGecmisi.objects.create(soru=soru, cevap=cevap)
            
            if not request.user.is_superuser:
                request.session['kalan_hak'] -= 1
                request.session.modified = True
                kalan_hak = request.session['kalan_hak']

        except Exception as e:
            cevap = f"<p class='error'>Sistemsel Hata: {str(e)}</p>"

    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

def render_home(request, ayar, cevap, kategoriler, b_sol, b_sag, bot, hak):
    return render(request, 'home.html', {
        'ayar': ayar, 'cevap': cevap, 'kategoriler': kategoriler,
        'banner_sol': b_sol, 'banner_sag': b_sag,
        'secilen_bot': bot, 'kalan_hak': hak,
    })

# --- DİĞER STANDART FONKSİYONLAR (DEĞİŞMEDİ) ---
def cikis_yap(request):
    logout(request)
    return redirect('home')

def avukatlar(request):
    ayar = get_settings()
    liste = Avukat.objects.all()
    return render(request, 'avukatlar.html', {'ayar': ayar, 'avukatlar': liste})

def paketler(request):
    ayar = get_settings()
    liste = Paket.objects.all()
    return render(request, 'paketler.html', {'ayar': ayar, 'paketler': liste})

def yasal(request):
    ayar = get_settings()
    return render(request, 'legal.html', {'ayar': ayar})

def satin_al(request, paket_id):
    ayar = get_settings()
    secilen_paket = get_object_or_404(Paket, id=paket_id)
    if request.method == "POST":
        form = SiparisForm(request.POST)
        if form.is_valid():
            siparis = form.save(commit=False)
            siparis.paket = secilen_paket
            siparis.save()
            return redirect('odeme_sayfasi', siparis_id=siparis.id)
    else: form = SiparisForm()
    return render(request, 'satin_al.html', {'form': form, 'paket': secilen_paket, 'ayar': ayar})

def odeme_sayfasi(request, siparis_id):
    ayar = get_settings()
    siparis = get_object_or_404(Siparis, id=siparis_id)
    if request.method == "POST":
        siparis.odendi_mi = True
        siparis.save()
        return redirect('siparis_basarili')
    return render(request, 'odeme.html', {'siparis': siparis, 'ayar': ayar})

def siparis_basarili(request):
    ayar = get_settings()
    return render(request, 'basarili.html', {'ayar': ayar})

def randevu_al(request, avukat_id):
    ayar = get_settings()
    secilen_avukat = get_object_or_404(Avukat, id=avukat_id)
    if request.method == "POST":
        form = RandevuForm(request.POST)
        if form.is_valid():
            randevu = form.save(commit=False)
            randevu.avukat = secilen_avukat
            randevu.save()
            return render(request, 'basarili.html', {'ayar': ayar, 'mesaj': 'Talebiniz iletildi.'})
    else: form = RandevuForm()
    return render(request, 'randevu.html', {'form': form, 'avukat': secilen_avukat, 'ayar': ayar})

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
    models_map = {'avukat': Avukat, 'paket': Paket, 'kanun': KanunMaddesi, 'reklam': ReklamBanner, 'siparis': Siparis, 'sohbet': SohbetGecmisi, 'randevu': AvukatRandevu}
    Model = models_map.get(tip)
    items = Model.objects.all().order_by('-id') if Model else []
    return render(request, 'panel/liste.html', {'items': items, 'tip': tip})

@login_required
def panel_ekle(request, tip):
    forms_map = {'avukat': AvukatForm, 'paket': PaketForm, 'reklam': ReklamForm, 'kanun': KanunForm}
    FormClass = forms_map.get(tip)
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        if form.is_valid(): form.save(); return redirect('panel_icerik', tip=tip)
    else: form = FormClass()
    return render(request, 'panel/form.html', {'form': form, 'title': f'Yeni {tip} Ekle'})

@login_required
def panel_duzenle(request, tip, id):
    config = {'avukat': (Avukat, AvukatForm), 'paket': (Paket, PaketForm), 'kanun': (KanunMaddesi, KanunForm), 'reklam': (ReklamBanner, ReklamForm), 'siparis': (Siparis, SiparisForm), 'sohbet': (SohbetGecmisi, SohbetForm), 'randevu': (AvukatRandevu, RandevuAdminForm)}
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
    models_map = {'avukat': Avukat, 'paket': Paket, 'reklam': ReklamBanner, 'kanun': KanunMaddesi}
    Model = models_map.get(tip)
    if Model: get_object_or_404(Model, id=id).delete()
    return redirect('panel_icerik', tip=tip)

@login_required
def avukat_dashboard(request):
    if not hasattr(request.user, 'avukat'):
        if request.user.is_superuser: return redirect('panel_dashboard')
        return render(request, 'hata.html', {'mesaj': 'Yetkisiz giriş.'})
    avukat = request.user.avukat
    tum = AvukatRandevu.objects.filter(avukat=avukat)
    istatistik = {'toplam': tum.count(), 'bekleyen': tum.filter(durum='Bekliyor').count(), 'tamamlanan': tum.filter(durum='Tamamlandı').count(), 'iptal': tum.filter(durum='İptal').count()}
    return render(request, 'avukat_panel/dashboard.html', {'avukat': avukat, 'bekleyenler': tum.filter(durum='Bekliyor').order_by('-tarih'), 'gecmis': tum.exclude(durum='Bekliyor').order_by('-tarih'), 'istatistik': istatistik})

@login_required
def avukat_profil_duzenle(request):
    avukat = request.user.avukat
    if request.method == "POST":
        form = AvukatProfilForm(request.POST, request.FILES, instance=avukat)
        if form.is_valid(): form.save(); return redirect('avukat_dashboard')
    else: form = AvukatProfilForm(instance=avukat)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Profilimi Düzenle'})

@login_required
def avukat_randevu_islem(request, id):
    randevu = get_object_or_404(AvukatRandevu, id=id, avukat=request.user.avukat)
    if request.method == "POST":
        form = RandevuDurumForm(request.POST, instance=randevu)
        if form.is_valid(): form.save(); return redirect('avukat_dashboard')
    else: form = RandevuDurumForm(instance=randevu)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Randevu Durumu Güncelle'})

def kategori_listesi(request): return redirect('home')
def uzman_bot_chat(request, slug): return redirect('home')

def avukat_giris_yap(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                messages.error(request, "⚠️ HATA: Yönetici buradan giremez.")
                return render(request, 'registration/login.html', {'form': form})
            login(request, user)
            return redirect('avukat_dashboard')
    else: form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})