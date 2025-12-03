from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # 인증 관련
    path('auth/google/', views.GoogleLoginView.as_view(), name='google-login'),
    path('auth/login/', views.EmailPasswordLoginView.as_view(), name='email-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # 사용자 정보
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    path('me/update/', views.UpdateUserView.as_view(), name='update-user'),

    # 선호도 설문
    path('preference-survey/', views.PreferenceSurveyView.as_view(), name='preference-survey'),

    # 검색 이력
    path('history/search/', views.SearchHistoryView.as_view(), name='search-history'),

    # 조회 이력
    path('history/view/', views.ListingViewHistoryView.as_view(), name='view-history'),

    # 찜 목록
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<str:listing_id>/', views.WishlistDetailView.as_view(), name='wishlist-detail'),
]
