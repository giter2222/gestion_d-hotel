from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('hotel', '0004_merge_0003_facture_add_default_passwords'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='password',
            field=models.CharField(default='password123', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='client',
            name='date_inscription',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ] 