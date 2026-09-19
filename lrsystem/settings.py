"""
Django settings for the LR & Attendance Management System.

Database  : Supabase (PostgreSQL)  -> set DATABASE_URL in the environment
Hosting   : Vercel (serverless)    -> see vercel.json / build_files.sh
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file when present (never committed, never used on Vercel).
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _value = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _value.strip().strip('"').strip("'"))


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me-before-deploy"
)

DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]
_extra_origin = os.environ.get("SITE_URL")
if _extra_origin:
    CSRF_TRUSTED_ORIGINS.append(_extra_origin)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "attendance",
    "lrinquiry",
    "reports",
    "reportbuilder",
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
    # Everything sits behind the login page.
    "accounts.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "lrsystem.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lrsystem.context_processors.asset_version",
            ],
        },
    },
]

WSGI_APPLICATION = "lrsystem.wsgi.application"


# --------------------------------------------------------------------------
# Database - Supabase PostgreSQL
# --------------------------------------------------------------------------
# Supabase -> Project Settings -> Database -> Connection string -> URI
# Use the Session pooler URI on Vercel, for example:
# postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Opening a fresh TLS connection to Supabase on every request is slow (several
# network round trips before the first query can run). A warm Vercel instance
# now keeps its connection for DB_CONN_MAX_AGE seconds and reuses it, and
# conn_health_checks drops one that Supabase/Vercel closed in the meantime.
# If Supabase ever reports "max clients reached", set DB_CONN_MAX_AGE=0 in the
# environment to go back to one connection per request.
DB_CONN_MAX_AGE = int(os.environ.get("DB_CONN_MAX_AGE", "60"))

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=DB_CONN_MAX_AGE,
            conn_health_checks=DB_CONN_MAX_AGE > 0,
            ssl_require=True,
        )
    }
else:
    # Local fallback so the project runs before Supabase is wired up.
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
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"

# Serverless (Vercel) has no build step that reliably survives into the
# running function, so this project does not depend on collectstatic.
# WHITENOISE_USE_FINDERS makes WhiteNoise serve files straight out of
# STATICFILES_DIRS (the committed static/ folder) at request time - that
# folder is guaranteed to be present because it's part of the source tree.
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# Static files get a long browser cache so the stylesheet is downloaded once,
# not on every visit. That is safe because templates link to it as
# app.css?v=<hash of the file> (see context_processors.asset_version), so any
# edit to the file produces a new URL.
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365

# Plain (non-manifest) storage. A manifest backend raises a hard ValueError
# from any {% static %} tag whose file isn't listed in staticfiles.json,
# and that file is only produced by collectstatic - which never runs here.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

# Uploaded Excel files are processed in memory (Vercel's filesystem is read-only).
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

# Default country code used when building wa.me links.
WHATSAPP_COUNTRY_CODE = os.environ.get("WHATSAPP_COUNTRY_CODE", "91")
