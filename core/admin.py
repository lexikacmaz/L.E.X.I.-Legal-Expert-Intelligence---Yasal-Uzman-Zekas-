from django.contrib import admin
from .models import HukukKategori, KanunMaddesi, EmsalKarar, SiteAyarlari, Avukat, Paket # Diğer modellerin...

# Kategorileri panelde görmek için
@admin.register(HukukKategori)
class HukukKategoriAdmin(admin.ModelAdmin):
    list_display = ('isim', 'ikon', 'aktif_mi') # Listede görünenler
    list_editable = ('ikon', 'aktif_mi') # Listeden direkt düzenleme imkanı
    search_fields = ('isim',)
    prepopulated_fields = {'slug': ('isim',)} # Slug'ı isme göre otomatik doldur
    
    fieldsets = (
        ('Görünüm Ayarları', {
            'fields': ('isim', 'slug', 'ikon', 'aciklama', 'aktif_mi')
        }),
        ('Yapay Zeka Beyni', {
            'fields': ('ai_talimati',),
            'description': 'Buraya yazacağınız talimat, botun karakterini belirler.'
        }),
    )
# Kanun maddelerini panelde görmek için
@admin.register(KanunMaddesi)
class KanunAdmin(admin.ModelAdmin):
    # BURASI DÜZELTİLDİ: Artık 'konu' yok.
    list_display = ('kanun_adi', 'madde_no', 'kanun_no')
    search_fields = ('kanun_adi', 'madde_no', 'icerik')
    list_filter = ('kategori',)

# Emsal kararları panelde görmek için
@admin.register(EmsalKarar)
class EmsalKararAdmin(admin.ModelAdmin):
    list_display = ('daire', 'esas_no', 'karar_no', 'tarih')
    search_fields = ('ozet', 'tam_metin')