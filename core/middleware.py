from django.shortcuts import redirect
from django.urls import reverse

class BetaAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Herkesin girebileceği serbest yollar (Giriş, Kayıt, Admin, Dosyalar)
        allowed_paths = [
            reverse('beta_giris'),   # /beta-giris/
            reverse('beta_basvuru'), # /beta-basvuru/
            '/admin/',               # Admin paneli
            '/static/',              # CSS/JS dosyaları
            '/media/',               # Resimler
            '/avukat-giris/',        # Avukat girişi
        ]

        # Eğer gidilen yol, izin verilenlerden biriyse KONTROL ETME, GEÇİR.
        if any(request.path.startswith(path) for path in allowed_paths):
            return self.get_response(request)

        # 2. KONTROL NOKTASI: İçeri girmek istiyor. Kimliği var mı?
        
        # A) Yönetici mi? (Admin hesabıyla girenler)
        is_admin = request.user.is_authenticated and request.user.is_superuser
        
        # B) Beta Kullanıcısı mı? (Session'da ID var mı?)
        is_beta_user = 'beta_kullanici_id' in request.session

        # Eğer ne Yönetici ne de Beta kullanıcısı ise -> GİRİŞE AT
        if not (is_admin or is_beta_user):
            return redirect('beta_giris')

        # Kimliği varsa -> DEVAM ET
        return self.get_response(request)