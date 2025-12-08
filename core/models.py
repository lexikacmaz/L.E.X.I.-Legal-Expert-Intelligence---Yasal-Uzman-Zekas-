from django.db import models
from django.contrib.auth.models import User
from PIL import Image

# --- SİTE AYARLARI ---
# core/models.py

# --- GENİŞLETİLMİŞ FONT LİSTESİ ---
FONT_SECENEKLERI = [
    ('Inter', 'Inter (Modern & Temiz)'),
    ('Roboto', 'Roboto (Standart & Okunaklı)'),
    ('Open Sans', 'Open Sans (Ferah & Açık)'),
    ('Lato', 'Lato (Yuvarlak & Samimi)'),
    ('Montserrat', 'Montserrat (Geometrik & Güçlü)'),
    ('Raleway', 'Raleway (Zarif & İnce)'),
    ('Poppins', 'Poppins (Popüler & Yuvarlak)'),
    ('Playfair Display', 'Playfair Display (Tırnaklı & Klasik)'),
    ('Merriweather', 'Merriweather (Okuma Odaklı)'),
    ('Lora', 'Lora (Hukuki & Ciddi)'),
    ('Oswald', 'Oswald (Dik & Sıkışık)'),
    ('Rubik', 'Rubik (Yumuşak Köşeli)'),
]

class SiteAyarlari(models.Model):
    site_basligi = models.CharField(max_length=200, default="L.E.X.I.")
    logo = models.ImageField(upload_to='logo/', null=True, blank=True)
    
    # Fontlar
    font_baslik = models.CharField(max_length=100, choices=FONT_SECENEKLERI, default="Inter")
    font_genel = models.CharField(max_length=100, choices=FONT_SECENEKLERI, default="Inter")
    
    # --- ORTAK RENKLER ---
    renk_ana = models.CharField(max_length=20, default="#0071e3", verbose_name="Ana Vurgu Rengi (Mavi vb.)")
    
    # --- LIGHT MODE RENKLERİ ---
    renk_arkaplan_light = models.CharField(max_length=20, default="#f5f5f7", verbose_name="Açık Mod Arkaplan")
    renk_yazi_light = models.CharField(max_length=20, default="#1d1d1f", verbose_name="Açık Mod Yazı")
    renk_kart_light = models.CharField(max_length=20, default="#ffffff", verbose_name="Açık Mod Kart Rengi")
    
    # --- DARK MODE RENKLERİ ---
    renk_arkaplan_dark = models.CharField(max_length=20, default="#202020", verbose_name="Koyu Mod Arkaplan")
    renk_yazi_dark = models.CharField(max_length=20, default="#f5f5f7", verbose_name="Koyu Mod Yazı")
    renk_kart_dark = models.CharField(max_length=20, default="#1c1c1e", verbose_name="Koyu Mod Kart Rengi")

    def __str__(self):
        return "Site Ayarları"

# --- KATEGORİ SİSTEMİ (Chat Bot İçin) ---
class HukukKategori(models.Model):
    isim = models.CharField(max_length=100) # Örn: Aile Hukuku
    slug = models.SlugField(unique=True) # Örn: aile-hukuku
    ikon = models.CharField(max_length=50, default="⚖️") # Emoji
    aciklama = models.TextField(blank=True)
    ai_talimati = models.TextField(help_text="Bu kategorideki AI botuna verilecek özel gizli talimat.")
    aktif_mi = models.BooleanField(default=True)

    def __str__(self):
        return self.isim

# --- AVUKAT MODELİ (GÜNCELLENDİ: Eposta ve Telefon Eklendi) ---
class Avukat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    isim = models.CharField(max_length=100)
    resim = models.ImageField(upload_to='avukatlar/', null=True, blank=True)
    uzmanlik = models.CharField(max_length=100)
    ozet = models.TextField()
    
    # EKSİK OLAN ALANLAR EKLENDİ:
    eposta = models.EmailField(max_length=254, null=True, blank=True)
    telefon = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.isim

# --- REKLAM BANNER (Genişlik/Yükseklik Dahil) ---
class ReklamBanner(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Reklam Adı (Örn: Sol Taraf)")
    gorsel = models.ImageField(upload_to='reklamlar/', verbose_name="Reklam Görseli")
    link = models.URLField(blank=True, null=True, verbose_name="Tıklanınca Gideceği Link")
    
    pozisyon = models.CharField(
        max_length=10, 
        choices=[('Sol', 'Sol'), ('Sag', 'Sag')], 
        verbose_name="Sayfadaki Yeri"
    )
    
    # Kullanıcıya göstermek için varsayılan değerler
    genislik = models.PositiveIntegerField(default=160, verbose_name="Genişlik (px)", editable=False)
    yukseklik = models.PositiveIntegerField(default=600, verbose_name="Yükseklik (px)", editable=False)
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Sitede Görünsün mü?")

    def save(self, *args, **kwargs):
        # Önce kaydet (Dosya oluşsun)
        super().save(*args, **kwargs)

        if self.gorsel:
            img_path = self.gorsel.path
            img = Image.open(img_path)

            # Hedef boyutlar (Standart Skyscraper Reklamı)
            target_size = (160, 600)

            # Eğer boyut farklıysa yeniden boyutlandır
            if img.height != 600 or img.width != 160:
                # Resmi bozmadan sığdırmak yerine, alanı tam doldurması için 'resize' kullanıyoruz.
                # İstersen 'thumbnail' ile oran koruyarak da yapabiliriz ama reklam alanları genelde tam dolmalıdır.
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                img.save(img_path)

    def __str__(self):
        return f"{self.isim} ({self.pozisyon})"

# --- KANUN MADDELERİ ---
class KanunMaddesi(models.Model):
    kategori = models.ForeignKey(HukukKategori, on_delete=models.SET_NULL, null=True, blank=True)
    kanun_adi = models.CharField(max_length=200) # Örn: Türk Borçlar Kanunu
    madde_no = models.CharField(max_length=50) # Örn: Madde 12
    icerik = models.TextField()

    def __str__(self):
        return f"{self.kanun_adi} - {self.madde_no}"

# --- EMSAL KARARLAR ---
class EmsalKarar(models.Model):
    baslik = models.CharField(max_length=200)
    ozet = models.TextField()
    dosya_linki = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.baslik

# --- HİZMET PAKETLERİ ---
class Paket(models.Model):
    isim = models.CharField(max_length=100)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    aciklama = models.TextField()
    ozellikler = models.TextField(help_text="Her satıra bir özellik yazın")

    def __str__(self):
        return self.isim

# --- SİPARİŞLER ---
class Siparis(models.Model):
    paket = models.ForeignKey(Paket, on_delete=models.CASCADE)
    ad_soyad = models.CharField(max_length=100)
    telefon = models.CharField(max_length=20)
    eposta = models.EmailField()
    notlar = models.TextField(blank=True)
    odendi_mi = models.BooleanField(default=False)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ad_soyad} - {self.paket.isim}"

# --- SOHBET GEÇMİŞİ ---
class SohbetGecmisi(models.Model):
    soru = models.TextField()
    cevap = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.soru[:50]

# --- AVUKAT RANDEVU ---
class AvukatRandevu(models.Model):
    avukat = models.ForeignKey(Avukat, on_delete=models.CASCADE)
    ad_soyad = models.CharField(max_length=100)
    telefon = models.CharField(max_length=20)
    eposta = models.EmailField()
    mesaj = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)
    durum = models.CharField(
        max_length=20, 
        choices=[('Bekliyor', 'Bekliyor'), ('Tamamlandı', 'Tamamlandı'), ('İptal', 'İptal')],
        default='Bekliyor'
    )

    def __str__(self):
        return f"{self.ad_soyad} -> {self.avukat.isim}"
    
    # models.py içine ekle

class VeriGuncellemeLog(models.Model):
    kategori = models.ForeignKey(HukukKategori, on_delete=models.CASCADE)
    islem_tarihi = models.DateTimeField(auto_now_add=True)
    eklenen_veri_sayisi = models.IntegerField(default=0)
    basarili_mi = models.BooleanField(default=True)
    hata_mesaji = models.TextField(blank=True, null=True)

    def __str__(self):
        durum = "✅" if self.basarili_mi else "❌"
        return f"{durum} - {self.kategori.isim} - {self.islem_tarihi.strftime('%d.%m.%Y')}"

class SistemBildirimi(models.Model):
    """Admin'e (Sana) gidecek bildirimler"""
    baslik = models.CharField(max_length=200)
    mesaj = models.TextField()
    okundu_mu = models.BooleanField(default=False)
    tarih = models.DateTimeField(auto_now_add=True)
    
    # Kritik seviye: Bilgi, Uyarı, Acil
    seviye = models.CharField(max_length=20, choices=[('info', 'Bilgi'), ('warning', 'Uyarı'), ('danger', 'Acil')], default='info')

    def __str__(self):
        return self.baslik
    
    # core/models.py en altına ekle:

class BetaKullanici(models.Model):
    kullanici_adi = models.CharField(max_length=50, unique=True)
    sifre = models.CharField(max_length=50) # Basit beta olduğu için şifreli tutmuyoruz, direkt görüp yönet diye.
    aktif_mi = models.BooleanField(default=True)
    notlar = models.TextField(blank=True, help_text="Bu hesabı kime verdin?")

    def __str__(self):
        return self.kullanici_adi