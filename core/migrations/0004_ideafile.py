# Generated by Django 5.1.5 on 2025-03-02 18:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_category_alter_idea_category_alter_user_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdeaFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='idea_files/')),
                ('idea', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='core.idea')),
            ],
        ),
    ]
