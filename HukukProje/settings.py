"""
Django settings for HukukProje project.
"""
import os
from pathlib import Path

# Projenin ana dizini
BASE_DIR = Path(__file__).resolve().parent.parent

# GÜVENLİK AYARLARI
# Canlıya alırken (Deploy) bu anahtarı gizli tutmalısın.
SECRET_KEY = 'django-insecure--q$bpt%v66x-c!od&m!v3+2*+$w-5$@047ti4bw5b$bq^7sdyf'

# Geliştirme aşamasında True, sunucuya atınca False olacak.
DEBUG = True

# Her yerden erişim için '*' yaptık (VDS ve Localhost için gerekli)
ALLOWED_HOSTS = ['*']


# UYGULAMA TANIMLARI
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core', # Senin uygulaman
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HukukProje.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # Eğer templates klasörün ana dizindeyse buraya eklenir
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'HukukProje.wsgi.application'


# VERİTABANI AYARLARI
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ŞİFRE DOĞRULAMA
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# DİL VE SAAT AYARLARI (Türkiye İçin Ayarlandı)
LANGUAGE_CODE = 'tr'  # Türkçe

TIME_ZONE = 'Europe/Istanbul' # Türkiye Saati

USE_I18N = True

USE_TZ = True


# --- STATİK DOSYALAR (CSS, JavaScript, Images) ---
STATIC_URL = 'static/'

# Proje içindeki static klasörü (Varsa)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Sunucuda (VDS) dosyaların toplanacağı yer
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# --- MEDYA AYARLARI (Yüklenen Resimler İçin) ---
# Tarayıcıdan erişim adresi
MEDIA_URL = '/media/'

# Dosyaların bilgisayarda kaydedileceği klasör
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- GİRİŞ / ÇIKIŞ YÖNLENDİRMELERİ ---
# Giriş yapan kullanıcı nereye gitsin?
LOGIN_REDIRECT_URL = 'avukat_dashboard' 

# Çıkış yapan kullanıcı nereye gitsin?
LOGOUT_REDIRECT_URL = 'home'

# Varsayılan Otomatik Alan Tipi (Uyarı vermemesi için)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'