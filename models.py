from django.db import models
from django.utils import timezone

#class Chambre(models.Model):
  #  numero = models.CharField(max_length=10)
  #  type = models.CharField(max_length=50)
  #  prix_par_nuit = models.DecimalField(max_digits=6, decimal_places=2)
  #  disponible = models.BooleanField(default=True)

   # def __str__(self):
    #    return f"Chambre {self.numero}" 
class Chambre(models.Model):
    TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ]
    
    numero = models.CharField(max_length=10)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    prix_par_nuit = models.DecimalField(max_digits=6, decimal_places=2)
    disponible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Chambre {self.numero}"

    def est_disponible(self, date_arrivee, date_depart):
        """
        Vérifie si la chambre est disponible pour les dates données
        """
        # Vérifier si la chambre est marquée comme disponible
        if not self.disponible:
            return False
            
        # Vérifier les réservations existantes qui se chevauchent
        reservations_existantes = Reservation.objects.filter(
            chambre=self,
            statut__in=['en_attente', 'confirmee'],
            date_arrivee__lt=date_depart,
            date_depart__gt=date_arrivee
        )
        
        return not reservations_existantes.exists()
    
    def get_dates_disponibles(self):
        """
        Retourne une liste des dates disponibles pour les 30 prochains jours
        """
        from datetime import date, timedelta
        dates_disponibles = []
        aujourd_hui = date.today()
        
        for i in range(30):  # Vérifier les 30 prochains jours
            date_a_verifier = aujourd_hui + timedelta(days=i)
            if self.est_disponible(date_a_verifier, date_a_verifier + timedelta(days=1)):
                dates_disponibles.append(date_a_verifier)
                
        return dates_disponibles

class Client(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class Reservation(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE)
    date_arrivee = models.DateField()
    date_depart = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    created_at = models.DateTimeField(default=timezone.now)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.client.nom} - {self.chambre.numero} ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
        # Calculate montant_total before saving
        if self.date_arrivee and self.date_depart and self.chambre:
            nombre_nuits = (self.date_depart - self.date_arrivee).days
            self.montant_total = nombre_nuits * self.chambre.prix_par_nuit
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']

  # Add this import at the top of your models.py

import uuid
from django.db import models

class Facture(models.Model): 
    PAYMENT_METHODS = [
        ('paypal', 'PayPal'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('stripe', 'Stripe'),
    ]

    id_facture = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate a unique transaction_id if not provided
        if not self.transaction_id:
            while True:
                generated_id = str(uuid.uuid4())
                if not Facture.objects.filter(transaction_id=generated_id).exists():
                    self.transaction_id = generated_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Facture #{self.id_facture} - {self.client.nom}"



