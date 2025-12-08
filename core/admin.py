from django.contrib import admin
from .models import BetaKullanici
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, HukukKategori, EmsalKarar , BetaKullanici ,
)

# --- SİTE AYARLARI ---
@admin.register(SiteAyarlari)
class SiteAyarlariAdmin(admin.ModelAdmin):
    list_display = ('site_basligi', 'renk_ana')

# --- KATEGORİ ---
@admin.register(HukukKategori)
class HukukKategoriAdmin(admin.ModelAdmin):
    list_display = ('isim', 'slug', 'aktif_mi')
    prepopulated_fields = {'slug': ('isim',)}

# --- AVUKAT ---
@admin.register(Avukat)
class AvukatAdmin(admin.ModelAdmin):
    list_display = ('isim', 'uzmanlik', 'telefon', 'eposta')
    search_fields = ('isim', 'uzmanlik')

# --- REKLAM BANNER (GÜNCELLENDİ) ---
@admin.register(ReklamBanner)
class ReklamBannerAdmin(admin.ModelAdmin):
    # Yeni eklenen genişlik ve yükseklik alanlarını buraya da ekledik
    list_display = ('isim', 'pozisyon', 'genislik', 'yukseklik', 'aktif_mi')
    list_filter = ('pozisyon', 'aktif_mi')

# --- KANUN MADDESİ ---
@admin.register(KanunMaddesi)
class KanunAdmin(admin.ModelAdmin):
    # 'kanun_no' alanı modelde olmadığı için sildik
    list_display = ('kanun_adi', 'madde_no', 'kategori')
    search_fields = ('kanun_adi', 'madde_no', 'icerik')
    list_filter = ('kategori',)

# --- EMSAL KARAR (DÜZELTİLDİ) ---
@admin.register(EmsalKarar)
class EmsalKararAdmin(admin.ModelAdmin):
    # Modelde olmayan (daire, esas_no vb.) alanları sildik.
    # Sadece var olan alanları ekledik.
    list_display = ('baslik', 'dosya_linki')
    search_fields = ('baslik', 'ozet')

# --- DİĞERLERİ ---
@admin.register(Paket)
class PaketAdmin(admin.ModelAdmin):
    list_display = ('isim', 'fiyat')

@admin.register(Siparis)
class SiparisAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'paket', 'odendi_mi', 'tarih')
    list_filter = ('odendi_mi',)

@admin.register(SohbetGecmisi)
class SohbetAdmin(admin.ModelAdmin):
    list_display = ('soru_ozet', 'tarih')
    
    def soru_ozet(self, obj):
        return obj.soru[:50] + "..." if obj.soru else ""

@admin.register(AvukatRandevu)
class RandevuAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'avukat', 'tarih', 'durum')
    list_filter = ('durum', 'avukat')
    
class BetaKullaniciAdmin(admin.ModelAdmin):
    list_display = ('kullanici_adi', 'email', 'onaylandi', 'olusturulma_tarihi') # Listede neler görünsün
    list_filter = ('onaylandi',) # Onaylı/Onaysız diye filtreleme çubuğu ekler
    list_editable = ('onaylandi',) # İçeri girmeden direkt listeden tik atıp onaylamanı sağlar
    search_fields = ('kullanici_adi', 'email')

admin.site.register(BetaKullanici, BetaKullaniciAdmin)

