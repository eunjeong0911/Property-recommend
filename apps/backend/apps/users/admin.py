from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, LoginHistory, SearchHistory, ListingViewHistory,
    Wishlist, WishlistHistory, PreferenceSurvey
)

BASE_USER_READONLY_FIELDS = getattr(BaseUserAdmin, 'readonly_fields', ())


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """사용자 Admin"""
    list_display = ['email', 'username', 'is_new_user', 'survey_completed', 'job_type', 'date_joined']
    list_filter = ['is_new_user', 'survey_completed', 'job_type', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'google_id']
    ordering = ['-date_joined']
    readonly_fields = BASE_USER_READONLY_FIELDS + ('profile_image_file', 'profile_image_mime')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('구글 로그인 정보', {'fields': ('google_id', 'profile_image')}),
        ('프로필 이미지', {'fields': ('profile_image_file', 'profile_image_mime')}),
        ('사용자 상태', {'fields': ('is_new_user', 'survey_completed', 'job_type')}),
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """로그인 이력 Admin"""
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """검색 이력 Admin"""
    list_display = ['user', 'result_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ListingViewHistory)
class ListingViewHistoryAdmin(admin.ModelAdmin):
    """매물 조회 이력 Admin"""
    list_display = ['user', 'listing_id', 'view_duration', 'scroll_depth', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'listing_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """찜 목록 Admin"""
    list_display = ['user', 'listing_id', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'listing_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WishlistHistory)
class WishlistHistoryAdmin(admin.ModelAdmin):
    """찜 목록 이력 Admin"""
    list_display = ['user', 'listing_id', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'listing_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(PreferenceSurvey)
class PreferenceSurveyAdmin(admin.ModelAdmin):
    """선호도 설문 Admin"""
    list_display = ['user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
