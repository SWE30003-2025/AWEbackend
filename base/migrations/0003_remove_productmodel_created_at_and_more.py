# Generated by Django 5.2.1 on 2025-06-03 23:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_remove_categorymodel_parentcategory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productmodel',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='productmodel',
            name='updated_at',
        ),
    ]
