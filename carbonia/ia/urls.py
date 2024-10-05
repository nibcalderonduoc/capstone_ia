from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('generate_plan/', views.generate_plan, name='generate_plan'), # Generar plan, corresponde l nombre de la función en views.py
    path('', views.index, name='index'),  # Página principal
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

