from django.shortcuts import render, redirect, get_object_or_404
from .models import Chambre, Client, Reservation, Facture
from .forms import ChambreForm, ClientForm, ReservationForm, ClientLoginForm, FactureForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.utils import timezone
from django.template.loader import render_to_string, get_template
import pdfkit
from django.conf import settings
import os

from datetime import datetime

def rechercher_chambre(request):
    TYPE_CHOICES = Chambre.TYPE_CHOICES  # Récupère les choix depuis le modèle
    
    if request.method == 'POST':
        try:
            # Récupération des paramètres
            date_arrivee = datetime.strptime(request.POST.get('date_arrivee'), '%Y-%m-%d').date()
            date_depart = datetime.strptime(request.POST.get('date_depart'), '%Y-%m-%d').date()
            type_chambre = request.POST.get('type_chambre')

            # Validation des dates
            if date_arrivee < timezone.now().date():
                raise ValueError("La date d'arrivée doit être dans le futur")
            if date_depart <= date_arrivee:
                raise ValueError("La date de départ doit être après l'arrivée")

            # Filtre de base
            chambres = Chambre.objects.filter(disponible=True)
            
            # Filtre par type si sélectionné (en excluant la valeur vide)
            if type_chambre and type_chambre.strip():
                chambres = chambres.filter(type=type_chambre)

            # Vérification de la disponibilité réelle
            chambres_disponibles = [
                ch for ch in chambres 
                if ch.est_disponible(date_arrivee, date_depart)
            ]

            return render(request, 'resultat_recherche.html', {
                'chambres': chambres_disponibles,
                'date_arrivee': date_arrivee,
                'date_depart': date_depart,
                'TYPE_CHOICES': TYPE_CHOICES  # Envoyer les choix au template
            })

        except ValueError as e:
            messages.error(request, str(e))
    
    # Valeurs par défaut pour le formulaire
    context = {
        'min_date': timezone.now().strftime('%Y-%m-%d'),
        'TYPE_CHOICES': TYPE_CHOICES  # Envoyer les choix au template
    }
    return render(request, 'rechercherchambre.html', context)

# Admin credentials
ADMIN_EMAIL = "admin@grandhorizon.com"
ADMIN_PASSWORD = "admin123"  # In production, use environment variables

# Configure PDFKit with the path to wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

# --- Chambre CRUD ---

def home(request):
    return render(request,"base.html")

def chambre_list(request):
    chambres = Chambre.objects.filter(disponible=True).order_by('numero')
    return render(request, 'chambre_list.html', {'chambres': chambres})

def chambre_create(request):
    if request.method == 'POST':
        form = ChambreForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('chambre_list')
    else:
        form = ChambreForm()
    return render(request, 'chambre_form.html', {'form': form})

def chambre_update(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    if request.method == 'POST':
        form = ChambreForm(request.POST, instance=chambre)
        if form.is_valid():
            form.save()
            return redirect('chambre_list')
    else:
        form = ChambreForm(instance=chambre)
    return render(request, 'chambre_form.html', {'form': form})

def chambre_delete(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    if request.method == 'POST':
        chambre.delete()
        return redirect('chambre_list')
    return render(request, 'chambre_confirm_delete.html', {'chambre': chambre})

# --- Client et Reservation CRUD seront similaires ---

def register_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre compte a été créé avec succès.')
            return redirect('client_login')
    else:
        form = ClientForm()
    return render(request, 'register_client.html', {'form': form})

def client_login(request):
    if request.method == 'POST':
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                client = Client.objects.get(email=email, password=password)
                request.session['client_id'] = client.id
                messages.success(request, 'Connexion réussie!')
                return redirect('client_account')
            except Client.DoesNotExist:
                messages.error(request, 'Email ou mot de passe incorrect.')
    else:
        form = ClientLoginForm()
    return render(request, 'client_login.html', {'form': form})

def client_logout(request):
    try:
        del request.session['client_id']
    except KeyError:
        pass
    return redirect('client_login')

def client_account(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('client_login')
    
    client = Client.objects.get(id=client_id)
    reservations = Reservation.objects.filter(client=client).exclude(statut='annulee').select_related('chambre').order_by('-date_arrivee')
    
    return render(request, 'client_account.html', {
        'client': client,
        'reservations': reservations,
        'today': timezone.now().date()
    })

def reserver_chambre(request, chambre_id):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('client_login')
    chambre = Chambre.objects.get(id=chambre_id)
    client = Client.objects.get(id=client_id)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            # Get the dates from the form
            date_arrivee = form.cleaned_data['date_arrivee']
            date_depart = form.cleaned_data['date_depart']
            
            # Check for overlapping reservations for this client
            # If no overlapping reservations, proceed with creating the new reservation
            reservation = form.save(commit=False)
            reservation.client = client
            reservation.chambre = chambre
            
            # Check if the room is available for these dates
            if not chambre.est_disponible(date_arrivee, date_depart):
                messages.error(request, "Cette chambre n'est pas disponible pour les dates sélectionnées.")
                return render(request, 'reserver_chambre.html', {'form': form, 'chambre': chambre})
            
            reservation.save()
            # Optionnel : mettre la chambre indisponible
            chambre.disponible = False
            chambre.save()
            messages.success(request, "Réservation créée avec succès!")
            return redirect('facture_create', reservation_id=reservation.id)
    else:
        form = ReservationForm()
    return render(request, 'reserver_chambre.html', {'form': form, 'chambre': chambre})

def dashboard_view(request):
    return render(request, 'dashboard.html')

def dashboard_data(request):
    chambres_total = Chambre.objects.count()
    clients_total = Client.objects.count()
    reservations_total = Reservation.objects.count()

    chambres_disponibles = Chambre.objects.filter(disponible=True).count()
    chambres_non_disponibles = Chambre.objects.filter(disponible=False).count()
    types_data = Chambre.objects.values('type').annotate(total= Count('id'))

    data = {
        'chambres_total': chambres_total,
        'clients_total': clients_total,
        'reservations_total': reservations_total,
        'chambres_disponibles': chambres_disponibles,
        'chambres_non_disponibles': chambres_non_disponibles,
        'types_data': list(types_data),
    }
    return JsonResponse(data)

def facture_create(request, reservation_id):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('client_login')

    client = Client.objects.get(id=client_id)
    reservation = Reservation.objects.get(id=reservation_id)

    if request.method == 'POST':
        form = FactureForm(request.POST)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.client = client
            facture.reservation = reservation
            facture.save()
            messages.success(request, "Paiement effectué avec succès.")
            return redirect('client_account')

    else:
        form = FactureForm()

    return render(request, 'facture_form.html', {
        'form': form,
        'reservation': reservation
    })

def delete_reservation(request, reservation_id):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('client_login')
    client = Client.objects.get(id=client_id)
    reservation = get_object_or_404(Reservation, id=reservation_id, client=client  )
    
    reservation.delete()
    messages.success(request, "Réservation supprimée avec succès.")
    return redirect('client_account')

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            messages.error(request, 'Veuillez vous connecter en tant qu\'administrateur.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            request.session['admin_logged_in'] = True
            messages.success(request, 'Connexion réussie.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Email ou mot de passe incorrect.')
    
    return render(request, 'admin_login.html')

@admin_required
def admin_dashboard(request):
    chambres = Chambre.objects.all()
    return render(request, 'admin_dashboard.html', {'chambres': chambres})

@admin_required
def admin_add_chambre(request):
    if request.method == 'POST':
        try:
            numero = request.POST.get('numero')
            type_chambre = request.POST.get('type')
            prix_par_nuit = request.POST.get('prix')
            disponible = request.POST.get('disponible') == 'on'
            
            Chambre.objects.create(
                numero=numero,
                type=type_chambre,
                prix_par_nuit=prix_par_nuit,
                disponible=disponible
            )
            messages.success(request, 'Chambre ajoutée avec succès.')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout de la chambre: {str(e)}')
    
    return render(request, 'admin_add_chambre.html')

@admin_required
def admin_edit_chambre(request, chambre_id):
    chambre = get_object_or_404(Chambre, id=chambre_id)
    
    if request.method == 'POST':
        try:
            chambre.numero = request.POST.get('numero')
            chambre.type = request.POST.get('type')
            chambre.prix_par_nuit = request.POST.get('prix')
            chambre.disponible = request.POST.get('disponible') == 'on'
            chambre.save()
            
            messages.success(request, 'Chambre modifiée avec succès.')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification de la chambre: {str(e)}')
    
    return render(request, 'admin_edit_chambre.html', {'chambre': chambre})

@admin_required
def admin_delete_chambre(request, chambre_id):
    chambre = get_object_or_404(Chambre, id=chambre_id)
    try:
        chambre.delete()
        messages.success(request, 'Chambre supprimée avec succès.')
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression de la chambre: {str(e)}')
    
    return redirect('admin_dashboard')

def admin_logout(request):
    request.session.pop('admin_logged_in', None)
    messages.success(request, 'Déconnexion réussie.')
    return redirect('admin_login')

def chambres_disponibles(request):
    chambres = Chambre.objects.filter(disponible=True).order_by('numero')
    return render(request, 'chambres_disponibles.html', {'chambres': chambres})

def generate_reservation_pdf(request, reservation_id):
    try:
        reservation = Reservation.objects.get(id=reservation_id)
        
        # Calculate total amount
        nombre_nuits = (reservation.date_depart - reservation.date_arrivee).days
        montant_total = nombre_nuits * reservation.chambre.prix_par_nuit
        
        # Try to get the facture if it exists
        try:
            facture = Facture.objects.get(reservation=reservation)
            has_facture = True
        except Facture.DoesNotExist:
            facture = None
            has_facture = False
        
        # Try different possible paths for wkhtmltopdf
        possible_paths = [
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\wkhtmltopdf\bin\wkhtmltopdf.exe'
        ]
        
        wkhtmltopdf_path = None
        for path in possible_paths:
            if os.path.exists(path):
                wkhtmltopdf_path = path
                break
        
        if not wkhtmltopdf_path:
            raise Exception("wkhtmltopdf executable not found. Please ensure it is installed correctly.")
        
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        
        # Prepare the context
        context = {
            'hotel_name': 'Grand Horizon',
            'hotel_address': '123 Rue de la Paix',
            'hotel_phone': '+33 1 23 45 67 89',
            'hotel_email': 'contact@hoteldeluxe.com',
            'reservation': reservation,
            'facture': facture,
            'has_facture': has_facture,
            'client': reservation.client,
            'chambre': reservation.chambre,
            'montant_total': montant_total,
            'nombre_nuits': nombre_nuits,
        }
        
        # Render the template
        template = get_template('reservation_pdf.html')
        html = template.render(context)
        
        # Generate PDF
        pdf = pdfkit.from_string(
            html,
            False,
            options={
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
                'no-outline': None
            },
            configuration=config
        )
        
        # Create the HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reservation_{reservation.id}.pdf"'
        
        return response
        
    except Reservation.DoesNotExist:
        return HttpResponse("Reservation not found")
    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}")













