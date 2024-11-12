from django.urls import path
from . import views

urlpatterns = [
    path('index', views.index, name='index'),  # Página principal para subir el documento
    path('dashboard/', views.dashboard, name='dashboard'),  # Página para mostrar el dashboard de BigQuery
    path('result/', views.result, name='result'),  # Página mostrar resultados
    path('base/', views.base, name='base'),  # Página mostrar header
    path('sidebar/', views.sidebar, name='sidebar'),  # Página mostrar sidebar
    path('content/', views.content, name='content'),  # Página mostrar content
    path('infostoric/', views.infostoric, name='infostoric'),  # Página mostrar infostoric
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),  # Página mostrar recomendaciones
    path('get_recommendation/', views.get_recommendation, name='get_recommendation'),  # Esta es la ruta para la API de recomendación
    #insertar paginas de alcance 1, 2 y 3
    path('alcance1/', views.alcance1, name='alcance1'),  # Página mostrar alcance1
    path('alcance2/', views.alcance2, name='alcance2'),  # Página mostrar alcance2
    path('alcance3/', views.alcance3, name='alcance3'),  # Página mostrar alcance3
    path('obtener_datos_bigquery/', views.obtener_datos_bigquery, name='obtener_datos_bigquery'),
    path('upload_to_bigquery/', views.upload_to_bigquery, name='upload_to_bigquery'),
    path('', views.login_view, name='login'), # Página mostrar login
    path('registro/', views.registro, name='registro'), # Página mostrar 
    path('carga-item-alcance3/', views.carga_item_alcance3, name='carga_item_alcance3'),
    path('base-admin/', views.base_admin, name='base_admin'),
    path('registro-admin/', views.registro_admin, name='registro_admin'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('login-admin/', views.login_admin, name='login_admin'),


   
    
    

]
