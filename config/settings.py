"""
Django settings for Seaway Trading marketing site.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-for-production",
)

# On Render, RENDER is set — default DEBUG off so ALLOWED_HOSTS is not localhost-only.
_on_render = os.environ.get("RENDER", "").lower() == "true"
_default_debug = "false" if _on_render else "true"
DEBUG = os.environ.get("DJANGO_DEBUG", _default_debug).lower() in ("1", "true", "yes")

_render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()

if DEBUG:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    if _render_hostname:
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, _render_hostname]
else:
    _hosts = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
    ALLOWED_HOSTS = _hosts if _hosts else [".onrender.com"]
    if _render_hostname and _render_hostname not in ALLOWED_HOSTS:
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, _render_hostname]

_csrf = [x.strip() for x in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]
if _csrf:
    CSRF_TRUSTED_ORIGINS = _csrf
elif _render_hostname:
    CSRF_TRUSTED_ORIGINS = [f"https://{_render_hostname}"]
else:
    CSRF_TRUSTED_ORIGINS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages",
]

MIDDLEWARE = [
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
        "DIRS": [BASE_DIR / "templates"],
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
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Contact form emails go here
CONTACT_FORM_TO = "sales@seawaytradingqatar.com"

# Optional: SendGrid API (recommended on Render — free tier). Set in environment:
# SENDGRID_API_KEY, and verify a sender in SendGrid (Sender Authentication).
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "").strip()
SENDGRID_FROM_EMAIL = os.environ.get(
    "SENDGRID_FROM_EMAIL",
    os.environ.get("DEFAULT_FROM_EMAIL", "") or f"noreply@{CONTACT_FORM_TO.split('@')[-1]}",
).strip()

# Email: set EMAIL_HOST (and user/password) in production for real SMTP.
# Without EMAIL_HOST, Django prints mail to the console (good for local testing).
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django’s default EMAIL_HOST is "localhost" — do not treat that as “configured”.
SMTP_ENABLED = bool(os.environ.get("EMAIL_HOST", "").strip())

# "From" address — must be allowed by your SMTP provider (often same as EMAIL_HOST_USER)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    f"website@{CONTACT_FORM_TO.split('@')[-1]}",
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
