from django.contrib import admin
from .models import Chambre, Client, Reservation

admin.site.register(Chambre)
admin.site.register(Client)
admin.site.register(Reservation)

