from django.shortcuts import render
from django.conf import settings
from google.cloud import storage  # Importa Google Cloud Storage
from django.http import HttpResponse

# Vista para subir un archivo y procesarlo
def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        # Obtener el archivo subido
        uploaded_file = request.FILES['pdf_file']
        
        # Subir el archivo a Google Cloud Storage
        uploaded_file_url = upload_to_gcs(uploaded_file)
        
        # Pasar la URL del archivo al contexto para mostrarlo en la plantilla
        context = {'file_url': uploaded_file_url}
        return render(request, 'result.html', context)

    return render(request, 'index.html')

# Función para subir el archivo a Google Cloud Storage
def upload_to_gcs(file):
    """Sube el archivo a Google Cloud Storage y retorna la URL pública"""
    storage_client = storage.Client()
    bucket_name = settings.GS_BUCKET_NAME  # El nombre del bucket debe estar en settings.py
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file.name)
    
    blob.upload_from_file(file)

    # Retorna la URL pública del archivo
    return f"https://storage.googleapis.com/{bucket_name}/{file.name}"
