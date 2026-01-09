from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LandViewSet
from .views.image_proxy import proxy_image

router = DefaultRouter()
router.register(r'lands', LandViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('proxy-image/', proxy_image, name='proxy-image'),
]
