from django.shortcuts import render
from django.conf import settings
from google.cloud import storage  # Importa Google Cloud Storage
from django.http import HttpResponse
import os
from google.cloud import bigquery
from django.shortcuts import render

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

    # Verifica si el archivo es un PDF y ajusta el tipo MIME
    if file.name.endswith('.pdf'):
        mime_type = 'application/pdf'
    else:
        mime_type = 'application/octet-stream'  # Para otros archivos

    # Sube el archivo especificando el tipo MIME
    blob.upload_from_file(file, content_type=mime_type)

    # Retorna la URL pública del archivo
    return f"https://storage.googleapis.com/{bucket_name}/{file.name}"


# Vista para obtener los datos de BigQuery y mostrarlos en el dashboard
def dashboard(request):
    # Inicializa el cliente de BigQuery
    client = bigquery.Client()

    # Define la consulta
    query = """
    SELECT * FROM `proyectocarbonia.alcance2.silver_parse_table`
    LIMIT 100
    """

    # Ejecuta la consulta
    query_job = client.query(query)  # Ejecuta la consulta
    results = query_job.result()  # Obtiene los resultados

    # Prepara los datos en una lista para enviar al template
    data = []
    for row in results:
        data.append(dict(row))  # Convierte cada fila en un diccionario

    # Renderiza los datos en el template dashboard.html
    return render(request, 'dashboard.html', {'data': data})

# Vista para mostrar previsualización de informe
def result(request):
    return render(request, 'result.html')

# Vista para mostrar Header
def header(request):
    return render(request, 'header.html')

# Vista para mostrar sidebar
def sidebar(request):
    return render(request, 'sidebar.html')