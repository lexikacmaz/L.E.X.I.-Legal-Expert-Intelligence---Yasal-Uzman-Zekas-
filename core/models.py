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

    class Meta:
        verbose_name = "Site Ayarları"
        verbose_name_plural = "Site Ayarları"

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

    class Meta:
        verbose_name = "Hukuk Kategorisi"
        verbose_name_plural = "Hukuk Kategorileri"

    def __str__(self):
        return self.isim

# --- AVUKAT MODELİ ---
class Avukat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    isim = models.CharField(max_length=100)
    resim = models.ImageField(upload_to='avukatlar/', null=True, blank=True)
    uzmanlik = models.CharField(max_length=100)
    ozet = models.TextField()
    
    eposta = models.EmailField(max_length=254, null=True, blank=True)
    telefon = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "Avukat"
        verbose_name_plural = "Avukatlar"

    def __str__(self):
        return self.isim

# --- REKLAM BANNER ---
class ReklamBanner(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Reklam Adı (Örn: Sol Taraf)")
    gorsel = models.ImageField(upload_to='reklamlar/', verbose_name="Reklam Görseli")
    link = models.URLField(blank=True, null=True, verbose_name="Tıklanınca Gideceği Link")
    
    pozisyon = models.CharField(
        max_length=10, 
        choices=[('Sol', 'Sol'), ('Sag', 'Sag')], 
        verbose_name="Sayfadaki Yeri"
    )
    
    genislik = models.PositiveIntegerField(default=160, verbose_name="Genişlik (px)", editable=False)
    yukseklik = models.PositiveIntegerField(default=600, verbose_name="Yükseklik (px)", editable=False)
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Sitede Görünsün mü?")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.gorsel:
            try:
                img_path = self.gorsel.path
                img = Image.open(img_path)
                target_size = (160, 600)
                if img.height != 600 or img.width != 160:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                    img.save(img_path)
            except Exception as e:
                print(f"Resim işlenirken hata: {e}")

    class Meta:
        verbose_name = "Reklam Banner"
        verbose_name_plural = "Reklam Bannerları"

    def __str__(self):
        return f"{self.isim} ({self.pozisyon})"

# --- KANUN MADDELERİ ---
class KanunMaddesi(models.Model):
    kategori = models.ForeignKey(HukukKategori, on_delete=models.SET_NULL, null=True, blank=True)
    kanun_adi = models.CharField(max_length=200) # Örn: Türk Borçlar Kanunu
    madde_no = models.CharField(max_length=50) # Örn: Madde 12
    icerik = models.TextField()

    class Meta:
        verbose_name = "Kanun Maddesi"
        verbose_name_plural = "Kanun Maddeleri"

    def __str__(self):
        return f"{self.kanun_adi} - {self.madde_no}"

# --- DAVA ANALİZLERİ (TURA ENTEGRASYONU İÇİN GÜNCELLENDİ) ---
# Eski 'EmsalKarar' modelini 'DavaAnalizi' olarak güçlendirdik.
class DavaAnalizi(models.Model):
    kategori = models.ForeignKey(HukukKategori, on_delete=models.CASCADE, related_name='davalar', null=True, blank=True)
    
    # Kimlik Bilgileri
    daire = models.CharField(max_length=100, verbose_name="Daire", blank=True)
    esas_no = models.CharField(max_length=50, verbose_name="Esas No", blank=True)
    karar_no = models.CharField(max_length=50, verbose_name="Karar No", blank=True)
    karar_tarihi = models.CharField(max_length=50, verbose_name="Tarih", blank=True)
    
    # İçerik ve Analiz (TURA JSON'dan gelecek)
    baslik = models.CharField(max_length=255, verbose_name="Dava Başlığı") # EmsalKarar uyumu için
    ozet_hikaye = models.TextField(verbose_name="Özet Hikaye", blank=True)
    hukuki_ilke = models.TextField(verbose_name="Hukuki İlke", blank=True)
    kritik_uyari = models.TextField(verbose_name="Kritik Uyarı", blank=True)
    hukum_sonucu = models.CharField(max_length=100, verbose_name="Sonuç", blank=True)
    
    # Etiketler (JSON formatında saklanır: ["Kira", "Tahliye"])
    konu_etiketleri = models.JSONField(default=list, verbose_name="Etiketler", blank=True)
    
    # Sistem
    dosya_adi = models.CharField(max_length=255, unique=True, verbose_name="Kaynak Dosya", blank=True, null=True)
    dosya_linki = models.URLField(blank=True, null=True) # Eski uyumluluk için
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dava Analizi (AI)"
        verbose_name_plural = "Dava Analizleri (AI)"
        # Aynı esas/karar tekrar girilmesin
        unique_together = ('daire', 'esas_no', 'karar_no')

    def __str__(self):
        if self.esas_no and self.karar_no:
            return f"{self.daire} - E:{self.esas_no} K:{self.karar_no}"
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

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"

    def __str__(self):
        return f"{self.ad_soyad} - {self.paket.isim}"

# --- SOHBET GEÇMİŞİ ---
class SohbetGecmisi(models.Model):
    soru = models.TextField()
    cevap = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sohbet Kaydı"
        verbose_name_plural = "Sohbet Geçmişi"

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

    class Meta:
        verbose_name = "Randevu"
        verbose_name_plural = "Randevular"

    def __str__(self):
        return f"{self.ad_soyad} -> {self.avukat.isim}"

# --- SİSTEM LOGLARI ---
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

    class Meta:
        verbose_name = "Sistem Bildirimi"
        verbose_name_plural = "Sistem Bildirimleri"

    def __str__(self):
        return self.baslik

# --- BETA KULLANICI ---
class BetaKullanici(models.Model):
    kullanici_adi = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    sifre = models.CharField(max_length=100)
    onaylandi = models.BooleanField(default=False)
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Beta Kullanıcı Başvurusu"
        verbose_name_plural = "Beta Kullanıcı Başvuruları"

    def __str__(self):
        return self.email