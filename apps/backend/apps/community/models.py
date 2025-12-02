from django.db import models
from apps.users.models import User


class CommunityPost(models.Model):
    """
    커뮤니티 게시글
    - 사용자들이 작성하는 게시글
    """
    BOARD_TYPE_CHOICES = [
        ('free', '자유게시판'),
        ('region', '행정동 커뮤니티'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_posts',
        help_text="작성자"
    )
    board_type = models.CharField(
        max_length=20,
        choices=BOARD_TYPE_CHOICES,
        default='free',
        help_text="게시판 종류"
    )
    title = models.CharField(max_length=200, help_text="게시글 제목")
    content = models.TextField(help_text="게시글 내용")
    region = models.CharField(max_length=50, null=True, blank=True, help_text="지역 (시/도)")
    dong = models.CharField(max_length=50, null=True, blank=True, help_text="행정동")
    complex_name = models.CharField(max_length=100, null=True, blank=True, help_text="단지명")

    # 게시글 메타
    view_count = models.IntegerField(default=0, help_text="조회수")
    like_count = models.IntegerField(default=0, help_text="좋아요 수")

    created_at = models.DateTimeField(auto_now_add=True, help_text="작성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")
    is_deleted = models.BooleanField(default=False, help_text="삭제 여부 (소프트 삭제)")

    class Meta:
        db_table = 'community_posts'
        ordering = ['-created_at']
        verbose_name = '커뮤니티 게시글'
        verbose_name_plural = '커뮤니티 게시글 목록'

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class CommunityComment(models.Model):
    """
    커뮤니티 댓글
    - 게시글에 대한 댓글
    """
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="게시글"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_comments',
        help_text="작성자"
    )
    content = models.TextField(help_text="댓글 내용")

    created_at = models.DateTimeField(auto_now_add=True, help_text="작성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")
    is_deleted = models.BooleanField(default=False, help_text="삭제 여부 (소프트 삭제)")

    class Meta:
        db_table = 'community_comments'
        ordering = ['created_at']
        verbose_name = '커뮤니티 댓글'
        verbose_name_plural = '커뮤니티 댓글 목록'

    def __str__(self):
        return f"Comment on '{self.post.title}' by {self.user.email}"
