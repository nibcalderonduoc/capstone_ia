from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Página principal para subir el documento
    path('dashboard/', views.dashboard, name='dashboard'),  # Página para mostrar el dashboard de BigQuery
    path('result/', views.result, name='result'),  # Página mostrar resultados
    path('base/', views.base, name='base'),  # Página mostrar header
    path('sidebar/', views.sidebar, name='sidebar'),  # Página mostrar sidebar
    path('content/', views.content, name='content'),  # Página mostrar content
    path('infostoric/', views.infostoric, name='infostoric'),  # Página mostrar infostoric
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),  # Página mostrar recomendaciones
]
