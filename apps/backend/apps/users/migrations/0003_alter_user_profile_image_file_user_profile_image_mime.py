from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_profile_image_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_image_file',
            field=models.BinaryField(blank=True, editable=False, help_text='사용자가 업로드한 프로필 이미지 데이터', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_image_mime',
            field=models.CharField(blank=True, help_text='프로필 이미지 MIME 타입', max_length=100, null=True),
        ),
    ]
