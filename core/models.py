from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class SiteAyarlari(models.Model):
    # GENEL
    site_basligi = models.CharField(max_length=100, default="LegalAI", verbose_name="Site Başlığı (Sol Üstte Yazan)")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Site Logosu")
    
    # RENKLER (AÇIKLAMALI)
    renk_ana = models.CharField(
        max_length=20, 
        default="#003366", 
        verbose_name="Ana Renk (Çizgiler, Kenarlıklar, Vurgular)"
    )
    
    renk_arkaplan = models.CharField(
        max_length=20, 
        default="#FDFBF7", 
        verbose_name="Tüm Sayfa Arka Plan Rengi"
    )
    
    renk_menu_bg = models.CharField(
        max_length=20, 
        default="#ffffff", 
        verbose_name="Üst Menü Arka Planı (Navbar)"
    )

    renk_yazi_baslik = models.CharField(
        max_length=20, 
        default="#003366", 
        verbose_name="Büyük Başlık Rengi (H1, H2)"
    )
    
    renk_yazi_genel = models.CharField(
        max_length=20, 
        default="#333333", 
        verbose_name="Genel Yazı Rengi (Paragraflar)"
    )
    
    renk_buton = models.CharField(
        max_length=20, 
        default="#003366", 
        verbose_name="Buton Rengi (Satın Al, Gönder)"
    )
    
    # SOHBET KUTUSU RENKLERİ
    renk_ai_balon = models.CharField(
        max_length=20, 
        default="#ffffff", 
        verbose_name="Yapay Zeka Cevap Kutusu Rengi"
    )
    
    renk_user_balon = models.CharField(
        max_length=20, 
        default="#f0f0f0", 
        verbose_name="Kullanıcı Mesaj Balonu Rengi"
    )
    
    renk_input_bg = models.CharField(
        max_length=20, 
        default="#ffffff", 
        verbose_name="Soru Yazma Kutusu (Input) Rengi"
    )
    
    # FONTLAR
    FONT_SECENEKLERI = [
        ('Times New Roman', 'Times New Roman (Klasik)'),
        ('Playfair Display', 'Playfair Display (Elit & Şık)'),
        ('Merriweather', 'Merriweather (Okunaklı Kitap Havası)'),
        ('Lora', 'Lora (Hukuki & Zarif)'),
        ('Segoe UI', 'Segoe UI (Modern Standart)'),
        ('Roboto', 'Roboto (Google Standardı - Net)'),
        ('Open Sans', 'Open Sans (Ferah & Açık)'),
        ('Montserrat', 'Montserrat (Güçlü Başlıklar İçin)'),
        ('Poppins', 'Poppins (Geometrik & Yeni Nesil)'),
        ('Oswald', 'Oswald (Dikkat Çekici Uzun)'),
    ]
    font_baslik = models.CharField(max_length=50, choices=FONT_SECENEKLERI, default='Playfair Display', verbose_name="Başlık Yazı Tipi")
    font_genel = models.CharField(max_length=50, choices=FONT_SECENEKLERI, default='Open Sans', verbose_name="Genel Yazı Tipi")

    def __str__(self):
        return "Site Ayarları"

# Diğer Modeller Aynen Kalıyor (Avukat, Paket vb.)
class Avukat(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Kullanıcı Hesabı")
    isim = models.CharField(max_length=100)
    uzmanlik = models.CharField(max_length=100)
    resim = models.ImageField(upload_to='avukatlar/', blank=True, null=True)
    ozet = models.TextField(blank=True, verbose_name="Biyografi")
    def __str__(self):
        return self.isim

class Paket(models.Model):
    isim = models.CharField(max_length=100)
    fiyat = models.CharField(max_length=50)
    ozellikler = models.TextField()
    def __str__(self): return self.isim

class Siparis(models.Model):
    paket = models.ForeignKey(Paket, on_delete=models.CASCADE)
    ad_soyad = models.CharField(max_length=100)
    telefon = models.CharField(max_length=20)
    email = models.EmailField()
    adres = models.TextField(blank=True)
    tarih = models.DateTimeField(auto_now_add=True)
    odendi_mi = models.BooleanField(default=False)
    def __str__(self): return f"{self.ad_soyad} - {self.paket.isim}"
    

# 1. SOHBET KAYITLARI (Yapay Zeka ile Konuşmalar)
class SohbetGecmisi(models.Model):
    soru = models.TextField(verbose_name="Kullanıcı Sorusu")
    cevap = models.TextField(verbose_name="AI Cevabı")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    def __str__(self):
        return f"{self.soru[:50]}..."

# 2. AVUKAT RANDEVULARI
class AvukatRandevu(models.Model):
    avukat = models.ForeignKey(Avukat, on_delete=models.CASCADE, verbose_name="Seçilen Avukat")
    ad_soyad = models.CharField(max_length=100, verbose_name="Müşteri Adı")
    telefon = models.CharField(max_length=20, verbose_name="Telefon")
    mesaj = models.TextField(verbose_name="Konuşulacak Konu/Not", blank=True)
    tarih = models.DateTimeField(auto_now_add=True)
    durum = models.CharField(
        max_length=20, 
        default='Bekliyor', 
        choices=[('Bekliyor', 'Bekliyor'), ('Görüşüldü', 'Görüşüldü'), ('İptal', 'İptal')]
    )

    def __str__(self):
        return f"{self.ad_soyad} - {self.avukat.isim}"
    
    # core/models.py EN ALTINA EKLE:

class ReklamBanner(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Reklam Adı (Örn: Coca Cola)")
    
    # BURAYA help_text EKLEDİK:
    resim = models.ImageField(
        upload_to='reklamlar/', 
        verbose_name="Banner Resmi",
        help_text="📢 ÖNERİLEN BOYUT: Genişlik 200px x Yükseklik 600px (Dikey Resim). Farklı boyutta yüklerseniz tasarım bozulabilir."
    )
    
    link = models.URLField(verbose_name="Tıklayınca Gideceği Link", blank=True)
    
    POZISYONLAR = [('Sol', 'Sol Taraf'), ('Sag', 'Sağ Taraf')]
    pozisyon = models.CharField(max_length=10, choices=POZISYONLAR, default='Sol')
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")

    def __str__(self):
        return f"{self.isim} ({self.pozisyon})"
    
    from django.db import models

# core/models.py dosyasında HukukKategori modelini güncelle:

class HukukKategori(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Link (Otomatik)")
    
    # --- YENİ EKLENEN ALANLAR ---
    ikon = models.CharField(max_length=20, default="⚖️", verbose_name="İkon (Emoji)")
    aciklama = models.TextField(max_length=300, verbose_name="Kart Açıklaması", default="Bu alandaki kanun ve emsal kararlarla eğitilmiş uzman asistan.")
    
    # Botun kişiliğini buradan yöneteceksin!
    ai_talimati = models.TextField(
        verbose_name="AI Gizli Talimatı (Prompt)", 
        default="Sen bu alanda uzman, yardımsever bir hukuk asistanısın. Kanun maddelerine dayanarak cevap ver.",
        help_text="Örn: 'Sen sert mizaçlı bir ceza avukatısın' veya 'Sen çok açıklayıcı bir kira uzmanısın' gibi."
    )
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Sitede Göster")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.isim)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.isim

class KanunMaddesi(models.Model):
    # Mevzuat.gov.tr'den gelecek veriler
    kategori = models.ForeignKey(HukukKategori, on_delete=models.CASCADE)
    kanun_no = models.CharField(max_length=20) # Örn: 5237
    kanun_adi = models.CharField(max_length=200) # Örn: Türk Ceza Kanunu
    madde_no = models.CharField(max_length=20) # Örn: Madde 1
    icerik = models.TextField() # Maddenin tamamı
    konu = models.CharField(max_length=200)
    def __str__(self): return self.madde_no
    
    def __str__(self):
        return f"{self.kanun_adi} - {self.madde_no}"

class EmsalKarar(models.Model):
    # Yargitay.gov.tr'den gelecek veriler
    kategori = models.ForeignKey(HukukKategori, on_delete=models.CASCADE)
    daire = models.CharField(max_length=100) # Örn: 3. Hukuk Dairesi
    esas_no = models.CharField(max_length=50)
    karar_no = models.CharField(max_length=50)
    tarih = models.DateField(null=True, blank=True)
    ozet = models.TextField() # Kararın özeti
    tam_metin = models.TextField() # Kararın tamamı (KVKK temizlenmiş)

    def __str__(self):
        return f"{self.daire} - {self.esas_no}/{self.karar_no}"