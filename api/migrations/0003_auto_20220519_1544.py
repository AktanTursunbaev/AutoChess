# Generated by Django 3.2.13 on 2022-05-19 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_matchinformation_place'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='last_health_decreased',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='player',
            name='last_round',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]