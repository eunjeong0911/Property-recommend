from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='board_type',
            field=models.CharField(choices=[('free', '자유게시판'), ('region', '행정동 커뮤니티')], default='free', help_text='게시판 종류', max_length=20),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='complex_name',
            field=models.CharField(blank=True, help_text='단지명', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='dong',
            field=models.CharField(blank=True, help_text='행정동', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='communitypost',
            name='region',
            field=models.CharField(blank=True, help_text='지역 (시/도)', max_length=50, null=True),
        ),
    ]
