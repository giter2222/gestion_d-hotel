from django.db import migrations

def populate_montant_total(apps, schema_editor):
    Reservation = apps.get_model('hotel', 'Reservation')
    for reservation in Reservation.objects.all():
        if reservation.date_arrivee and reservation.date_depart and reservation.chambre:
            nombre_nuits = (reservation.date_depart - reservation.date_arrivee).days
            reservation.montant_total = nombre_nuits * reservation.chambre.prix_par_nuit
            reservation.save()

def reverse_populate_montant_total(apps, schema_editor):
    Reservation = apps.get_model('hotel', 'Reservation')
    Reservation.objects.all().update(montant_total=None)

class Migration(migrations.Migration):
    dependencies = [
        ('hotel', '0009_reservation_montant_total'),
    ]

    operations = [
        migrations.RunPython(populate_montant_total, reverse_populate_montant_total),
    ] 