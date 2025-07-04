from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chambres/', views.chambre_list, name='chambre_list'),
    path('chambres/new/', views.chambre_create, name='chambre_create'),
    path('chambres/<int:pk>/edit/', views.chambre_update, name='chambre_update'),
    path('chambres/<int:pk>/delete/', views.chambre_delete, name='chambre_delete'),
    path('register/', views.register_client, name='register_client'),
    path('login/', views.client_login, name='client_login'),
    path('account/', views.client_account, name='client_account'),
    path('logout/', views.client_logout, name='client_logout'),
    path('reserver/<int:chambre_id>/', views.reserver_chambre, name='reserver_chambre'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),
    path('facture/create/<int:reservation_id>/', views.facture_create, name='facture_create'),
    path('reservation/<int:reservation_id>/pdf/', views.generate_reservation_pdf, name='generate_reservation_pdf'),
    re_path(r'^delete_reservation/(?P<reservation_id>\d+)/$', views.delete_reservation, name='delete_reservation'),
    path('recherche/', views.rechercher_chambre, name='recherche'),
    # Admin URLs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/chambre/add/', views.admin_add_chambre, name='admin_add_chambre'),
    path('admin/chambre/<int:chambre_id>/edit/', views.admin_edit_chambre, name='admin_edit_chambre'),
    path('admin/chambre/<int:chambre_id>/delete/', views.admin_delete_chambre, name='admin_delete_chambre'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),

    # Vous pouvez ajouter de la même manière pour Clients et Réservations
    path('chambres/', views.chambres_disponibles, name='chambres_disponibles'),
]
