# Generated by Django 5.2.1 on 2025-06-05 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_alter_usermodel_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmodel',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
