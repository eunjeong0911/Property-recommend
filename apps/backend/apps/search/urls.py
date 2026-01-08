from django.urls import path
from .views import UserSearchLogView

urlpatterns = [
    path('log/', UserSearchLogView.as_view(), name='search-log'),
]
