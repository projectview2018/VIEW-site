# Generated by Django 2.0.2 on 2018-02-25 02:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blindspotapp', '0003_remove_vehicles_vseries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicles',
            name='fullvin',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='vehicles',
            name='partialvin',
            field=models.CharField(max_length=100),
        ),
    ]
