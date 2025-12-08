
# core/middleware.py (Dosya yoksa oluştur)

from django.shortcuts import redirect
from django.urls import reverse

class BetaAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Eğer kullanıcı zaten Beta izni aldıysa geçsin
        if request.session.get('beta_erisim_izni'):
            return self.get_response(request)

        # 2. Eğer gidilen yer zaten "Beta Giriş Sayfası" ise geçsin (Döngüye girmesin)
        if request.path == reverse('beta_giris'):
            return self.get_response(request)
            
        # 3. Admin paneline ve statik dosyalara izin ver (Yoksa kilitli kalırsın)
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        # 4. Yukarıdakiler değilse, HOP HEMŞERİM NEREYE? -> Giriş sayfasına at
        return redirect('beta_giris')