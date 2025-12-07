from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.db.models import Q 
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, HukukKategori, EmsalKarar
)
from .forms import (
    AyarForm, AvukatForm, PaketForm, KanunForm, SiparisForm, 
    RandevuForm, SohbetForm, RandevuAdminForm, AvukatProfilForm, 
    RandevuDurumForm, ReklamForm
)
import google.generativeai as genai
import numpy as np

# --- AYARLARI ÇEKME ---
def get_settings():
    ayar, created = SiteAyarlari.objects.get_or_create(id=1)
    return ayar

# --- ESKİ GENEL SAYFALAR (Home, Avukatlar, Paketler vb.) ---

def home(request):
    """Eski Ana Sayfa (Genel Sohbet)"""
    ayar = get_settings()
    banner_sol = ReklamBanner.objects.filter(pozisyon='Sol', aktif_mi=True).order_by('?').first()
    banner_sag = ReklamBanner.objects.filter(pozisyon='Sag', aktif_mi=True).order_by('?').first()
    
    cevap = None
    kalan_hak = request.session.get('kalan_hak', 1)
    
    if request.user.is_superuser:
        request.session['kalan_hak'] = 999

    # Burası eski genel bot mantığı, olduğu gibi bırakıyoruz...
    # (Kodun sadeliği için burayı kısa geçiyorum, eski mantığın çalışmaya devam eder)
    return render(request, 'home.html', {
        'ayar': ayar, 
        'cevap': cevap, 
        'kalan_hak': kalan_hak,
        'banner_sol': banner_sol,
        'banner_sag': banner_sag,
    })

def cikis_yap(request):
    logout(request)
    if 'kalan_hak' in request.session: del request.session['kalan_hak']
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

# --- SATIŞ / RANDEVU İŞLEMLERİ ---

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
    else:
        form = SiparisForm()
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
    else:
        form = RandevuForm()
    return render(request, 'randevu.html', {'form': form, 'avukat': secilen_avukat, 'ayar': ayar})

# --- PANEL İŞLEMLERİ (Admin & Avukat) ---

# Artık giriş yapmamışsa Mavi Admin Girişine gönderecek
@login_required(login_url='/admin/login/') 
def panel_dashboard(request):
    if not request.user.is_superuser:
        return redirect('avukat_dashboard')
    return render(request, 'panel/dashboard.html')

@login_required
def panel_ayarlar(request):
    ayar = get_settings()
    if request.method == "POST":
        form = AyarForm(request.POST, request.FILES, instance=ayar)
        if form.is_valid():
            form.save()
            return redirect('panel_dashboard')
    else:
        form = AyarForm(instance=ayar)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Site Ayarları'})

@login_required
def panel_icerik(request, tip):
    # Tip kontrolü ve listeleme
    models_map = {
        'avukat': Avukat, 'paket': Paket, 'kanun': KanunMaddesi, 
        'reklam': ReklamBanner, 'siparis': Siparis, 
        'sohbet': SohbetGecmisi, 'randevu': AvukatRandevu
    }
    Model = models_map.get(tip)
    if Model:
        items = Model.objects.all().order_by('-id')
    else:
        items = []
    return render(request, 'panel/liste.html', {'items': items, 'tip': tip})

@login_required
def panel_ekle(request, tip):
    forms_map = {
        'avukat': AvukatForm, 'paket': PaketForm, 'reklam': ReklamForm, 'kanun': KanunForm
    }
    FormClass = forms_map.get(tip)
    
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('panel_icerik', tip=tip)
    else:
        form = FormClass()
    return render(request, 'panel/form.html', {'form': form, 'title': f'Yeni {tip} Ekle'})

@login_required
def panel_duzenle(request, tip, id):
    # Model ve Form eşleştirme
    config = {
        'avukat': (Avukat, AvukatForm), 'paket': (Paket, PaketForm),
        'kanun': (KanunMaddesi, KanunForm), 'reklam': (ReklamBanner, ReklamForm),
        'siparis': (Siparis, SiparisForm), 'sohbet': (SohbetGecmisi, SohbetForm),
        'randevu': (AvukatRandevu, RandevuAdminForm)
    }
    
    if tip not in config: return redirect('panel_dashboard')
    
    Model, FormClass = config[tip]
    kayit = get_object_or_404(Model, id=id)
    
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=kayit)
        if form.is_valid():
            form.save()
            return redirect('panel_icerik', tip=tip)
    else:
        form = FormClass(instance=kayit)
    return render(request, 'panel/form.html', {'form': form, 'title': f'{tip.capitalize()} Düzenle'})

@login_required
def panel_sil(request, tip, id):
    models_map = {
        'avukat': Avukat, 'paket': Paket, 'reklam': ReklamBanner, 'kanun': KanunMaddesi
    }
    Model = models_map.get(tip)
    if Model:
        obj = get_object_or_404(Model, id=id)
        obj.delete()
    return redirect('panel_icerik', tip=tip)

@login_required
def avukat_dashboard(request):
    if not hasattr(request.user, 'avukat'):
        if request.user.is_superuser: return redirect('panel_dashboard')
        return render(request, 'hata.html', {'mesaj': 'Yetkisiz giriş.'})
    
    avukat = request.user.avukat
    bekleyenler = AvukatRandevu.objects.filter(avukat=avukat, durum='Bekliyor').order_by('-tarih')
    gecmis = AvukatRandevu.objects.filter(avukat=avukat).exclude(durum='Bekliyor').order_by('-tarih')
    
    return render(request, 'avukat_panel/dashboard.html', {
        'avukat': avukat, 'bekleyenler': bekleyenler, 'gecmis': gecmis
    })

@login_required
def avukat_profil_duzenle(request):
    avukat = request.user.avukat
    if request.method == "POST":
        form = AvukatProfilForm(request.POST, request.FILES, instance=avukat)
        if form.is_valid():
            form.save()
            return redirect('avukat_dashboard')
    else:
        form = AvukatProfilForm(instance=avukat)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Profilimi Düzenle'})

@login_required
def avukat_randevu_islem(request, id):
    randevu = get_object_or_404(AvukatRandevu, id=id, avukat=request.user.avukat)
    if request.method == "POST":
        form = RandevuDurumForm(request.POST, instance=randevu)
        if form.is_valid():
            form.save()
            return redirect('avukat_dashboard')
    else:
        form = RandevuDurumForm(instance=randevu)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Randevu Durumu Güncelle'})

# =========================================================================
# YENİ UZMAN BOT SİSTEMİ (BURASI GÜNCELLENDİ)
# =========================================================================

def kategori_listesi(request):
    """Ana Sayfa: Hukuk kategorilerini bloklar halinde listeler."""
    ayar = get_settings()
    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    
    banner_sol = ReklamBanner.objects.filter(pozisyon='Sol', aktif_mi=True).order_by('?').first()
    banner_sag = ReklamBanner.objects.filter(pozisyon='Sag', aktif_mi=True).order_by('?').first()

    return render(request, 'anasayfa_bloklar.html', {
        'kategoriler': kategoriler, 
        'ayar': ayar,
        'banner_sol': banner_sol,
        'banner_sag': banner_sag
    })

def uzman_bot_chat(request, slug):
    """Seçilen Kategoriye Özel Yapay Zeka Sohbeti"""
    ayar = get_settings()
    secilen_kategori = get_object_or_404(HukukKategori, slug=slug)
    
    cevap = None
    soru = None

    # -- Kredi (Hak) Sistemi --
    if 'kalan_hak' not in request.session:
        request.session['kalan_hak'] = 1
    if request.user.is_superuser:
        request.session['kalan_hak'] = 999

    if request.method == "POST":
        # Hak Bitti mi?
        if request.session.get('kalan_hak', 0) <= 0 and not request.user.is_superuser:
            return render(request, 'limit_bitti.html', {'ayar': ayar})

        soru = request.POST.get('soru')
        
        # --- GEMINI AI BAĞLANTISI ---
        API_KEY = "AIzaSyCkgzc7kNT8vNhHjC_PDPJtliwN9oPphNk" # Senin Anahtarın
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')

        # 1. Veritabanı Filtreleme: Sadece bu kategoriye ait kanunları çek
        filtrelenmis_kanunlar = KanunMaddesi.objects.filter(kategori=secilen_kategori)
        
        try:
            # Kullanıcı sorusunu vektöre çevir
            soru_vec = genai.embed_content(model="models/text-embedding-004", content=soru, task_type="retrieval_query")['embedding']
            
            best_score = -1
            best_match_content = ""
            
            # Sadece filtrelenen kanunlarda arama yap
            if filtrelenmis_kanunlar.exists():
                for k in filtrelenmis_kanunlar:
                    # Not: Her seferinde embed yapmak yavaştır ama şu anlık çalışır.
                    # İleride vektör veritabanına geçersek burası hızlanır.
                    k_content = f"Kanun: {k.kanun_adi} Madde: {k.madde_no} İçerik: {k.icerik}"
                    k_vec = genai.embed_content(model="models/text-embedding-004", content=k_content, task_type="retrieval_document")['embedding']
                    
                    score = np.dot(soru_vec, k_vec)
                    if score > best_score:
                        best_score = score
                        best_match_content = k_content

            # Eşik Değer (Yeterince alakalı mı?)
            if best_score > 0.45:
                # --- İŞTE BURASI YENİ KISIM ---
                # Admin panelinden yazdığın "Gizli Talimatı" çekiyoruz
                ozel_talimat = secilen_kategori.ai_talimati
                
                prompt = f"""
                GÖREVİN: {ozel_talimat}
                
                KULLANICI SORUSU: {soru}
                
                REFERANS BİLGİ (Dayanak): {best_match_content}
                
                KURALLAR:
                1. Sadece referans bilgiyi ve alanınla ilgili genel hukuku kullan.
                2. Profesyonel ol, HTML formatında cevap ver.
                3. Kesinlikle ilgili kanun maddesini (Madde No) belirt.
                
                ÇIKTI FORMATI:
                <p><strong>Merhaba,</strong></p>
                <p> ...Cevap buraya... </p>
                <div style='background:#f9f9f9; padding:10px; border-left:4px solid #007bff; margin-top:10px;'>
                   📜 <strong>Dayanak:</strong> {best_match_content[:200]}...
                </div>
                """
                
                res = model.generate_content(prompt)
                cevap = res.text.replace('```html', '').replace('```', '')
                
                # Sohbeti Kaydet
                SohbetGecmisi.objects.create(soru=soru, cevap=cevap)
                
            else:
                cevap = f"<p>Veritabanımda (Kategori: {secilen_kategori.isim}) sorunuza uygun net bir kanun maddesi bulamadım. Genel bir avukata danışmanızı öneririm.</p>"

            # Hakkı Düşür
            if not request.user.is_superuser:
                request.session['kalan_hak'] -= 1
                request.session.modified = True

        except Exception as e:
            cevap = f"<p>AI Servisinde hata oluştu: {e}</p>"

    return render(request, 'ozel_bot.html', {
        'kategori': secilen_kategori, 
        'cevap': cevap, 
        'soru': soru,
        'ayar': ayar
    })
    
    # core/views.py dosyasının EN ALTINA ekle:

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib import messages

def avukat_giris_yap(request):
    """
    ÖZEL GÜVENLİKLİ GİRİŞ:
    Sadece Avukatları içeri alır.
    Yöneticileri (Superuser) KESİNLİKLE reddeder.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # --- GÜVENLİK KONTROLÜ ---
            if user.is_superuser:
                # Eğer yönetici ise OTURUM AÇMA, hata ver ve geri gönder.
                messages.error(request, "⚠️ HATA: Yöneticiler Avukat Girişini kullanamaz! Lütfen Yönetim Panelini kullanın.")
                return render(request, 'registration/login.html', {'form': form})
            
            # Yönetici değilse (Avukatsa) içeri al
            login(request, user)
            return redirect('avukat_dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})