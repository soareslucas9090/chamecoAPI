import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from .spectacular_settings import *

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

# SECRET_KEY do Django, usada para criptografia
SECRET_KEY = os.environ.get("secretKeyDjango")

# Configura se o Django está em modo de DEBUG ou não
DEBUG = os.environ.get("debugMode")

# Indica todos os hosts autorizados a fazer requisições para o APP
ALLOWED_HOSTS = [os.environ.get("allowedHosts")]

# Configura o banco de dados
# Configurações do banco em produção
# DATABASES = {
#     "default": {
#         "ENGINE": os.environ.get("bdEngine"),
#         "NAME": os.environ.get("bdName"),
#         "USER": os.environ.get("bdUser"),
#         "PASSWORD": os.environ.get("bdPass"),
#         "HOST": os.environ.get("bdHost"),
#         "PORT": os.environ.get("bdPort"),
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Armazena os endereços confiáveis para CSRF
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "csrfTrustedOriginsANDcorsOriginWhitelist", ""
).split(",")

# Indica quais são os endereços internos
INTERNAL_IPS = os.environ.get("internalIPs", "").split(",")

# Armazena os endereços confiáveis para CORS
CORS_ORIGIN_WHITELIST = os.environ.get(
    "csrfTrustedOriginsANDcorsOriginWhitelist", ""
).split(",")

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS: True

CORS_ALLOW_METHODS = ["*"]


if "test" in sys.argv or "test_coverage" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }


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

STATIC_ROOT = "/home/chamecoapi/cortex/static"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
