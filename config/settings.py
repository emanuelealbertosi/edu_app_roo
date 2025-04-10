"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import os # Add this line
from dotenv import load_dotenv # Aggiunto import
import dj_database_url
import sys
from pathlib import Path

# Carica le variabili d'ambiente da .env (per sviluppo locale)
# Questo dovrebbe essere fatto il prima possibile
load_dotenv()



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the 'apps' directory to sys.path
# This allows Django to find our apps like 'apps.users'
APPS_DIR = BASE_DIR / 'apps'
if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Leggi SECRET_KEY dall'ambiente, con un fallback per sicurezza (anche se non ideale per prod)
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-insecure-key-replace-me-in-env')

# SECURITY WARNING: don't run with debug turned on in production!
# Leggi DEBUG dall'ambiente, convertendo la stringa in Booleano. Default a False per produzione.
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# Leggi ALLOWED_HOSTS dall'ambiente, separando la stringa per virgole.
# Default a '*' se non specificato, ma è più sicuro specificare host reali in .env.prod
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_json_widget', # Added for better JSON editing in admin
    # (e.g., 'allauth', etc. - will be added later)

    # Local Apps
    'apps.users.apps.UsersConfig',

    'apps.education.apps.EducationConfig',
    'apps.rewards.apps.RewardsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise Middleware (subito dopo SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Aggiunto per CORS
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# https://github.com/jazzband/dj-database-url

# Leggi esplicitamente DATABASE_URL dall'ambiente
DATABASE_URL_ENV = os.getenv('DATABASE_URL')
print(f"DATABASE_URL from environment: {DATABASE_URL_ENV}") # Debug

if DATABASE_URL_ENV:
    print("Using DATABASE_URL from environment for database config.") # Debug
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL_ENV, conn_max_age=600)
    }
else:
    # Fallback a SQLite se DATABASE_URL non è impostata (per sviluppo locale senza .env)
    print("DATABASE_URL not found in environment, falling back to SQLite.") # Debug
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Directory dove collectstatic raccoglierà i file statici per la produzione
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configurazione Storage per Whitenoise (per servire file statici compressi)
# https://whitenoise.readthedocs.io/en/stable/django.html#add-compression-and-caching-support
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media Files (User Uploaded Files)
# https://docs.djangoproject.com/en/5.1/topics/files/
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles' # Directory dove verranno salvati i file caricati
# Rimuovi la parentesi graffa extra qui sotto

# Custom User Model
# https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = 'users.User'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Authentication Backends
# https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#specifying-authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', # Backend di default per User (Admin/Docente)
    'apps.users.backends.StudentCodeBackend',    # Backend custom per Studenti
]


# Django REST Framework Configuration
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Prova prima l'autenticazione studente custom
        'apps.users.authentication.StudentJWTAuthentication',
        # Poi prova l'autenticazione JWT standard per Admin/Docenti
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # Rimuoviamo temporaneamente SessionAuthentication per debug test 401
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        # NON impostare un permesso predefinito globale.
        # I permessi verranno specificati esplicitamente in ciascuna View/ViewSet.
        # 'rest_framework.permissions.IsAuthenticated', # Rimosso
    ),
    # Optional: Add pagination, filtering, etc. defaults here
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10
}

# Simple JWT Configuration
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Adjust as needed (e.g., 5 minutes for higher security)
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False, # Set to True if you want refresh tokens to be invalidated after use
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True, # Update user's last_login field upon refresh

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY, # Use Django's SECRET_KEY
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",), # Standard "Bearer <token>"
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5), # Not used by default
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1), # Not used by default

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

# CORS Configuration
# https://github.com/adamchainz/django-cors-headers
# Leggi le origini CORS dall'ambiente, separando la stringa per virgole.
# Fornisci un default ragionevole per lo sviluppo locale se la variabile non è impostata.
CORS_ALLOWED_ORIGINS_ENV = os.getenv('CORS_ALLOWED_ORIGINS')
if CORS_ALLOWED_ORIGINS_ENV:
    CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS_ENV.split(',')
else:
    # Default per sviluppo locale se la variabile d'ambiente non è impostata
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175", # Probabilmente vecchio, ma lo lasciamo per sicurezza
        "http://127.0.0.1:5175",
        "http://localhost:5174", # Porta corrente sviluppo docente
        "http://127.0.0.1:5174",
    ]

CORS_ALLOW_CREDENTIALS = True  # Permetti l'invio di cookies nelle richieste cross-origin

# Metodi HTTP consentiti
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Headers consentiti nelle richieste
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
