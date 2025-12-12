from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteAyarlari, 
    HukukKategori, 
    Avukat, 
    ReklamBanner, 
    KanunMaddesi, 
    DavaAnalizi,  # Yeni Model (EmsalKarar yerine)
    Paket, 
    Siparis, 
    SohbetGecmisi, 
    AvukatRandevu,
    VeriGuncellemeLog,
    SistemBildirimi,
    BetaKullanici
)

# --- SİTE AYARLARI ---
@admin.register(SiteAyarlari)
class SiteAyarlariAdmin(admin.ModelAdmin):
    list_display = ('site_basligi', 'renk_ana', 'font_genel')
    
    # Sadece tek bir kayıt olmasına izin verelim
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

# --- DAVA ANALİZLERİ (AI & TURA) ---
@admin.register(DavaAnalizi)
class DavaAnaliziAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'kategori', 'karar_tarihi', 'baslik_goster')
    list_filter = ('kategori', 'daire')
    search_fields = ('baslik', 'esas_no', 'karar_no', 'ozet_hikaye', 'hukuki_ilke')
    readonly_fields = ('created_at',)
    
    def baslik_goster(self, obj):
        return obj.baslik or "Başlık Yok"
    baslik_goster.short_description = "Dava Başlığı"

# --- HUKUK KATEGORİLERİ ---
@admin.register(HukukKategori)
class HukukKategoriAdmin(admin.ModelAdmin):
    list_display = ('isim', 'slug', 'aktif_mi')
    prepopulated_fields = {'slug': ('isim',)}

# --- AVUKATLAR ---
@admin.register(Avukat)
class AvukatAdmin(admin.ModelAdmin):
    list_display = ('isim', 'uzmanlik', 'eposta', 'telefon')
    search_fields = ('isim', 'uzmanlik')

# --- REKLAM BANNERLARI ---
@admin.register(ReklamBanner)
class ReklamBannerAdmin(admin.ModelAdmin):
    list_display = ('isim', 'pozisyon', 'gorsel_onizleme', 'aktif_mi')
    list_filter = ('pozisyon', 'aktif_mi')
    
    def gorsel_onizleme(self, obj):
        if obj.gorsel:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.gorsel.url)
        return "-"
    gorsel_onizleme.short_description = "Görsel"

# --- RANDEVULAR ---
@admin.register(AvukatRandevu)
class AvukatRandevuAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'avukat', 'tarih', 'durum_renkli')
    list_filter = ('durum', 'tarih', 'avukat')
    search_fields = ('ad_soyad', 'eposta')
    
    def durum_renkli(self, obj):
        colors = {
            'Bekliyor': 'orange',
            'Tamamlandı': 'green',
            'İptal': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.durum, 'black'),
            obj.durum
        )
    durum_renkli.short_description = "Durum"

# --- SİPARİŞLER ---
@admin.register(Siparis)
class SiparisAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'paket', 'fiyat_goster', 'tarih', 'odendi_mi')
    list_filter = ('odendi_mi', 'tarih')
    
    def fiyat_goster(self, obj):
        return f"{obj.paket.fiyat} TL"
    fiyat_goster.short_description = "Tutar"

# --- DİĞER MODELLER ---
admin.site.register(KanunMaddesi)
admin.site.register(Paket)
admin.site.register(SohbetGecmisi)
admin.site.register(VeriGuncellemeLog)
admin.site.register(SistemBildirimi)
admin.site.register(BetaKullanici)

# --- PANEL BAŞLIKLARI ---
admin.site.site_header = "L.E.X.I. Yönetim Paneli"
admin.site.site_title = "L.E.X.I. Admin"
admin.site.index_title = "Hukuk AI Sistem Yönetimi"