# Generated by Django 3.1.7 on 2021-04-29 15:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('InvoiceEngineApp', '0030_auto_20210427_0845'),
    ]

    operations = [
        migrations.RenameField(
            model_name='component',
            old_name='next_date_prolong',
            new_name='date_next_prolongation',
        ),
        migrations.RenameField(
            model_name='component',
            old_name='end_date_prolong',
            new_name='date_prolonged_until',
        ),
        migrations.RenameField(
            model_name='contract',
            old_name='next_date_prolong',
            new_name='date_next_prolongation',
        ),
        migrations.RenameField(
            model_name='contract',
            old_name='end_date_prolong',
            new_name='date_prolonged_until',
        ),
        migrations.RenameField(
            model_name='tenancy',
            old_name='day_next_prolong',
            new_name='date_next_prolongation',
        ),
    ]