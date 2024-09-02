import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from .spectacular_settings import *

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("secretKeyDjango")
# Testa se já há variáveis de ambiente configuradas, se não há, carrega do arquivo local .env
if not SECRET_KEY:
    load_dotenv()
    SECRET_KEY = os.environ.get("secretKeyDjango")

DEBUG = os.environ.get("debugMode")
ALLOWED_HOSTS = [os.environ.get("allowedHosts")]
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("bdEngine"),
        "NAME": os.environ.get("bdName"),
        "USER": os.environ.get("bdUser"),
        "PASSWORD": os.environ.get("bdPass"),
        "HOST": os.environ.get("bdHost"),
        "PORT": os.environ.get("bdPort"),
    }
}

INTERNAL_IPS = [
    "127.0.0.1",
]

if "test" in sys.argv or "test_coverage" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }

CORS_ORIGIN_WHITELIST = [
    "https://cloud.seenode.com",
    "http://127.0.0.1",
    "https://127.0.0.1",
]

CORS_ALLOWED_HOSTS = [
    "https://cloud.seenode.com",
    "http://127.0.0.1",
    "https://127.0.0.1",
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://cloud.seenode.com",
    "http://127.0.0.1",
    "https://127.0.0.1",
]

CORS_ALLOW_ALL_ORIGINS: True

CORS_ALLOW_METHODS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "chamecoapi",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "chameco.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
    "DATE_INPUT_FORMATS": ["%Y-%m-%d", "%Y/%m/%d"],
    "TIME_INPUT_FORMATS": [
        "%H:%M",
    ],
}

WSGI_APPLICATION = "chameco.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "pt-BR"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
