# Generated by Django 5.1 on 2024-12-03 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chamecoapi', '0008_chaves_principal'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tokens',
            fields=[
                ('hash_token', models.CharField(max_length=256, primary_key=True, serialize=False)),
                ('id_cortex', models.IntegerField()),
                ('data_expiracao', models.DateTimeField()),
            ],
        ),
    ]
