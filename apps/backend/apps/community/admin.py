from django.contrib import admin
from .models import CommunityPost, CommunityComment


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    """커뮤니티 게시글 Admin"""
    list_display = ['id', 'title', 'user', 'view_count', 'like_count', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['title', 'content', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['view_count', 'like_count', 'created_at', 'updated_at']


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    """커뮤니티 댓글 Admin"""
    list_display = ['id', 'post', 'user', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'user__email', 'post__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']