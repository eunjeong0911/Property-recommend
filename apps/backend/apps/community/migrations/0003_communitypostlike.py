from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_profile_image_file'),
        ('community', '0002_communitypost_board_type_communitypost_region_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityPostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='좋아요 시간')),
                ('post', models.ForeignKey(help_text='게시글', on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='community.communitypost')),
                ('user', models.ForeignKey(help_text='사용자', on_delete=django.db.models.deletion.CASCADE, related_name='community_post_likes', to='users.user')),
            ],
            options={
                'verbose_name': '커뮤니티 게시글 좋아요',
                'verbose_name_plural': '커뮤니티 게시글 좋아요 목록',
                'db_table': 'community_post_likes',
            },
        ),
        migrations.AddIndex(
            model_name='communitypostlike',
            index=models.Index(fields=['post', 'user'], name='community__post_id_user_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='communitypostlike',
            unique_together={('post', 'user')},
        ),
    ]
