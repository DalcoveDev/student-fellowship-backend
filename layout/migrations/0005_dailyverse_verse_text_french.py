# Generated manually for French daily verse support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layout', '0004_homepagelayout_article_limit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyverse',
            name='verse_text_french',
            field=models.TextField(blank=True, default='', help_text='Verse text in French'),
        ),
    ]
