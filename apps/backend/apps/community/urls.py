from django.urls import path
from . import views

urlpatterns = [
    # 게시글
    path('posts/', views.CommunityPostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', views.CommunityPostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/like/', views.CommunityPostLikeView.as_view(), name='post-like'),

    # 댓글
    path('posts/<int:post_id>/comments/', views.CommunityCommentView.as_view(), name='comments'),
    path('comments/<int:comment_id>/', views.CommunityCommentDetailView.as_view(), name='comment-detail'),
]

