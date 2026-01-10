import os
from django.core.wsgi import get_wsgi_application

# 기본 세팅은 prod로 설정 (필요하면 환경변수로 덮어쓰기)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

application = get_wsgi_application()
