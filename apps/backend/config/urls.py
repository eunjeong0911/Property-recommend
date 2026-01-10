from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")), 
    path("api/users/", include("apps.users.urls")),
    path("api/listings/", include("apps.listings.urls")),
    path("api/recommend/", include("apps.recommend.urls")),
    path("api/graph/", include("apps.graph.urls")),
    path("api/community/", include("apps.community.urls")),
    # Health check endpoints for AWS ECS/ALB
    path("api/", include("apps.health.urls")),
]

# Media 파일 서빙 (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
