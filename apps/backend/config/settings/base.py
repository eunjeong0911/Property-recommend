import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# Security Settings (Requirements 3.1, 3.2)
# =============================================================================
# DEBUG: Must be False in production
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

# SECRET_KEY: Required in production, no hardcoded default
# In production, this MUST be set via environment variable
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    # Only allow missing SECRET_KEY in development
    if DEBUG:
        SECRET_KEY = "dev-secret-key-not-for-production"
    else:
        raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

# ALLOWED_HOSTS: Required in production
# Format: comma-separated list (e.g., "api.example.com,www.example.com")
_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(",") if host.strip()]
else:
    # Development defaults
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend"]

# Production security settings (only when DEBUG=False)
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in ("true", "1", "yes")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    
    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Content security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# Custom User Model
AUTH_USER_MODEL = "users.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "apps.users",
    "apps.listings",
    "apps.recommend",
    "apps.graph",
    "apps.community",
    "apps.search",
    "apps.health",
]

MIDDLEWARE = [
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

# =============================================================================
# Database Configuration (Requirements 3.1, 3.2)
# =============================================================================
# Support both DATABASE_URL (production) and individual env vars (development)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL for production (AWS RDS, etc.)
    # Format: postgres://user:password@host:port/dbname
    import urllib.parse
    url = urllib.parse.urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": url.path[1:],  # Remove leading '/'
            "USER": url.username,
            "PASSWORD": url.password,
            "HOST": url.hostname,
            "PORT": url.port or 5432,
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    # Individual environment variables for development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("POSTGRES_HOST"),
            "PORT": os.getenv("POSTGRES_PORT"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }

# Neo4j 설정 (Django 백엔드에서 GraphDB 접근 시 사용)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")      # Neo4j 접속 주소
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")                # Neo4j 사용자 ID
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")                 # Neo4j 비밀번호 (환경변수 필수)

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (user uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# CORS Settings (Requirements 6.1)
# =============================================================================
# In production, CORS_ALLOWED_ORIGINS must be set via environment variable
# Format: comma-separated list of origins (e.g., "https://example.com,https://api.example.com")
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
else:
    # Development defaults only - NOT for production
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

CORS_ALLOW_CREDENTIALS = True

# Google OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# =============================================================================
# Logging Configuration (Requirements 5.1, 5.3)
# =============================================================================
# JSON-formatted logging for CloudWatch Logs compatibility
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s",
            "rename_fields": {
                "levelname": "level",
                "asctime": "timestamp",
            },
            "timestamp": True,
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        },
        "console_standard": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console_json"] if os.getenv("LOG_FORMAT", "json") == "json" else ["console_standard"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console_json"] if os.getenv("LOG_FORMAT", "json") == "json" else ["console_standard"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console_json"] if os.getenv("LOG_FORMAT", "json") == "json" else ["console_standard"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
