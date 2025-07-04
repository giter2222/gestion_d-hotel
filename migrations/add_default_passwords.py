from django.db import migrations

def add_default_passwords(apps, schema_editor):
    Client = apps.get_model('hotel', 'Client')
    # Set default password as 'password123' for all existing clients
    for client in Client.objects.all():
        client.password = 'password123'
        client.save()

def reverse_default_passwords(apps, schema_editor):
    Client = apps.get_model('hotel', 'Client')
    # Clear passwords (not really necessary but good practice for reverse migration)
    for client in Client.objects.all():
        client.password = ''
        client.save()

class Migration(migrations.Migration):
    dependencies = [
        ('hotel', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        migrations.RunPython(add_default_passwords, reverse_default_passwords),
    ] 