# Generated by Django 2.0 on 2018-02-21 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fullvin', models.IntegerField()),
                ('partialvin', models.IntegerField()),
                ('vmake', models.CharField(max_length=100)),
                ('vmodel', models.CharField(max_length=100)),
                ('vseries', models.CharField(max_length=100)),
                ('vgvwr', models.CharField(max_length=100)),
                ('when', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
            ],
        ),
        migrations.AlterField(
            model_name='greeting',
            name='when',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date created'),
        ),
    ]
