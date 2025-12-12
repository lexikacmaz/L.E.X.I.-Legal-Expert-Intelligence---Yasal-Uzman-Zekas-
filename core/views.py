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
# DÜZELTME: Veritabanı yolu sabitlendi
CHROMA_PATH = "./lexi_beyin_db"

try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    print("✅ ChromaDB Başlatıldı.")
except Exception as e:
    chroma_client = None
    print(f"⚠️ ChromaDB Hatası: {e}")

# --- API KEY AYARLARI ---
API_KEY = getattr(settings, 'GOOGLE_API_KEY', None)

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        print(f"✅ AI Anahtarı Yüklendi.")
    except Exception as e:
        print(f"❌ AI Yapılandırma Hatası: {e}")
else:
    print("❌ HATA: Google API Anahtarı Bulunamadı! settings.py dosyasını kontrol edin.")

EMBEDDING_MODEL = "models/text-embedding-004"

def get_settings():
    ayar, created = SiteAyarlari.objects.get_or_create(id=1)
    return ayar

# ==========================================
# --- BETA SİSTEMİ ---
# ==========================================
def beta_basvuru(request):
    if request.method == 'POST':
        form = BetaBasvuruForm(request.POST)
        if form.is_valid():
            yeni_kullanici = form.save(commit=False)
            yeni_kullanici.onaylandi = False 
            yeni_kullanici.save()
            messages.success(request, 'Başvurunuz alındı! Yönetici onayladığında giriş yapabileceksiniz.')
            return redirect('beta_giris')
    else: form = BetaBasvuruForm()
    return render(request, 'beta_basvuru.html', {'form': form})

def beta_giris_yap(request):
    if request.method == 'POST':
        kadi = request.POST.get('kullanici_adi')
        sifre = request.POST.get('sifre')
        admin_user = authenticate(request, username=kadi, password=sifre)
        if admin_user is not None and admin_user.is_superuser:
            login(request, admin_user)
            messages.success(request, f'Yönetici girişi başarılı. Hoşgeldin {kadi} 👑')
            return redirect('/') 
        beta_user = BetaKullanici.objects.filter(kullanici_adi=kadi, sifre=sifre).first()
        if beta_user:
            if beta_user.onaylandi:
                request.session['beta_kullanici_id'] = beta_user.id
                messages.success(request, f'Giriş başarılı. Hoşgeldin {beta_user.kullanici_adi}')
                return redirect('/')
            else: messages.error(request, 'Hesabınız henüz onaylanmadı.')
        else: messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
    return render(request, 'beta_giris.html')

# ==========================================
# --- AI MOTORU ---
# ==========================================

def generate_safe_content(prompt):
    model_listesi = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.5-flash",
        "gemini-flash-latest"
    ]
    
    system_instruction = """
    Sen bir Hukuk Asistanısın.
    GÖREVİN: SADECE sana verilen 'VERİLER' kısmındaki bilgileri kullanarak cevap vermek.
    Eğer veri yoksa veya yetersizse dürüstçe 'Bilgi bulunamadı' de.
    Cevabı HTML formatında (h3, p, ul, li) ver.
    """

    for model_name in model_listesi:
        try:
            print(f"🔄 Model deneniyor: {model_name}...")
            model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=8000,
                    temperature=0.3
                )
            )
            if response and response.text:
                print(f"✅ BAŞARILI: {model_name} cevap verdi.")
                return response.text
        except Exception as e:
            print(f"❌ MODEL HATASI ({model_name}): {str(e)}")
            continue

    return "<h3>⚠️ Servis Hatası</h3><p>Modellere erişilemedi. Lütfen daha sonra tekrar deneyin.</p>"

def home(request):
    if not request.user.is_superuser and 'beta_kullanici_id' not in request.session:
        return redirect('beta_giris')

    ayar = get_settings()
    banner_sol = ReklamBanner.objects.filter(pozisyon='Sol', aktif_mi=True).order_by('?').first()
    banner_sag = ReklamBanner.objects.filter(pozisyon='Sag', aktif_mi=True).order_by('?').first()
    kategoriler = HukukKategori.objects.filter(aktif_mi=True)
    cevap = request.session.pop('ai_cevap', None)
    
    ilk_kategori = HukukKategori.objects.filter(aktif_mi=True).first()
    secilen_bot_slug = ilk_kategori.slug if ilk_kategori else "genel"
    
    if 'kalan_hak' not in request.session: request.session['kalan_hak'] = 1
    if request.user.is_superuser: request.session['kalan_hak'] = 999
    kalan_hak = request.session['kalan_hak']

    if request.method == "POST":
        soru = request.POST.get("soru")
        secilen_bot_slug = request.POST.get("bot_slug")

        if kalan_hak <= 0 and not request.user.is_superuser:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Limitiniz doldu.'}, status=403)
            return render(request, 'limit_bitti.html', {'ayar': ayar})

        try:
            context_text = ""
            
            # --- RAG SORGUSU ---
            if chroma_client:
                # DÜZELTME: Koleksiyon adı emsal_kararlar olarak sabitlendi
                collection_name = "emsal_kararlar"
                try:
                    collection = chroma_client.get_collection(name=collection_name)
                    print(f"📂 Koleksiyon bulundu: {collection_name}")
                    
                    # DÜZELTME: Sadece çalışan model (text-embedding-004) kullanılıyor
                    soru_vec = genai.embed_content(model="models/text-embedding-004", content=soru, task_type="retrieval_query")['embedding']

                    results = collection.query(query_embeddings=[soru_vec], n_results=5)
                    
                    if 'documents' in results and results['documents'] and results['documents'][0]:
                        bulunan_metinler = results['documents'][0]
                        context_text = "\n\n".join(bulunan_metinler)
                        print(f"📄 {len(bulunan_metinler)} adet doküman bulundu.")
                    else:
                        print("⚠️ Doküman bulunamadı.")

                except Exception as db_err:
                    print(f"❌ Veritabanı Hatası: {db_err}")

            # --- PROMPT ---
            if context_text:
                prompt = f"""
                SORU: "{soru}"
                VERİLER: {context_text}
                GÖREV: Sadece VERİLER'i kullanarak cevapla.
                """
                cevap = generate_safe_content(prompt)
            else:
                cevap = "<h3>🚫 Bilgi Bulunamadı</h3><p>Veritabanında kayıt yok.</p>"

            cevap = cevap.replace('```html', '').replace('```', '')
            SohbetGecmisi.objects.create(soru=soru, cevap=cevap)
            
            if not request.user.is_superuser and "Bilgi Bulunamadı" not in cevap:
                request.session['kalan_hak'] -= 1
                request.session.modified = True
                kalan_hak = request.session['kalan_hak']

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'cevap': cevap, 'kalan_hak': kalan_hak})
            
            request.session['ai_cevap'] = cevap
            return redirect('home')

        except Exception as e:
            print(f"❌ GENEL HATA: {e}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest': return JsonResponse({'error': str(e)}, status=500)
            request.session['ai_cevap'] = f"Sistem Hatası: {str(e)}"
            return redirect('home')

    return render_home(request, ayar, cevap, kategoriler, banner_sol, banner_sag, secilen_bot_slug, kalan_hak)

def render_home(request, ayar, cevap, kategoriler, b_sol, b_sag, bot, hak):
    return render(request, 'home.html', {
        'ayar': ayar, 'cevap': cevap, 'kategoriler': kategoriler,
        'banner_sol': b_sol, 'banner_sag': b_sag,
        'secilen_bot': bot, 'kalan_hak': hak,
    })

# --- DİĞER FONKSİYONLAR ---
def avukatlar(request): return render(request, 'avukatlar.html', {'ayar': get_settings(), 'avukatlar': Avukat.objects.all()})
def paketler(request): return render(request, 'paketler.html', {'ayar': get_settings(), 'paketler': Paket.objects.all()})
def yasal(request): return render(request, 'legal.html', {'ayar': get_settings()})
def satin_al(request, paket_id):
    secilen_paket = get_object_or_404(Paket, id=paket_id)
    if request.method == "POST":
        form = SiparisForm(request.POST)
        if form.is_valid():
            siparis = form.save(commit=False); siparis.paket = secilen_paket; siparis.save()
            return redirect('odeme_sayfasi', siparis_id=siparis.id)
    else: form = SiparisForm()
    return render(request, 'satin_al.html', {'form': form, 'paket': secilen_paket, 'ayar': get_settings()})
def odeme_sayfasi(request, siparis_id):
    siparis = get_object_or_404(Siparis, id=siparis_id)
    if request.method == "POST": siparis.odendi_mi = True; siparis.save(); return redirect('siparis_basarili')
    return render(request, 'odeme.html', {'siparis': siparis, 'ayar': get_settings()})
def siparis_basarili(request): return render(request, 'basarili.html', {'ayar': get_settings()})
def randevu_al(request, avukat_id):
    secilen_avukat = get_object_or_404(Avukat, id=avukat_id)
    if request.method == "POST":
        form = RandevuForm(request.POST)
        if form.is_valid(): randevu = form.save(commit=False); randevu.avukat = secilen_avukat; randevu.save(); return render(request, 'basarili.html', {'ayar': get_settings(), 'mesaj': 'Talebiniz iletildi.'})
    else: form = RandevuForm()
    return render(request, 'randevu.html', {'form': form, 'avukat': secilen_avukat, 'ayar': get_settings()})
@login_required(login_url='/admin/login/') 
def panel_dashboard(request): return render(request, 'panel/dashboard.html') if request.user.is_superuser else redirect('avukat_dashboard')
@login_required
def panel_ayarlar(request):
    ayar = get_settings()
    if request.method=="POST": form=AyarForm(request.POST, request.FILES, instance=ayar); form.save() if form.is_valid() else None; return redirect('panel_dashboard')
    return render(request, 'panel/form.html', {'form': AyarForm(instance=ayar), 'title': 'Site Ayarları'})
@login_required
def panel_icerik(request, tip):
    models={ 'avukat':Avukat,'paket':Paket,'kanun':KanunMaddesi,'reklam':ReklamBanner,'siparis':Siparis,'sohbet':SohbetGecmisi,'randevu':AvukatRandevu,'beta':BetaKullanici }
    return render(request, 'panel/liste.html', {'items': models[tip].objects.all().order_by('-id') if tip in models else [], 'tip': tip})
@login_required
def panel_ekle(request, tip):
    forms={'avukat':AvukatForm,'paket':PaketForm,'reklam':ReklamForm,'kanun':KanunForm,'beta':BetaKullaniciForm}
    if request.method=="POST": form=forms[tip](request.POST, request.FILES); form.save() if form.is_valid() else None; return redirect('panel_icerik', tip=tip)
    return render(request, 'panel/form.html', {'form': forms[tip](), 'title': f'Yeni {tip} Ekle'})
@login_required
def panel_duzenle(request, tip, id):
    conf={'avukat':(Avukat,AvukatForm),'paket':(Paket,PaketForm),'kanun':(KanunMaddesi,KanunForm),'reklam':(ReklamBanner,ReklamForm),'siparis':(Siparis,SiparisForm),'sohbet':(SohbetGecmisi,SohbetForm),'randevu':(AvukatRandevu,RandevuAdminForm),'beta':(BetaKullanici,BetaKullaniciForm)}
    M,F=conf[tip]; obj=get_object_or_404(M,id=id)
    if request.method=="POST": form=F(request.POST, request.FILES, instance=obj); form.save() if form.is_valid() else None; return redirect('panel_icerik', tip=tip)
    return render(request, 'panel/form.html', {'form': F(instance=obj), 'title': f'Düzenle'})
@login_required
def panel_sil(request, tip, id):
    models={'avukat':Avukat,'paket':Paket,'reklam':ReklamBanner,'kanun':KanunMaddesi,'beta':BetaKullanici}
    get_object_or_404(models[tip],id=id).delete() if tip in models else None; return redirect('panel_icerik', tip=tip)
def avukat_giris_yap(request):
    if request.method=='POST': 
        form=AuthenticationForm(request,data=request.POST)
        if form.is_valid(): login(request,form.get_user()); return redirect('avukat_dashboard')
    return render(request, 'registration/login.html', {'form': AuthenticationForm()})
def cikis_yap(request): logout(request); return redirect('home')
@login_required
def avukat_dashboard(request):
    if not hasattr(request.user,'avukat'): return redirect('panel_dashboard') if request.user.is_superuser else render(request,'hata.html',{'mesaj':'Yetkisiz'})
    av=request.user.avukat; tum=AvukatRandevu.objects.filter(avukat=av)
    return render(request,'avukat_panel/dashboard.html',{'avukat':av,'bekleyenler':tum.filter(durum='Bekliyor'),'gecmis':tum.exclude(durum='Bekliyor'),'istatistik':{'toplam':tum.count()}})
@login_required
def avukat_profil_duzenle(request):
    av=request.user.avukat
    if request.method=="POST": form=AvukatProfilForm(request.POST,request.FILES,instance=av); form.save() if form.is_valid() else None; return redirect('avukat_dashboard')
    return render(request,'panel/form.html',{'form':AvukatProfilForm(instance=av),'title':'Profil'})
@login_required
def avukat_randevu_islem(request, id):
    r=get_object_or_404(AvukatRandevu,id=id,avukat=request.user.avukat)
    if request.method=="POST": form=RandevuDurumForm(request.POST,instance=r); form.save() if form.is_valid() else None; return redirect('avukat_dashboard')
    return render(request,'panel/form.html',{'form':RandevuDurumForm(instance=r),'title':'Randevu'})
def kategori_listesi(request): return redirect('home')
def uzman_bot_chat(request, slug): return redirect('home')