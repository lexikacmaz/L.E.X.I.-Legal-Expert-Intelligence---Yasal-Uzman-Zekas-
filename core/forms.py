from django import forms
from .models import (
    SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis, 
    SohbetGecmisi, AvukatRandevu, ReklamBanner
)

# --- 1. SİTE AYARLARI FORMU (RENK PALETİ ÖZELLİKLİ) ---
# forms.py -> AyarForm kısmını güncelle

class AyarForm(forms.ModelForm):
    class Meta:
        model = SiteAyarlari
        fields = '__all__'
        
        # Tüm renk alanları için ortak stil
        color_widget = forms.TextInput(attrs={
            'type': 'color', 
            'style': 'height: 45px; width: 100%; padding: 2px; border-radius: 8px; cursor: pointer; border: 1px solid #ddd;'
        })

        widgets = {
            'renk_ana': color_widget,
            'renk_arkaplan_light': color_widget,
            'renk_yazi_light': color_widget,
            'renk_kart_light': color_widget,
            'renk_arkaplan_dark': color_widget,
            'renk_yazi_dark': color_widget,
            'renk_kart_dark': color_widget,
        }

# --- DİĞER FORMLAR (Standart) ---
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
            'gorsel': '📷 <strong>Otomatik Boyutlandırma:</strong> Yüklediğiniz resim ne boyutta olursa olsun, sistem tarafından otomatik olarak <strong>160x600 piksel</strong> boyutuna getirilecektir.',
            'pozisyon': 'Bu reklamın sayfanın solunda mı yoksa sağında mı duracağını seçin.'
        }
        
        