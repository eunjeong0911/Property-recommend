from .base import *

# =============================================================================
# Production Settings (Requirements 3.2, 6.2)
# =============================================================================

# DEBUG must be False in production
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")
if DEBUG:
    import warnings
    warnings.warn("DEBUG is True in production settings! Set DJANGO_DEBUG=False")

# ALLOWED_HOSTS from environment variable (comma-separated)
_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(",") if h.strip()]

# Ensure ALLOWED_HOSTS is not empty in production
if not ALLOWED_HOSTS and not DEBUG:
    raise ValueError("DJANGO_ALLOWED_HOSTS environment variable is required in production")

# =============================================================================
# Security Settings for Production (Requirements 6.2)
# =============================================================================
# CSRF protection
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    origin.strip() 
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") 
    if origin.strip()
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS (only enable if using HTTPS)
if os.getenv("ENABLE_HSTS", "False").lower() in ("true", "1", "yes"):
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# AWS ALB의 HTTPS 헤더 신뢰 설정 (무한 리다이렉트 해결)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
