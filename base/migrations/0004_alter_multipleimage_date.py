# Generated by Django 4.1.7 on 2023-03-27 09:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_multipleimage_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multipleimage',
            name='date',
            field=models.DateField(default=datetime.datetime(2023, 3, 27, 9, 26, 45, 670372)),
        ),
    ]
