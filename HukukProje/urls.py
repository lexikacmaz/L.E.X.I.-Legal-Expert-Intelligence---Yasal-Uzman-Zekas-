from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # --- ESKİ ANA SAYFAN (Sitenin girişi burası olacak) ---
    path('', views.home, name='home'), 

    # --- YENİ SİSTEM (Menüden tıklayınca gidilecek yer) ---
    path('asistan/', views.kategori_listesi, name='asistan_secimi'),
    path('bot/<slug:slug>/', views.uzman_bot_chat, name='uzman_bot'),

    # --- DİĞER ESKİ SAYFALARIN (Hepsi duruyor) ---
    path('admin/', admin.site.urls),
    path('avukatlar/', views.avukatlar, name='avukatlar'),
    path('paketler/', views.paketler, name='paketler'),
    path('yasal/', views.yasal, name='yasal'),
    
    # Satış ve Randevu
    path('satin-al/<int:paket_id>/', views.satin_al, name='satin_al'),
    path('odeme/<int:siparis_id>/', views.odeme_sayfasi, name='odeme_sayfasi'),
    path('siparis-basarili/', views.siparis_basarili, name='siparis_basarili'),
    path('randevu-al/<int:avukat_id>/', views.randevu_al, name='randevu_al'),

    # Panel İşlemleri
    path('cikis/', views.cikis_yap, name='cikis_yap'),
    path('panel/', views.panel_dashboard, name='panel_dashboard'),
    path('panel/ayarlar/', views.panel_ayarlar, name='panel_ayarlar'),
    # Panel liste için str:tip kullanıyorduk, aynen devam
    path('panel/liste/<str:tip>/', views.panel_icerik, name='panel_icerik'),
    path('panel/ekle/<str:tip>/', views.panel_ekle, name='panel_ekle'),
    path('panel/duzenle/<str:tip>/<int:id>/', views.panel_duzenle, name='panel_duzenle'),
    path('panel/sil/<str:tip>/<int:id>/', views.panel_sil, name='panel_sil'),

    path('avukat-panel/', views.avukat_dashboard, name='avukat_dashboard'),
    path('avukat-profil/', views.avukat_profil_duzenle, name='avukat_profil_duzenle'),
    path('randevu-islem/<int:id>/', views.avukat_randevu_islem, name='avukat_randevu_islem'),
    path('avukat-giris/', views.avukat_giris_yap, name='avukat_giris'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)