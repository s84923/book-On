# Generated by Django 4.1.1 on 2025-07-09 02:58

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboro', '0004_transactionrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='favorite_users',
            field=models.ManyToManyField(blank=True, related_name='favorite_books', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='books',
            field=models.ManyToManyField(through='onboro.TransactionRecord', to='onboro.book'),
        ),
    ]
