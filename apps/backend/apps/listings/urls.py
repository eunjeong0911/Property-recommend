from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LandViewSet

router = DefaultRouter()
router.register(r'lands', LandViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
