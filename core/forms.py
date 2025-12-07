from django import forms
from .models import SiteAyarlari, Avukat, Paket, KanunMaddesi, Siparis

class AyarForm(forms.ModelForm):
    class Meta:
        model = SiteAyarlari
        fields = '__all__'
        # SİHİRLİ KISIM BURASI:
        # Django'ya diyoruz ki: "Bu alanlarda yazı kutusu değil, RENK SEÇİCİ (Color Input) kullan."
        widgets = {
            'renk_ana': forms.TextInput(attrs={'type': 'color'}),
            'renk_arkaplan': forms.TextInput(attrs={'type': 'color'}),
            'renk_yazi_baslik': forms.TextInput(attrs={'type': 'color'}),
            'renk_yazi_genel': forms.TextInput(attrs={'type': 'color'}),
            'renk_menu_bg': forms.TextInput(attrs={'type': 'color'}),
            'renk_buton': forms.TextInput(attrs={'type': 'color'}),
            'renk_ai_balon': forms.TextInput(attrs={'type': 'color'}),
            'renk_user_balon': forms.TextInput(attrs={'type': 'color'}),
            'renk_input_bg': forms.TextInput(attrs={'type': 'color'}),
        }

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
        fields = ['ad_soyad', 'telefon', 'email', 'adres']
        

from .models import SohbetGecmisi, AvukatRandevu # Modelleri import etmeyi unutma

class RandevuForm(forms.ModelForm):
    class Meta:
        model = AvukatRandevu
        fields = ['ad_soyad', 'telefon', 'mesaj']

class SohbetForm(forms.ModelForm):
    class Meta:
        model = SohbetGecmisi
        fields = '__all__'

class RandevuAdminForm(forms.ModelForm): # Admin panelinde durumu değiştirmek için
    class Meta:
        model = AvukatRandevu
        fields = '__all__'
        
        # core/forms.py EN ALTINA ekle:

# Avukatın kendi profilini düzenlemesi için
class AvukatProfilForm(forms.ModelForm):
    class Meta:
        model = Avukat
        fields = ['isim', 'uzmanlik', 'ozet', 'resim']

# Avukatın randevu durumunu güncellemesi için
class RandevuDurumForm(forms.ModelForm):
    class Meta:
        model = AvukatRandevu
        fields = ['durum']
        
        # core/forms.py EN ALTINA EKLE:

from .models import ReklamBanner

class ReklamForm(forms.ModelForm):
    class Meta:
        model = ReklamBanner
        fields = '__all__'