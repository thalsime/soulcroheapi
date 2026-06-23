"""
Configuração do Django para a API da Soul Crochê.

Valores sensíveis e de ambiente vêm do arquivo .env (ver .env.example), lidos com
python-decouple. Em produção, o docker-compose injeta essas variáveis no ambiente.
"""
from pathlib import Path

from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent

# Defesa contra "decompression bomb": teto de pixels que o Pillow aceita abrir
# (acima disso ele recusa a imagem). Cobre o upload de imagem no admin.
Image.MAX_IMAGE_PIXELS = 40_000_000  # ~40 megapixels

DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

# Em produção a chave é obrigatória (o repositório é público; não pode haver
# chave padrão conhecida). Em desenvolvimento, há um fallback inseguro.
SECRET_KEY = config("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-inseguro-apenas-para-debug-local"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY é obrigatória em produção (defina no .env)."
        )

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv()
)
CSRF_TRUSTED_ORIGINS = [
    origem
    for origem in config("DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
    if origem
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "loja",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("DJANGO_DB_PATH", default=str(BASE_DIR / "data" / "db.sqlite3")),
        # timeout maior evita "database is locked" quando há escrita concorrente.
        "OPTIONS": {"timeout": 20},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = config("DJANGO_TIME_ZONE", default="America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

# Arquivos estáticos (admin, DRF) servidos pelo WhiteNoise dentro do container.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Mídia (imagens enviadas no admin). Em produção o nginx serve /media/ direto.
MEDIA_URL = "/media/"
MEDIA_ROOT = config("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media"))
# Arquivos enviados ficam legíveis para o nginx (que roda como www-data) servir.
FILE_UPLOAD_PERMISSIONS = 0o644

# Limites de upload (defesa contra payloads enormes). O nginx também limita o
# corpo da requisição (client_max_body_size); estes valores são a segunda barreira.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100

# A storage com manifesto exige collectstatic (rodado no container). Em
# desenvolvimento direto (runserver) usamos a versão sem manifesto, que não quebra.
_static_storage = (
    "whitenoise.storage.CompressedStaticFilesStorage"
    if DEBUG
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _static_storage},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Por padrão a API é de leitura pública; cada view restringe o que precisa.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # Só JSON: a Browsable API (HTML) fica desligada; a API responde JSON sempre.
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Ignora o Accept do cliente e responde JSON mesmo a pedidos de text/html.
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "loja.negotiation.JSONOnlyContentNegotiation",
    # Busca (?search=), filtros (?campo=) e ordenação (?ordering=) nos endpoints.
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # Paginação: 10 itens por página (configurável via .env -> PAGE_SIZE).
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": config("PAGE_SIZE", default=10, cast=int),
    # Limite de envios do formulário de contato (mitiga spam pelo token público).
    "DEFAULT_THROTTLE_RATES": {"contato": config("THROTTLE_CONTATO", default="30/min")},
}

# CORS: por segurança, FECHADO por padrão. O .env de produção abre explicitamente
# (CORS_ALLOW_ALL_ORIGINS=1) enquanto o site cliente não tem domínio fixo.
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)

# A API roda atrás do nginx, que termina o TLS. Estes ajustes garantem que o
# Django reconheça o HTTPS (admin e URLs absolutas de imagem ficam com https).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Cabeçalhos de segurança emitidos pelo Django (passam pelo proxy até o cliente):
#   X-Content-Type-Options: nosniff  e  X-Frame-Options: DENY.
# O nginx cuida dos demais (CSP, Referrer-Policy, Permissions-Policy) - ver
# deploy/nginx-soulcroheapi.conf. Divisão para não duplicar o mesmo cabeçalho.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Cookies de sessão e CSRF: sem acesso por JavaScript e presos ao mesmo site.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Em produção: cookies só por HTTPS e HSTS (força HTTPS no navegador). O HSTS é
# emitido pelo Django (não pelo nginx) para evitar o cabeçalho duplicado.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("DJANGO_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging básico para o console (capturado pelo docker logs). Sem corpo de
# requisição nem dados do formulário - evita vazar PII nos logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simples": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simples"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
