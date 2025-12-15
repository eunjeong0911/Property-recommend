# =============================================================================
# Search App Models - 사용자 검색 로그
# =============================================================================
#
# 역할: 사용자의 검색 질의, 필터 조건, 추천 결과를 저장하여
#       검색 패턴 분석 및 추천 품질 개선에 활용
#
# Requirements: 1.1, 1.2
# =============================================================================

from django.db import models
from django.conf import settings


class UserSearchLog(models.Model):
    """
    사용자 검색 로그 모델
    
    검색 질의, 필터 조건, 결과 매물 ID 목록을 저장하여
    검색 패턴 분석 및 추천 품질 개선에 활용합니다.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_search_logs',
        help_text="검색을 수행한 사용자 (비로그인 시 null)"
    )
    session_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="세션 ID (비로그인 사용자 추적용)"
    )
    query = models.TextField(
        help_text="검색 질의 내용"
    )
    filters = models.JSONField(
        default=dict,
        help_text="적용된 필터 조건 (예: {price_min, price_max, region})"
    )
    result_ids = models.JSONField(
        default=list,
        help_text="결과 매물 ID 목록"
    )
    result_count = models.IntegerField(
        default=0,
        help_text="검색 결과 개수"
    )
    search_duration_ms = models.IntegerField(
        default=0,
        help_text="검색 소요 시간 (밀리초)"
    )
    search_type = models.CharField(
        max_length=50,
        default='rag',
        choices=[
            ('rag', 'RAG 검색'),
            ('es', 'Elasticsearch 검색'),
            ('hybrid', '하이브리드 검색'),
        ],
        help_text="검색 유형"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="검색 시간"
    )

    class Meta:
        db_table = 'user_search_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'user']),
            models.Index(fields=['query']),
            models.Index(fields=['session_id', '-created_at']),
        ]
        verbose_name = '사용자 검색 로그'
        verbose_name_plural = '사용자 검색 로그 목록'

    def __str__(self):
        user_str = self.user.email if self.user else 'anonymous'
        return f"{user_str} - '{self.query[:50]}' at {self.created_at}"
