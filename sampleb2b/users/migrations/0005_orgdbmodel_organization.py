# Generated by Django 4.2.3 on 2023-07-17 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_customusermodel_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='orgdbmodel',
            name='organization',
            field=models.ManyToManyField(to='users.organizationmodel'),
        ),
    ]
