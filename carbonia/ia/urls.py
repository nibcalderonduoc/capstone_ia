from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Página principal para subir el documento
]
