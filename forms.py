from django import forms
from .models import Chambre, Client, Reservation , Facture
from django.utils import timezone
from django import forms
from django.core.exceptions import ValidationError
from .models import Facture

# Form for the Chambre model
class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = ['numero', 'type', 'prix_par_nuit', 'disponible']
        widgets = {
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
               
            'type': forms.Select(choices=Chambre.TYPE_CHOICES),
        }
        


# Form for the Client model
class ClientForm(forms.ModelForm):
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe'
        })
    )
    confirm_password = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe'
        })
    )

    class Meta:
        model = Client
        fields = ['nom', 'email', 'telephone', 'password']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez votre nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez votre email'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez votre numéro de téléphone'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez votre mot de passe'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        if password and len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = self.cleaned_data['password']
        if commit:
            user.save()
        return user

# Form for the Reservation model
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date_arrivee', 'date_depart']
        widgets = {
            'date_arrivee': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'date_depart': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        date_arrivee = cleaned_data.get('date_arrivee')
        date_depart = cleaned_data.get('date_depart')

        if date_arrivee and date_depart:
            if date_arrivee < timezone.now().date():
                raise forms.ValidationError("La date d'arrivée ne peut pas être dans le passé.")
            
            if date_depart <= date_arrivee:
                raise forms.ValidationError("La date de départ doit être après la date d'arrivée.")
            
            # Vérifier que la durée du séjour n'excède pas 30 jours
            duree = (date_depart - date_arrivee).days
            if duree > 30:
                raise forms.ValidationError("La durée du séjour ne peut pas excéder 30 jours.")

        return cleaned_data

class ClientLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre email'
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe'
        })
    )




class FactureForm(forms.ModelForm):
    transaction_id = forms.CharField(
        label='Transaction ID',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez l\'ID de transaction',
            'pattern': '[A-Za-z0-9-]+',
            'title': 'L\'ID de transaction doit contenir uniquement des lettres, chiffres et tirets'
        })
    )

    # Champs personnalisés (non stockés en base de données)
    paypal_email = forms.EmailField(required=False, label='Email PayPal', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@paypal.com'}))
    visa_number = forms.CharField(required=False, label='Numéro Visa', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234 5678 9012 3456'}))
    mastercard_number = forms.CharField(required=False, label='Numéro MasterCard', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234 5678 9012 3456'}))
    stripe_token = forms.CharField(required=False, label='Token Stripe', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tok_xxxx'}))

    class Meta:
        model = Facture
        fields = ['method', 'transaction_id']

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')

        if method == 'paypal' and not cleaned_data.get('paypal_email'):
            raise ValidationError("L'email PayPal est requis pour ce mode de paiement.")
        elif method == 'visa' and not cleaned_data.get('visa_number'):
            raise ValidationError("Le numéro de carte Visa est requis.")
        elif method == 'mastercard' and not cleaned_data.get('mastercard_number'):
            raise ValidationError("Le numéro de carte MasterCard est requis.")
        elif method == 'stripe' and not cleaned_data.get('stripe_token'):
            raise ValidationError("Le token Stripe est requis.")

        return cleaned_data
