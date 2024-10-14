# Generated by Django 5.0 on 2024-10-08 08:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trustcheck', '0004_datatype_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, help_text='Parent Category for hierarchical categorization.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategories', to='trustcheck.category'),
        ),
        migrations.AlterField(
            model_name='datatype',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
