# Generated by Django 4.2.6 on 2023-10-15 19:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_alter_review_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='review',
            old_name='user',
            new_name='profile',
        ),
    ]
