"""
Django settings for HukukProje project.
"""
import os
from pathlib import Path

# Projenin ana dizini
BASE_DIR = Path(__file__).resolve().parent.parent

# GÜVENLİK AYARLARI
SECRET_KEY = 'django-insecure--q$bpt%v66x-c!od&m!v3+2*+$w-5$@047ti4bw5b$bq^7sdyf'

# Geliştirme aşamasında True
DEBUG = True

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

# --- DÜZELTİLEN MIDDLEWARE (TEK VE DOĞRU LİSTE) ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Session en üstlerde olmalı
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Auth, Session'dan sonra gelmeli
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # BİZİM GÜVENLİK GÖREVLİSİ (EN SONDA OLMALI)
    'core.middleware.BetaAccessMiddleware',
]

ROOT_URLCONF = 'HukukProje.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Eğer ana dizinde templates klasörü kullanırsan
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
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


# DİL VE SAAT AYARLARI
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True


# --- STATİK DOSYALAR ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# --- MEDYA AYARLARI ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- GİRİŞ / ÇIKIŞ YÖNLENDİRMELERİ ---
# Eğer sistem otomatik bir yönlendirme yaparsa buraya gitsin:
LOGIN_URL = '/beta-giris/'  # DÜZELTME: Giriş yapılmamışsa buraya atsın
LOGIN_REDIRECT_URL = '/'    # DÜZELTME: Giriş yapınca Ana Sayfaya gitsin
LOGOUT_REDIRECT_URL = '/'   # Çıkış yapınca Ana Sayfaya (veya girişe) gitsin

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'