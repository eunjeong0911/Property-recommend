import base64
from rest_framework import serializers
from .models import CommunityPost, CommunityComment


class CommunityCommentSerializer(serializers.ModelSerializer):
    """커뮤니티 댓글 시리얼라이저"""
    author_name = serializers.CharField(source='user.username', read_only=True)
    author_email = serializers.CharField(source='user.email', read_only=True)
    author_profile_image = serializers.SerializerMethodField()

    class Meta:
        model = CommunityComment
        fields = ['id', 'content', 'author_name', 'author_email', 'author_profile_image', 'created_at', 'updated_at', 'is_deleted']
        read_only_fields = ['id', 'author_name', 'author_email', 'author_profile_image', 'created_at', 'updated_at']

    def get_author_profile_image(self, obj):
        if obj.user.profile_image_file:
            encoded = base64.b64encode(obj.user.profile_image_file).decode('utf-8')
            mime = obj.user.profile_image_mime or 'application/octet-stream'
            return f'data:{mime};base64,{encoded}'
        return obj.user.profile_image


class CommunityPostSerializer(serializers.ModelSerializer):
    """커뮤니티 게시글 시리얼라이저"""
    author_name = serializers.CharField(source='user.username', read_only=True)
    author_email = serializers.CharField(source='user.email', read_only=True)
    author_profile_image = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    comments = CommunityCommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'title', 'content', 'author_name', 'author_email', 'author_profile_image',
            'board_type', 'region', 'dong', 'complex_name',
            'view_count', 'like_count', 'comment_count', 'comments',
            'is_liked', 'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'author_name', 'author_email', 'author_profile_image', 'view_count', 'like_count', 'created_at', 'updated_at']

    def get_author_profile_image(self, obj):
        if obj.user.profile_image_file:
            encoded = base64.b64encode(obj.user.profile_image_file).decode('utf-8')
            mime = obj.user.profile_image_mime or 'application/octet-stream'
            return f'data:{mime};base64,{encoded}'
        return obj.user.profile_image

    def get_comment_count(self, obj):
        """삭제되지 않은 댓글 수"""
        return obj.comments.filter(is_deleted=False).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()

    def validate(self, attrs):
        board_type = attrs.get('board_type') or getattr(self.instance, 'board_type', 'free')
        if board_type != 'region':
            attrs['region'] = None
            attrs['dong'] = None
            attrs['complex_name'] = None
        return attrs


class CommunityPostListSerializer(serializers.ModelSerializer):
    """커뮤니티 게시글 목록용 시리얼라이저 (comments 제외)"""
    author_name = serializers.CharField(source='user.username', read_only=True)
    author_profile_image = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'title', 'content', 'author_name', 'author_profile_image',
            'board_type', 'region', 'dong', 'complex_name',
            'view_count', 'like_count', 'comment_count', 'is_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_name', 'author_profile_image', 'view_count', 'like_count', 'created_at', 'updated_at']

    def get_author_profile_image(self, obj):
        if obj.user.profile_image_file:
            encoded = base64.b64encode(obj.user.profile_image_file).decode('utf-8')
            mime = obj.user.profile_image_mime or 'application/octet-stream'
            return f'data:{mime};base64,{encoded}'
        return obj.user.profile_image

    def get_comment_count(self, obj):
        """삭제되지 않은 댓글 수"""
        return obj.comments.filter(is_deleted=False).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()
