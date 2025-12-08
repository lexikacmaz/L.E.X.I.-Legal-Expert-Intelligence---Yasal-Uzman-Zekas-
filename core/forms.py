from django import forms
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner, BetaKullanici
)

# --- 1. SİTE AYARLARI FORMU (RENK PALETİ ÖZELLİKLİ) ---
class AyarForm(forms.ModelForm):
    class Meta:
        model = SiteAyarlari
        fields = '__all__'
        widgets = {
            'renk_ana': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_arkaplan_light': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_yazi_light': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_kart_light': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_arkaplan_dark': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_yazi_dark': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
            'renk_kart_dark': forms.TextInput(attrs={'type': 'color', 'style': 'height: 50px; width: 100%; padding: 2px; border-radius: 10px; cursor: pointer;'}),
        }

# --- BETA GİRİŞ FORMU ---
class BetaGirisForm(forms.Form):
    kullanici_adi = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'beta-input', 'placeholder': 'Kullanıcı Adı'
    }))
    sifre = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'beta-input', 'placeholder': 'Şifre'
    }))

# --- YENİ EKLENEN: BETA BAŞVURU FORMU ---
class BetaBasvuruForm(forms.ModelForm):
    class Meta:
        model = BetaKullanici
        fields = ['kullanici_adi', 'email', 'sifre']
        widgets = {
            'kullanici_adi': forms.TextInput(attrs={'class': 'beta-input', 'placeholder': 'Kullanıcı Adı Belirleyin'}),
            'email': forms.EmailInput(attrs={'class': 'beta-input', 'placeholder': 'E-posta Adresiniz'}),
            'sifre': forms.PasswordInput(attrs={'class': 'beta-input', 'placeholder': 'Şifre Belirleyin'}),
        }

# --- BETA KULLANICI YÖNETİMİ ---
class BetaKullaniciForm(forms.ModelForm):
    class Meta:
        model = BetaKullanici
        fields = '__all__'

# --- DİĞER FORMLAR ---
class AvukatForm(forms.ModelForm):
    class Meta:
        model = Avukat
        fields = '__all__'

class PaketForm(forms.ModelForm):
    class Meta:
        model = Paket
        fields = '__all__'

class KanunForm(forms.ModelForm):
    class Meta:
        model = KanunMaddesi
        fields = '__all__'

class SiparisForm(forms.ModelForm):
    class Meta:
        model = Siparis
        fields = ['ad_soyad', 'telefon', 'eposta', 'notlar']

class RandevuForm(forms.ModelForm):
    class Meta:
        model = AvukatRandevu
        fields = ['ad_soyad', 'telefon', 'eposta', 'mesaj']

class SohbetForm(forms.ModelForm):
    class Meta:
        model = SohbetGecmisi
        fields = '__all__'

class RandevuAdminForm(forms.ModelForm):
    class Meta:
        model = AvukatRandevu
        fields = '__all__'

class AvukatProfilForm(forms.ModelForm):
    class Meta:
        model = Avukat
        fields = ['resim', 'uzmanlik', 'ozet', 'eposta', 'telefon']

class RandevuDurumForm(forms.ModelForm):
    class Meta:
        model = AvukatRandevu
        fields = ['durum']

class ReklamForm(forms.ModelForm):
    class Meta:
        model = ReklamBanner
        fields = ['isim', 'gorsel', 'link', 'pozisyon', 'aktif_mi']
        widgets = {
            'isim': forms.TextInput(attrs={'placeholder': 'Örn: Nike Reklamı'}),
            'link': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'pozisyon': forms.Select(attrs={'style': 'height: 50px;'}),
        }
        help_texts = {
            'gorsel': '📷 Otomatik Boyutlandırma: Yüklenen resim otomatik 160x600px yapılır.',
        }