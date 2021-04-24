# Generated by Django 3.1.7 on 2021-03-30 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Foo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attr1', models.IntegerField()),
                ('attr2', models.CharField(max_length=255)),
                ('attr3', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Bar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attr1', models.IntegerField()),
                ('attr2', models.CharField(max_length=255)),
                ('attr3', models.FloatField(blank=True, null=True)),
                ('foo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='foo.foo')),
            ],
        ),
    ]