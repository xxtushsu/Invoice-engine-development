# Generated by Django 3.1.7 on 2021-04-27 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0022_auto_20210416_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contractperson',
            name='percentage_of_total',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
