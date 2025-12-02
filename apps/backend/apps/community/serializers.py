from rest_framework import serializers
from .models import CommunityPost, CommunityComment


class CommunityCommentSerializer(serializers.ModelSerializer):
    """커뮤니티 댓글 시리얼라이저"""
    author_name = serializers.CharField(source='user.username', read_only=True)
    author_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CommunityComment
        fields = ['id', 'content', 'author_name', 'author_email', 'created_at', 'updated_at', 'is_deleted']
        read_only_fields = ['id', 'author_name', 'author_email', 'created_at', 'updated_at']


class CommunityPostSerializer(serializers.ModelSerializer):
    """커뮤니티 게시글 시리얼라이저"""
    author_name = serializers.CharField(source='user.username', read_only=True)
    author_email = serializers.CharField(source='user.email', read_only=True)
    comment_count = serializers.SerializerMethodField()
    comments = CommunityCommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'title', 'content', 'author_name', 'author_email',
            'board_type', 'region', 'dong', 'complex_name',
            'view_count', 'like_count', 'comment_count', 'comments',
            'is_liked', 'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'author_name', 'author_email', 'view_count', 'like_count', 'created_at', 'updated_at']

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
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'title', 'content', 'author_name',
            'board_type', 'region', 'dong', 'complex_name',
            'view_count', 'like_count', 'comment_count', 'is_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author_name', 'view_count', 'like_count', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        """삭제되지 않은 댓글 수"""
        return obj.comments.filter(is_deleted=False).count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or request.user.is_anonymous:
            return False
        return obj.likes.filter(user=request.user).exists()
