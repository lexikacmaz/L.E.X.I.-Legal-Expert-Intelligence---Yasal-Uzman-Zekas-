from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.views import beta_basvuru

urlpatterns = [
    # --- ANA SAYFA ---
    path('', views.home, name='home'),

    # --- AI ASİSTAN ---
    path('asistan/', views.kategori_listesi, name='asistan_secimi'),
    path('bot/<slug:slug>/', views.uzman_bot_chat, name='uzman_bot'),

    # --- GİRİŞ YOLLARI ---
    path('avukat-giris/', views.avukat_giris_yap, name='avukat_giris'),
    path('admin/', admin.site.urls),
    path('cikis/', views.cikis_yap, name='cikis_yap'),

    # --- PANELLER ---
    path('panel/', views.panel_dashboard, name='panel_dashboard'),
    path('panel/ayarlar/', views.panel_ayarlar, name='panel_ayarlar'),
    path('panel/liste/<str:tip>/', views.panel_icerik, name='panel_icerik'),
    path('panel/ekle/<str:tip>/', views.panel_ekle, name='panel_ekle'),
    path('panel/duzenle/<str:tip>/<int:id>/', views.panel_duzenle, name='panel_duzenle'),
    path('panel/sil/<str:tip>/<int:id>/', views.panel_sil, name='panel_sil'),

    # Avukat Paneli
    path('avukat-panel/', views.avukat_dashboard, name='avukat_dashboard'),
    path('avukat-profil/', views.avukat_profil_duzenle, name='avukat_profil_duzenle'),
    path('randevu-islem/<int:id>/', views.avukat_randevu_islem, name='avukat_randevu_islem'),

    # --- DİĞER SAYFALAR ---
    path('avukatlar/', views.avukatlar, name='avukatlar'),
    path('paketler/', views.paketler, name='paketler'),
    path('yasal/', views.yasal, name='yasal'),
    path('satin-al/<int:paket_id>/', views.satin_al, name='satin_al'),
    path('odeme/<int:siparis_id>/', views.odeme_sayfasi, name='odeme_sayfasi'),
    path('siparis-basarili/', views.siparis_basarili, name='siparis_basarili'),
    path('randevu-al/<int:avukat_id>/', views.randevu_al, name='randevu_al'),
    path('beta-giris/', views.beta_giris_yap, name='beta_giris'),
    path('beta-basvuru/', beta_basvuru, name='beta_basvuru'),


]

# --- MEDYA DOSYALARI İÇİN SİHİRLİ KOD ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)