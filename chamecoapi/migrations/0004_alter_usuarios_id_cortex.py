# Generated by Django 5.1 on 2024-09-03 03:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chamecoapi', '0003_usuarios_nome'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuarios',
            name='id_cortex',
            field=models.IntegerField(unique=True),
        ),
    ]
