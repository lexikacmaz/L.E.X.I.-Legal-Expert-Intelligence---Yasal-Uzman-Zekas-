import time
import chromadb
import numpy as np
import google.generativeai as genai
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.conf import settings 
from django.http import JsonResponse

# MODELLER
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, HukukKategori, BetaKullanici, 
)

# FORMLAR
from .forms import (
    AyarForm, AvukatForm, PaketForm, KanunForm, SiparisForm, 
    RandevuForm, SohbetForm, RandevuAdminForm, AvukatProfilForm, 
    RandevuDurumForm, ReklamForm, BetaGirisForm, BetaKullaniciForm, BetaBasvuruForm
)

# --- GLOBAL AYARLAR ---
CHROMA_PATH = "./chroma_db"
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
except:
    chroma_client = None

# API KEY
API_KEY = settings.GOOGLE_API_KEY
genai.configure(api_key=API_KEY)
EMBEDDING_MODEL = "models/text-embedding-004"

def get_settings():
    ayar, created = SiteAyarlari.objects.get_or_create(id=1)
    return ayar

# ==========================================
# --- BETA SİSTEMİ (BAŞVURU VE GİRİŞ) ---
# ==========================================

def beta_basvuru(request):
    """Kullanıcıların başvuru yapmasını sağlar."""
    if request.method == 'POST':
        form = BetaBasvuruForm(request.POST)
        if form.is_valid():
            # Kaydı oluştur ama ONAYLAMA (Admin onaylayacak)
            yeni_kullanici = form.save(commit=False)
            yeni_kullanici.onaylandi = False 
            yeni_kullanici.save()
            messages.success(request, 'Başvurunuz alındı! Yönetici onayladığında giriş yapabileceksiniz.')
            return redirect('beta_giris')
    else:
        form = BetaBasvuruForm()
    
    return render(request, 'beta_basvuru.html', {'form': form})

def beta_giris_yap(request):
    """Hem Yönetici (Superuser) hem de Beta Kullanıcıları buradan girebilir."""
    if request.method == 'POST':
        kadi = request.POST.get('kullanici_adi')
        sifre = request.POST.get('sifre')

        # 1. ÖNCE: Yönetici (Superuser) mi?
        admin_user = authenticate(request, username=kadi, password=sifre)
        
        if admin_user is not None:
            if admin_user.is_superuser:
                login(request, admin_user)
                messages.success(request, f'Yönetici girişi başarılı. Hoşgeldin {kadi} 👑')
                # DÜZELTME BURADA: 'home' yerine '/' yazdık
                return redirect('/') 

        # 2. SONRA: Beta Kullanıcısı mı?
        beta_user = BetaKullanici.objects.filter(kullanici_adi=kadi, sifre=sifre).first()

        if beta_user:
            if beta_user.onaylandi:
                request.session['beta_kullanici_id'] = beta_user.id
                messages.success(request, f'Giriş başarılı. Hoşgeldin {beta_user.kullanici_adi}')
                # DÜZELTME BURADA: 'home' yerine '/' yazdık
                return redirect('/')
            else:
                messages.error(request, 'Hesabınız henüz onaylanmadı. Lütfen bekleyiniz.')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')

    return render(request, 'beta_giris.html')
# ==========================================
# --- AI VE ANASAYFA ---
# ==========================================

# --- HIZLANDIRILMIŞ AI FONKSİYONU ---
# --- GÜÇLENDİRİLMİŞ & HIZLANDIRILMIŞ AI FONKSİYONU ---
def generate_safe_content(prompt):
    # Denenecek Modeller (Sırasıyla en hızlıdan en güçlüye)
    model_listesi = [
        "gemini-1.5-flash",          # En hızlısı (Varsa)
        "gemini-1.5-flash-latest",   # Alternatif isim
        "gemini-1.5-pro",            # Daha zeki
        "gemini-pro",                # En kararlı (Eski ama sağlam)
    ]
    
    system_instruction = "Sen uzman bir hukuk asistanısın. Cevaplarını HTML formatında (h3, ul, li) ver. Kısa ve net ol."

    for model_name in model_listesi:
        try:
            # Modeli başlat
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction
            )
            
            # İçerik üret (Hız ayarlarıyla)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=800, # Hız için sınırı koru
                    temperature=0.7
                )
            )
            # Eğer cevap boş değilse döndür
            if response.text:
                return response.text
                
        except Exception as e:
            # Bu model çalışmadıysa (404 vs.) sessizce diğerine geç
            continue

    # Hiçbir model çalışmazsa
    return "<h3>⚠️ Bağlantı Hatası</h3><p>Şu an AI servislerine erişilemiyor. Lütfen daha sonra tekrar deneyin.</p>"

# core/views.py içindeki home fonksiyonunu bununla değiştir:

# ... importların ...

def home(request):
    # ============================================================
    # 🛡️ GÜVENLİK DUVARI: GİRİŞ YAPMAYANI İÇERİ ALMA
    # ============================================================
    # Eğer kullanıcı Admin değilse VE Beta girişi yapmamışsa -> Beta Girişe Fırlat
    if not request.user.is_superuser and 'beta_kullanici_id' not in request.session:
        return redirect('beta_giris')
    # ============================================================

    ayar = get_settings()
    banner_sol = ReklamBanner.objects.filter(pozisyon='Sol', aktif_mi=True).order_by('?').first()
    banner_sag = ReklamBanner.objects.filter(pozisyon='Sag', aktif_mi=True).order_by('?').first()
    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    
    # Session'daki cevabı al ve temizle (Sayfa yenilenince gitmesi için)
    cevap = request.session.pop('ai_cevap', None)
    
    secilen_bot_slug = "genel"
    
    if 'kalan_hak' not in request.session: request.session['kalan_hak'] = 1
    if request.user.is_superuser: request.session['kalan_hak'] = 999
    kalan_hak = request.session['kalan_hak']

    if request.method == "POST":
        soru = request.POST.get("soru")
        secilen_bot_slug = request.POST.get("bot_slug")

        # Hak Kontrolü
        if kalan_hak <= 0 and not request.user.is_superuser:
            # AJAX isteği ise JSON dön
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Limitiniz doldu. Lütfen paket satın alın.'}, status=403)
            return render(request, 'limit_bitti.html', {'ayar': ayar})

        try:
            # --- AI İŞLEMLERİ ---
            if secilen_bot_slug == 'genel':
                prompt = f"""
                VERİ: {context_text}
                SORU: "{soru}"
                GÖREV: Yukarıdaki veriyi kullanarak soruya kısa, maddeler halinde ve net bir cevap ver.
                FORMAT: <h3>Durum</h3>... <h3>Öneri</h3>... şeklinde HTML kullan.
                """
                cevap = generate_safe_content(prompt)
            else:
                # Özel Bot Mantığı
                try:
                    collection = chroma_client.get_collection(name=secilen_bot_slug)
                except:
                    cevap = "<h3>⚠️ Veri Tabanı Hatası</h3><p>Veri yüklenmemiş. Genel Bot'u kullanın.</p>"
                
                if not cevap or "Hata" not in cevap:
                    try:
                        soru_vec = genai.embed_content(model=EMBEDDING_MODEL, content=soru, task_type="retrieval_query")['embedding']
                    except:
                        soru_vec = genai.embed_content(model="models/embedding-001", content=soru, task_type="retrieval_query")['embedding']

                    results = collection.query(query_embeddings=[soru_vec], n_results=2)
                    
                    if 'documents' in results and results['documents'] and results['documents'][0]:
                        bulunan_metinler = results['documents'][0]
                        context_text = "\n\n".join(bulunan_metinler)
                        prompt = f"""
                        GÖREVİN: Sadece aşağıdaki verileri kullanan hukuk uzmanısın.
                        VERİ: {context_text}
                        SORU: "{soru}"
                        KURALLAR: HTML formatında cevapla. Uydurma.
                        """
                        cevap = generate_safe_content(prompt)
                    else:
                        cevap = f"<h3>🚫 Sonuç Bulunamadı</h3><p>Veritabanında bilgi yok.</p>"

            # Temizlik ve Kayıt
            cevap = cevap.replace('```html', '').replace('```', '')
            SohbetGecmisi.objects.create(soru=soru, cevap=cevap)
            
            if not request.user.is_superuser:
                request.session['kalan_hak'] -= 1
                request.session.modified = True
                kalan_hak = request.session['kalan_hak'] # Güncel hakkı al

            # AJAX İsteği ise JSON Döndür (Sayfa Yenilenmez)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'cevap': cevap,
                    'kalan_hak': kalan_hak
                })
            
            # Normal POST ise Session'a kaydet ve yönlendir (Yenileme sorununu çözer)
            request.session['ai_cevap'] = cevap
            return redirect('home')

        except Exception as e:
            error_msg = f"<p class='error'>Hata: {str(e)}</p>"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=500)
            
            request.session['ai_cevap'] = error_msg
            return redirect('home')

    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

def render_home(request, ayar, cevap, kategoriler, b_sol, b_sag, bot, hak):
    return render(request, 'home.html', {
        'ayar': ayar, 'cevap': cevap, 'kategoriler': kategoriler,
        'banner_sol': b_sol, 'banner_sag': b_sag,
        'secilen_bot': bot, 'kalan_hak': hak,
    })

# ==========================================
# --- DİĞER SAYFALAR (AVUKATLAR, PAKETLER) ---
# ==========================================

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

# ==========================================
# --- YÖNETİM PANELİ ---
# ==========================================

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
    models_map = {
        'avukat': Avukat, 'paket': Paket, 'kanun': KanunMaddesi, 
        'reklam': ReklamBanner, 'siparis': Siparis, 
        'sohbet': SohbetGecmisi, 'randevu': AvukatRandevu,
        'beta': BetaKullanici
    }
    Model = models_map.get(tip)
    items = Model.objects.all().order_by('-id') if Model else []
    return render(request, 'panel/liste.html', {'items': items, 'tip': tip})

@login_required
def panel_ekle(request, tip):
    forms_map = {
        'avukat': AvukatForm, 'paket': PaketForm, 
        'reklam': ReklamForm, 'kanun': KanunForm,
        'beta': BetaKullaniciForm
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
        'avukat': (Avukat, AvukatForm), 'paket': (Paket, PaketForm),
        'kanun': (KanunMaddesi, KanunForm), 'reklam': (ReklamBanner, ReklamForm),
        'siparis': (Siparis, SiparisForm), 'sohbet': (SohbetGecmisi, SohbetForm),
        'randevu': (AvukatRandevu, RandevuAdminForm),
        'beta': (BetaKullanici, BetaKullaniciForm)
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
    models_map = {'avukat': Avukat, 'paket': Paket, 'reklam': ReklamBanner, 'kanun': KanunMaddesi, 'beta': BetaKullanici}
    Model = models_map.get(tip)
    if Model: get_object_or_404(Model, id=id).delete()
    return redirect('panel_icerik', tip=tip)

# ==========================================
# --- AVUKAT SİSTEMİ ---
# ==========================================

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

def cikis_yap(request): logout(request); return redirect('home')

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

# URL yönlendirmeleri
def kategori_listesi(request): return redirect('home')
def uzman_bot_chat(request, slug): return redirect('home')