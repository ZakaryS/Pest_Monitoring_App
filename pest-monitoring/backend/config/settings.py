"""Django settings for the Pest Monitoring backend.

Every value that changes between a laptop, the CI pipeline and Azure is read
from an environment variable. Defaults are safe for local development and tests:
SQLite, local file storage and no Entra ID sign-in required.
"""
from __future__ import annotations

import os
from pathlib import Path

from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).lower() in ("1", "true", "yes")


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

if not DEBUG and SECRET_KEY.startswith("dev-only"):
    raise RuntimeError("Set DJANGO_SECRET_KEY when DJANGO_DEBUG is false.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "reference",
    "accounts",
    "sightings",
    "alerts",
]

MIDDLEWARE = [
    "config.health.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ---------- Database ----------
# Local/CI: SQLite. Azure: DB_ENGINE=mssql (Azure SQL Database via mssql-django).
if env("DB_ENGINE", "sqlite") == "mssql":
    DATABASES = {"default": {
        "ENGINE": "mssql",
        "NAME": env("DB_NAME", "pestmonitoring"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", "1433"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "OPTIONS": {
            "python_driver": "mssql_python",
            "extra_params": env("DB_EXTRA_PARAMS", "Encrypt=yes;TrustServerCertificate=no"),
        },
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / env("SQLITE_NAME", "db.sqlite3"),
    }}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en-ie"
TIME_ZONE = "Europe/Dublin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------- File storage (sighting photos) ----------
# Local/CI: files under backend/media. Azure: Blob Storage with managed identity.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"
if env("AZURE_STORAGE_ACCOUNT"):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "account_name": env("AZURE_STORAGE_ACCOUNT"),
                "azure_container": env("AZURE_STORAGE_CONTAINER", "sightings"),
                "expiration_secs": 600,  # photo links are short-lived SAS URLs
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# ---------- API ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.EntraJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": env("ANON_THROTTLE", "60/hour")},
}

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:4200")
CORS_ALLOW_HEADERS = (*default_headers, "x-upload-token")

# ---------- Microsoft Entra ID (US-01) ----------
ENTRA_TENANT_ID = env("ENTRA_TENANT_ID")
ENTRA_API_AUDIENCE = env("ENTRA_API_AUDIENCE")  # e.g. api://pest-monitoring
ENTRA_ISSUER = env("ENTRA_ISSUER", f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/v2.0")
ENTRA_JWKS_URL = env("ENTRA_JWKS_URL",
                     f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/discovery/v2.0/keys")

# ---------- Alerts (US-06) ----------
ALERT_THRESHOLD = int(env("ALERT_THRESHOLD", "10"))  # sightings in 30 days; agree with the group
NOTIFICATION_HUB_CONNECTION_STRING = env("NOTIFICATION_HUB_CONNECTION_STRING")
NOTIFICATION_HUB_NAME = env("NOTIFICATION_HUB_NAME")

# ---------- Security headers when deployed ----------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}

if env("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: E402

    configure_azure_monitor()
