"""
Django settings for bizops project.

Security hardened configuration following OWASP best practices.
"""

from pathlib import Path

import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Environment detection (development, staging, production)
ENVIRONMENT = config("ENVIRONMENT", default="development")

# SECURITY: No default SECRET_KEY - must be set in environment
# Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = config("SECRET_KEY")  # Will raise error if not set

# SECURITY: DEBUG defaults to False - must explicitly enable
DEBUG = config("DEBUG", default=False, cast=bool)

# Validate DEBUG is not enabled in production
if ENVIRONMENT == "production" and DEBUG:
    raise ValueError("DEBUG cannot be True in production environment")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
    "django_extensions",
    "encrypted_model_fields",
    # Local apps
    "deadlines",
]

# Field-level encryption for sensitive data (CC numbers, SSNs, etc.)
FIELD_ENCRYPTION_KEY = config("FIELD_ENCRYPTION_KEY", default="")

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "bizops.urls"

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
                "deadlines.context_processors.urgency_stats",
            ],
        },
    },
]

WSGI_APPLICATION = "bizops.wsgi.application"

# =============================================================================
# DATABASE
# =============================================================================

if config("DATABASE_URL", default=None):
    DATABASES = {
        "default": dj_database_url.config(
            default=config("DATABASE_URL"), conn_max_age=600
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # SECURITY: Require email verification
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/"

# Microsoft SSO Configuration
SOCIALACCOUNT_PROVIDERS = {
    "microsoft": {
        "APP": {
            "client_id": config("MICROSOFT_CLIENT_ID", default=""),
            "secret": config("MICROSOFT_CLIENT_SECRET", default=""),
            "settings": {
                "tenant": config("MICROSOFT_TENANT_ID", default="common"),
            },
        },
        "SCOPE": ["User.Read"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# =============================================================================
# SESSION SECURITY (PCI DSS Requirement 8.1.8)
# =============================================================================

SESSION_COOKIE_AGE = 900  # 15 minutes
SESSION_SAVE_EVERY_REQUEST = True  # Reset timeout on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# =============================================================================
# FILE UPLOAD LIMITS
# =============================================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# =============================================================================
# SECURITY HEADERS (Always applied)
# =============================================================================

# Clickjacking protection
X_FRAME_OPTIONS = "DENY"

# Prevent MIME-type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer policy - don't leak URLs
SECURE_REFERRER_POLICY = "same-origin"

# =============================================================================
# HTTPS/TLS SECURITY (Production only)
# =============================================================================

if ENVIRONMENT == "production" or not DEBUG:
    # HTTPS settings (Cloud Run terminates SSL at load balancer)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS - enforce HTTPS for 1 year
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# CSRF CONFIGURATION
# =============================================================================

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# =============================================================================
# LOGGING (Security audit trail)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
        "security": {
            "format": "{asctime} SECURITY {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "security_console": {
            "class": "logging.StreamHandler",
            "formatter": "security",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "security.audit": {
            "handlers": ["security_console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
