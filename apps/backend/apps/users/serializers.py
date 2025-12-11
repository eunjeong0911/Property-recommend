import base64
from typing import Tuple

from rest_framework import serializers
from .models import (
    User, LoginHistory, SearchHistory, ListingViewHistory,
    Wishlist, WishlistHistory, PreferenceSurvey
)


class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 시리얼라이저"""
    profile_image_data = serializers.SerializerMethodField()
    profile_image_upload = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'google_id', 'profile_image', 'profile_image_data', 'profile_image_mime',
            'is_new_user', 'survey_completed', 'job_type', 'date_joined', 'updated_at',
            'profile_image_upload',
        ]
        read_only_fields = ['id', 'google_id', 'date_joined', 'updated_at', 'profile_image_data']

    def get_profile_image_data(self, obj: User):
        if obj.profile_image_file:
            encoded = base64.b64encode(obj.profile_image_file).decode('utf-8')
            mime = obj.profile_image_mime or 'application/octet-stream'
            return f'data:{mime};base64,{encoded}'
        return None

    def update(self, instance: User, validated_data):
        upload_data = validated_data.pop('profile_image_upload', None)
        instance = super().update(instance, validated_data)

        if upload_data is not None:
            if upload_data == '':
                instance.profile_image_file = None
                instance.profile_image_mime = None
            else:
                mime_type, encoded_payload = self._split_data_uri(upload_data)
                instance.profile_image_file = base64.b64decode(encoded_payload)
                instance.profile_image_mime = mime_type
            instance.save(update_fields=['profile_image_file', 'profile_image_mime'])

        return instance

    def _split_data_uri(self, value: str) -> Tuple[str, str]:
        if value.startswith('data:'):
            header, encoded = value.split(',', 1)
            mime = header.split(';')[0].replace('data:', '') or 'application/octet-stream'
            return mime, encoded
        return 'application/octet-stream', value


class GoogleLoginSerializer(serializers.Serializer):
    """구글 로그인 요청 시리얼라이저"""
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True, max_length=255)
    image = serializers.URLField(required=False, allow_blank=True)
    googleId = serializers.CharField(required=True, max_length=255)


class PreferenceSurveySerializer(serializers.ModelSerializer):
    """선호도 설문 시리얼라이저"""
    class Meta:
        model = PreferenceSurvey
        fields = ['id', 'user', 'priorities', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class SearchHistorySerializer(serializers.ModelSerializer):
    """검색 이력 시리얼라이저"""
    class Meta:
        model = SearchHistory
        fields = ['id', 'search_conditions', 'result_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class ListingViewHistorySerializer(serializers.ModelSerializer):
    """매물 조회 이력 시리얼라이저"""
    class Meta:
        model = ListingViewHistory
        fields = ['id', 'listing_id', 'view_duration', 'scroll_depth', 'created_at']
        read_only_fields = ['id', 'created_at']


class WishlistSerializer(serializers.ModelSerializer):
    """찜 목록 시리얼라이저"""
    class Meta:
        model = Wishlist
        fields = ['id', 'listing_id', 'memo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WishlistHistorySerializer(serializers.ModelSerializer):
    """찜 목록 이력 시리얼라이저"""
    class Meta:
        model = WishlistHistory
        fields = ['id', 'listing_id', 'action', 'created_at']
        read_only_fields = ['id', 'created_at']


class LoginHistorySerializer(serializers.ModelSerializer):
    """로그인 이력 시리얼라이저"""
    class Meta:
        model = LoginHistory
        fields = ['id', 'action', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmailPasswordLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, trim_whitespace=False)
