# Generated by Django 4.2.6 on 2023-10-15 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_review_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='products.profile'),
        ),
    ]
