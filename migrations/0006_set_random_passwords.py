from django.db import migrations
import random
import string

def generate_random_password(length=8):
    # Generate a random password with letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def set_random_passwords(apps, schema_editor):
    Client = apps.get_model('hotel', 'Client')
    # Get all existing clients
    for client in Client.objects.all():
        # Generate a random password
        random_password = generate_random_password()
        # Save the password
        client.password = random_password
        client.save()
        # Print the email and password for reference (will show in migration output)
        print(f"Client {client.email}: {random_password}")

def reverse_random_passwords(apps, schema_editor):
    Client = apps.get_model('hotel', 'Client')
    # Reset passwords to default (not really necessary but good practice for reverse migration)
    for client in Client.objects.all():
        client.password = 'password123'
        client.save()

class Migration(migrations.Migration):
    dependencies = [
        ('hotel', '0005_add_client_fields'),
    ]

    operations = [
        migrations.RunPython(set_random_passwords, reverse_random_passwords),
    ] 