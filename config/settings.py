import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

IS_TESTING = "test" in sys.argv
VERCEL_ENV = os.getenv("VERCEL_ENV", "").strip().lower()
IS_VERCEL = os.getenv("VERCEL", "").strip() == "1" or bool(VERCEL_ENV)
DJANGO_ENV = (
    os.getenv("DJANGO_ENV", "production" if IS_VERCEL else "development")
    .strip()
    .lower()
)
if DJANGO_ENV not in {"development", "test", "preview", "production"}:
    raise ImproperlyConfigured(
        "DJANGO_ENV deve ser development, test, preview ou production."
    )

IS_PRODUCTION = DJANGO_ENV == "production"
IS_DEPLOYED = IS_VERCEL or DJANGO_ENV in {"preview", "production"}
DEBUG = os.getenv("DJANGO_DEBUG", "False").strip().lower() == "true"
if IS_DEPLOYED and DEBUG:
    raise ImproperlyConfigured(
        "DJANGO_DEBUG deve ser False fora do desenvolvimento local."
    )


def _boolean_environment_setting(name, default):
    value = os.getenv(name, default).strip().lower()
    if value not in {"true", "false"}:
        raise ImproperlyConfigured(f"{name} deve ser True ou False.")
    return value == "true"


def _bounded_integer_environment_setting(name, default, minimum, maximum):
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} deve ser um numero inteiro.") from exc
    if not minimum <= value <= maximum:
        raise ImproperlyConfigured(f"{name} deve ficar entre {minimum} e {maximum}.")
    return value


# O chat e opcional: a chave do Gemini nunca chega ao navegador e a feature
# continua desligada ate que seja habilitada explicitamente no ambiente.
AI_FILTER_ENABLED = _boolean_environment_setting("AI_FILTER_ENABLED", "False")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
AI_FILTER_TIMEOUT_SECONDS = _bounded_integer_environment_setting(
    "AI_FILTER_TIMEOUT_SECONDS", 20, 10, 45
)
AI_FILTER_RETRIES = _bounded_integer_environment_setting("AI_FILTER_RETRIES", 2, 1, 3)
AI_FILTER_MAX_TEXT_CHARS = _bounded_integer_environment_setting(
    "AI_FILTER_MAX_TEXT_CHARS", 360, 40, 1000
)
AI_FILTER_CACHE_SECONDS = _bounded_integer_environment_setting(
    "AI_FILTER_CACHE_SECONDS", 600, 0, 3600
)
if AI_FILTER_ENABLED and not GEMINI_MODEL:
    raise ImproperlyConfigured("GEMINI_MODEL e obrigatorio com AI_FILTER_ENABLED=True.")
if AI_FILTER_ENABLED and IS_DEPLOYED and not GEMINI_API_KEY:
    raise ImproperlyConfigured(
        "GEMINI_API_KEY e obrigatoria com AI_FILTER_ENABLED=True fora do ambiente local."
    )


def _secret_is_strong(value):
    insecure_markers = {
        "insegura-apenas-para-desenvolvimento",
        "troque-por-uma-chave-segura",
        "change-me",
        "changeme",
    }
    return (
        len(value) >= 50
        and len(set(value)) >= 12
        and value.casefold() not in insecure_markers
    )


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if IS_DEPLOYED and not _secret_is_strong(SECRET_KEY):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY deve existir, ter ao menos 50 caracteres e ser exclusiva."
    )
if not SECRET_KEY:
    if DEBUG or IS_TESTING or DJANGO_ENV == "test":
        SECRET_KEY = "insegura-apenas-para-desenvolvimento"
    else:
        raise ImproperlyConfigured("Configure a variavel DJANGO_SECRET_KEY.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

SITE_URL = os.getenv("SITE_URL", "https://qualfilmehoje.vercel.app").strip().rstrip("/")
site_url_parts = urlsplit(SITE_URL)
if (
    site_url_parts.scheme not in {"http", "https"}
    or not site_url_parts.netloc
    or site_url_parts.path
    or site_url_parts.query
    or site_url_parts.fragment
):
    raise ImproperlyConfigured(
        "SITE_URL deve conter apenas a origem publica, por exemplo "
        "https://qualfilmehoje.vercel.app."
    )
if IS_DEPLOYED and site_url_parts.scheme != "https":
    raise ImproperlyConfigured("SITE_URL deve usar HTTPS fora do ambiente local.")

GOOGLE_SITE_VERIFICATION = (
    os.getenv("GOOGLE_SITE_VERIFICATION", "").strip()
    or "8J1E6sV8WN1zxIrmvUWlcKWKDZ8lurm1bycxUgO2ssc"
)
BING_SITE_VERIFICATION = (
    os.getenv("BING_SITE_VERIFICATION", "").strip()
    or "BAADAFCE767CC2A73B3A5DEF51A06BC7"
)
INDEXNOW_KEY = (
    os.getenv("INDEXNOW_KEY", "").strip() or "a8c7cb6034564b13897e893feebabe4e"
)
if not 8 <= len(INDEXNOW_KEY) <= 128 or any(
    not character.isascii() or not (character.isalnum() or character == "-")
    for character in INDEXNOW_KEY
):
    raise ImproperlyConfigured("INDEXNOW_KEY possui formato invalido.")
indexnow_enabled_value = (
    os.getenv("INDEXNOW_ENABLED", "True" if IS_PRODUCTION else "False").strip().lower()
)
if indexnow_enabled_value not in {"true", "false"}:
    raise ImproperlyConfigured("INDEXNOW_ENABLED deve ser True ou False.")
INDEXNOW_ENABLED = indexnow_enabled_value == "true"

# Cada Preview da Vercel recebe um hostname proprio. Aceitamos apenas os
# hostnames exatos fornecidos pela plataforma, sem liberar o curinga amplo
# ``.vercel.app``.
for vercel_host_variable in (
    "VERCEL_URL",
    "VERCEL_BRANCH_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
):
    vercel_host = os.getenv(vercel_host_variable, "").strip()
    if vercel_host:
        vercel_host = vercel_host.removeprefix("https://").removeprefix("http://")
        vercel_host = vercel_host.split("/", 1)[0]
        if vercel_host and vercel_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(vercel_host)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "movies.apps.MoviesConfig",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "anymail",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "movies.middleware.AdminMFAMiddleware",
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
                "movies.context_processors.authentication",
                "movies.context_processors.seo_metadata",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_SQLITE = (
    os.getenv("DJANGO_USE_SQLITE", "False").strip().lower() == "true" or IS_TESTING
)

if IS_DEPLOYED and USE_SQLITE:
    raise ImproperlyConfigured("SQLite nao pode ser usado na Vercel ou em producao.")

if DATABASE_URL and not USE_SQLITE:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.getenv("DATABASE_CONN_MAX_AGE", "0")),
            conn_health_checks=True,
        )
    }
elif USE_SQLITE and not IS_DEPLOYED:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured(
        "Configure DATABASE_URL. SQLite so e aceito quando DJANGO_USE_SQLITE=True "
        "no desenvolvimento local."
    )

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# O projeto nao recebe uploads. Estes limites impedem que o Django mantenha
# corpos arbitrariamente grandes em memoria antes de uma view rejeita-los.
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100
DATA_UPLOAD_MAX_NUMBER_FILES = 5

CSP_POLICY = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF],
    "style-src": [CSP.SELF, "https://fonts.googleapis.com"],
    "img-src": [
        CSP.SELF,
        "data:",
        "https://image.tmdb.org",
        "https://cdn.watchmode.com",
    ],
    "font-src": [CSP.SELF, "https://fonts.gstatic.com"],
    "connect-src": [CSP.SELF],
    "frame-src": ["https://www.youtube-nocookie.com"],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.SELF],
    "form-action": [CSP.SELF],
    "frame-ancestors": [CSP.NONE],
    "report-uri": ["/security/csp-report/"],
}
CSP_ENFORCE = os.getenv("DJANGO_CSP_ENFORCE", "False").strip().lower() == "true"
if CSP_ENFORCE:
    SECURE_CSP = CSP_POLICY
else:
    SECURE_CSP_REPORT_ONLY = CSP_POLICY

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# No servidor, o cache usa o proprio Neon para ser compartilhado entre todas
# as funcoes serverless. Testes permanecem isolados e rapidos em memoria.
if IS_TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "qualfilmehoje-tests",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "qualfilmehoje_cache",
            "KEY_PREFIX": "qfh",
            "TIMEOUT": 300,
            "OPTIONS": {"MAX_ENTRIES": 5000, "CULL_FREQUENCY": 4},
        }
    }

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_ADAPTER = "movies.adapters.QualFilmeHojeAccountAdapter"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SESSION_REMEMBER = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
ACCOUNT_RATE_LIMITS = {
    "login": "20/5m/ip",
    "login_failed": "10/10m/ip,5/10m/key",
    "signup": "5/h/ip",
    "reset_password": "5/h/ip,3/h/key",
    "reset_password_from_key": "10/h/ip",
}

# A Vercel e o unico proxy confiavel na arquitetura atual. Localmente o XFF e
# ignorado, evitando que um cliente burle os limites com um header forjado.
ALLAUTH_TRUSTED_PROXY_COUNT = 1 if IS_VERCEL else 0
ALLAUTH_RATE_LIMIT_IPV6_PREFIX = 64

MFA_ADAPTER = "movies.mfa_adapter.QualFilmeHojeMFAAdapter"
MFA_SUPPORTED_TYPES = ["recovery_codes", "totp"]
MFA_TOTP_ISSUER = "QualFilmeHoje"
MFA_RECOVERY_CODES_SHOW_ONCE = True
MFA_TRUST_ENABLED = False

# Sessões curtas e apenas cookies estritamente necessários. A sessão atual é
# preservada na troca de senha; as demais são eliminadas pelos signals do app.
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = False

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_AUTH_CONFIGURED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()
CONFIGURED_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "").strip()
EMAIL_DELIVERY_CONFIGURED = bool(BREVO_API_KEY and CONFIGURED_FROM_EMAIL)
if IS_DEPLOYED and not EMAIL_DELIVERY_CONFIGURED:
    raise ImproperlyConfigured(
        "BREVO_API_KEY e DEFAULT_FROM_EMAIL sao obrigatorios fora do ambiente local."
    )
EMAIL_FEATURES_ENABLED = EMAIL_DELIVERY_CONFIGURED or DEBUG or IS_TESTING

DEFAULT_FROM_EMAIL = CONFIGURED_FROM_EMAIL or "QualFilmeHoje <no-reply@localhost>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 10

if IS_TESTING:
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
elif EMAIL_DELIVERY_CONFIGURED:
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    ANYMAIL = {"BREVO_API_KEY": BREVO_API_KEY}
elif DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    raise ImproperlyConfigured(
        "A entrega de e-mail nao esta configurada; a verificacao nao sera desativada."
    )

# Cadastro por senha nunca degrada silenciosamente para e-mail nao verificado.
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
        "EMAIL_AUTHENTICATION": True,
    }
}
if GOOGLE_AUTH_CONFIGURED:
    SOCIALACCOUNT_PROVIDERS["google"]["APPS"] = [
        {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
        }
    ]

if not DEBUG and not IS_TESTING:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "3600"))
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
