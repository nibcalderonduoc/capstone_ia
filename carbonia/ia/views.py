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


# Vista para obtener los datos de BigQuery y mostrarlos en el 
#def dashboard(request):
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
def base(request):
    return render(request, 'base.html')

# Vista para mostrar sidebar
def sidebar(request):
    return render(request, 'sidebar.html')

# Vista para mostrar content
def content(request):
    return render(request, 'content.html')

# Vista para mostrar infostoric
def infostoric(request):
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
    return render(request, 'infostoric.html', {'data': data})

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
#def dashboard(request):
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


#def dashboard(request):
    client = bigquery.Client()

    query = """
    SELECT 
      EXTRACT(YEAR FROM fec_ter) AS year,
      EXTRACT(MONTH FROM fec_ter) AS month,
      SUM(consumo) AS total_consumo,
      SUM(CO2) AS total_CO2,
      SUM(TCO2) AS total_TCO2
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY year, month
    ORDER BY year, month
    """
    
    query_job = client.query(query)
    results = query_job.result()

    # Prepara los datos para el gráfico
    labels = []
    consumo_data = []
    CO2_data = []
    TCO2_data = []

    for row in results:
        labels.append(f"{int(row['year'])}-{int(row['month']):02d}")  # Formato "Año-Mes"
        consumo_data.append(row['total_consumo'])
        CO2_data.append(row['total_CO2'])
        TCO2_data.append(row['total_TCO2'])

    context = {
        'labels': labels,
        'consumo_data': consumo_data,
        'CO2_data': CO2_data,
        'TCO2_data': TCO2_data,
    }

    return render(request, 'dashboard.html', context)

def dashboard(request):
    client = bigquery.Client()

    # Consulta para consumo mensual
    consumo_query = """
    SELECT 
      EXTRACT(YEAR FROM fec_ter) AS year,
      EXTRACT(MONTH FROM fec_ter) AS month,
      SUM(consumo) AS total_consumo
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY year, month
    ORDER BY year, month
    """
    consumo_results = client.query(consumo_query).result()

    # Consulta para TCO2 mensual extraído de la tabla
    tco2_query = """
    SELECT 
      EXTRACT(YEAR FROM fec_ter) AS year,
      EXTRACT(MONTH FROM fec_ter) AS month,
      SUM(TCO2) AS total_TCO2
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY year, month
    ORDER BY year, month
    """
    tco2_results = client.query(tco2_query).result()

    # Consulta para consumo por distribuidora
    distribuidora_query = """
    SELECT 
      nom_dist,
      SUM(consumo) AS total_consumo
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY nom_dist
    ORDER BY total_consumo DESC
    """
    distribuidora_results = client.query(distribuidora_query).result()

    # Preparar datos para los gráficos
    labels = []
    consumo_data = []
    tco2_data = []

    for row in consumo_results:
        labels.append(f"{int(row['year'])}-{int(row['month']):02d}")
        consumo_data.append(row['total_consumo'])

    for row in tco2_results:
        tco2_data.append(row['total_TCO2'])

    distribuidora_labels = []
    distribuidora_data = []
    for row in distribuidora_results:
        distribuidora_labels.append(row['nom_dist'])
        distribuidora_data.append(row['total_consumo'])

    context = {
        'labels': labels,
        'consumo_data': consumo_data,
        'tco2_data': tco2_data,
        'distribuidora_labels': distribuidora_labels,
        'distribuidora_data': distribuidora_data
    }

    return render(request, 'dashboard.html', context)
