from django.urls import path
from . import views
from .views import result

urlpatterns = [
    path('index/', views.index, name='index'),  # Página principal para subir el documento
    path('dashboard/', views.dashboard, name='dashboard'),  # Página para mostrar el dashboard de BigQuery
    path('result/', views.result, name='result'),  # Página mostrar resultados
    #path('dashboard/', views.alcance1_view, name='dashboard'),
    path('base/', views.base, name='base'),  # Página mostrar header
    path('sidebar/', views.sidebar, name='sidebar'),  # Página mostrar sidebar
    path('content/', views.content, name='content'),  # Página mostrar content
    path('infostoric/', views.infostoric, name='infostoric'),  # Página mostrar infostoric
    path('recomendaciones/', views.recomendaciones, name='recomendaciones'),  # Página mostrar recomendaciones
    path('get_recommendation/', views.get_recommendation, name='get_recommendation'),  # Esta es la ruta para la API de recomendación
    #insertar paginas de alcance 1, 2 y 3
    path('alcance1/', views.alcance1, name='alcance1'),  # Página mostrar alcance1
    #path('alcance1/', views.alcance1_view, name='alcance1'),
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
    #path('empresas-registradas/', views.empresas_registradas, name='empresas_registradas'),
    path('sidebar-admin/', views.sidebar_admin, name='sidebar_admin'),
    path('revisar/', result, name='nombre_de_tu_url_a_result'),
    path('get_regions/', views.get_regions, name='get_regions'),
    path('get_provinces/', views.get_provinces, name='get_provinces'),
    path('get_communes/', views.get_communes, name='get_communes'),
    path('get_statistics/', views.get_statistics, name='get_statistics'),
     # Página principal para listar empresas registradas
    path('empresas-registradas/', views.empresas_registradas, name='empresas_registradas'),       
    path('sucursales-registradas/<str:rut_empresa>/', views.sucursales_registradas, name='sucursales_registradas'),
    # Registrar una nueva empresa
    path('registro-empresas/', views.registro_empresa, name='registro_empresa'),
    # Registrar una nueva sucursal para una empresa
    path('registro-sucursal/<str:rut_empresa>/', views.registro_sucursal, name='registro_sucursal'),    
    path('logout-confirmation/', views.logout_confirmation, name='logout_confirmation'),
    path('logout/', views.logout_view, name='logout'),  # Mantén la ruta existente
    path('infostoric-export-excel/', views.infostoric_export_excel, name='infostoric_export_excel'),
    path('export-filtered-excel/', views.export_filtered_excel, name='export_filtered_excel'), 
    #error de pagina no encontrada error_404
    
    

   
    
    

]
