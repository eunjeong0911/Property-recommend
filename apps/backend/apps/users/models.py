from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    구글 소셜 로그인 사용자 모델
    - email을 unique identifier로 사용
    - AbstractUser를 확장하여 기본 필드 상속
    """
    # Email을 unique identifier로 사용하기 위해 override
    email = models.EmailField(
        unique=True,
        help_text="이메일 주소 (로그인 ID)"
    )

    # 구글 로그인 관련 필드
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Google OAuth Provider Account ID"
    )
    profile_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Google 프로필 이미지 URL"
    )
    profile_image_file = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
        help_text="사용자가 업로드한 프로필 이미지 데이터"
    )
    profile_image_mime = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="프로필 이미지 MIME 타입"
    )

    # 사용자 상태 필드
    is_new_user = models.BooleanField(
        default=True,
        help_text="신규 사용자 여부 (첫 로그인 시 True)"
    )
    survey_completed = models.BooleanField(
        default=False,
        help_text="선호도 설문 완료 여부"
    )

    # 선호도 정보
    job_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ('직장인', '직장인'),
            ('학생', '학생'),
            ('취준생', '취준생'),
            ('프리랜서', '프리랜서'),
            ('자영업', '자영업'),
        ],
        help_text="직업 유형"
    )

    # 메타 정보
    updated_at = models.DateTimeField(auto_now=True, help_text="마지막 수정 시간")

    # email을 로그인 식별자로 사용
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return f"{self.email} ({self.username})"


class LoginHistory(models.Model):
    """
    로그인/로그아웃 이력
    - 사용자의 접속 기록 추적
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_histories',
        help_text="사용자"
    )
    action = models.CharField(
        max_length=10,
        choices=[('login', '로그인'), ('logout', '로그아웃')],
        help_text="행동 유형"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="접속 IP 주소"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="브라우저 User-Agent"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시간")

    class Meta:
        db_table = 'login_histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = '로그인 이력'
        verbose_name_plural = '로그인 이력 목록'

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.created_at}"


class SearchHistory(models.Model):
    """
    매물 검색 이력
    - 검색 조건을 JSONField로 유연하게 저장
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='search_histories',
        help_text="사용자"
    )
    search_conditions = models.JSONField(
        help_text="검색 조건 JSON (예: {region, price_min, price_max, room_type})"
    )
    result_count = models.IntegerField(
        default=0,
        help_text="검색 결과 개수"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="검색 시간")

    class Meta:
        db_table = 'search_histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = '검색 이력'
        verbose_name_plural = '검색 이력 목록'

    def __str__(self):
        return f"{self.user.email} - Search at {self.created_at}"


class ListingViewHistory(models.Model):
    """
    매물 조회 이력
    - 어떤 매물을 얼마나 자세히 봤는지 추적
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listing_view_histories',
        help_text="사용자"
    )
    listing_id = models.CharField(
        max_length=255,
        help_text="매물 ID"
    )
    view_duration = models.IntegerField(
        null=True,
        blank=True,
        help_text="조회 시간(초)"
    )
    scroll_depth = models.IntegerField(
        null=True,
        blank=True,
        help_text="스크롤 깊이(%)"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="조회 시간")

    class Meta:
        db_table = 'listing_view_histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['listing_id']),
        ]
        verbose_name = '매물 조회 이력'
        verbose_name_plural = '매물 조회 이력 목록'

    def __str__(self):
        return f"{self.user.email} - Listing {self.listing_id} at {self.created_at}"


class Wishlist(models.Model):
    """
    찜 목록 (현재 상태)
    - 사용자가 현재 찜한 매물 목록
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlists',
        help_text="사용자"
    )
    listing_id = models.CharField(
        max_length=255,
        help_text="매물 ID"
    )
    memo = models.TextField(
        null=True,
        blank=True,
        help_text="사용자 메모"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="찜한 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")

    class Meta:
        db_table = 'wishlists'
        unique_together = [('user', 'listing_id')]
        ordering = ['-created_at']
        verbose_name = '찜 목록'
        verbose_name_plural = '찜 목록'

    def __str__(self):
        return f"{self.user.email} - Listing {self.listing_id}"


class WishlistHistory(models.Model):
    """
    찜 목록 변경 이력
    - 찜 추가/삭제의 전체 이력 추적
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_histories',
        help_text="사용자"
    )
    listing_id = models.CharField(
        max_length=255,
        help_text="매물 ID"
    )
    action = models.CharField(
        max_length=10,
        choices=[('add', '추가'), ('remove', '삭제')],
        help_text="행동 유형"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="발생 시간")

    class Meta:
        db_table = 'wishlist_histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = '찜 목록 이력'
        verbose_name_plural = '찜 목록 이력 목록'

    def __str__(self):
        return f"{self.user.email} - {self.action} Listing {self.listing_id}"


class PreferenceSurvey(models.Model):
    """
    선호도 설문 응답
    - 신규 사용자의 선호도 조사 결과 저장
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='preference_surveys',
        help_text="사용자"
    )
    priorities = models.JSONField(
        help_text="선호도 우선순위 JSON (예: {주변공원: 1, 편의시설: 2})"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="설문 응답 시간")

    class Meta:
        db_table = 'preference_surveys'
        ordering = ['-created_at']
        verbose_name = '선호도 설문'
        verbose_name_plural = '선호도 설문 목록'

    def __str__(self):
        return f"{self.user.email} - Survey at {self.created_at}"
