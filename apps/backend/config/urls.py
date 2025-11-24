from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/listings/", include("apps.listings.urls")),
    path("api/logs/", include("apps.logs.urls")),
    path("api/recommend/", include("apps.recommend.urls")),
    path("api/graph/", include("apps.graph.urls")),
]
