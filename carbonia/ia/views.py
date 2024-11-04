from django.shortcuts import render
from django.conf import settings
from google.cloud import storage  # Importa Google Cloud Storage
from django.http import HttpResponse
import os
from google.cloud import bigquery
from django.shortcuts import render
import openai
from django.http import JsonResponse
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from django.http import JsonResponse
from django.conf import settings


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

# Vista para mostrar recomendaciones
def recomendaciones(request):
    return render(request, 'recomendaciones.html')

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

    # Consulta para TCO2 mensual
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

## ver graficos en combobox y recomendaciones
def recomendaciones(request):
    client = bigquery.Client()

    # Consultas para los gráficos de consumo y TCO2 mensual
    query = """
    SELECT 
      EXTRACT(YEAR FROM fec_ter) AS year,
      EXTRACT(MONTH FROM fec_ter) AS month,
      SUM(consumo) AS total_consumo,
      SUM(TCO2) AS total_TCO2
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY year, month
    ORDER BY year, month
    """
    query_job = client.query(query)
    results = query_job.result()

    # Preparar los datos para los gráficos
    labels = []
    consumo_data = []
    tco2_data = []

    for row in results:
        labels.append(f"{int(row['year'])}-{int(row['month']):02d}")  # Formato "Año-Mes"
        consumo_data.append(row['total_consumo'])
        tco2_data.append(row['total_TCO2'])

    # Imprimir los datos para ver si son correctos
    print("Labels:", labels)
    print("Consumo Data:", consumo_data)
    print("TCO2 Data:", tco2_data)

    # Si los datos son correctos, sigamos con la consulta de distribuidoras
    distribuidora_query = """
    SELECT 
      nom_dist,
      SUM(consumo) AS total_consumo
    FROM `proyectocarbonia.alcance2.silver_parse_table`
    GROUP BY nom_dist
    ORDER BY total_consumo DESC
    """
    distribuidora_results = client.query(distribuidora_query).result()

    distribuidora_labels = []
    distribuidora_data = []
    for row in distribuidora_results:
        distribuidora_labels.append(row['nom_dist'])
        distribuidora_data.append(row['total_consumo'])

    print("Distribuidora Labels:", distribuidora_labels)
    print("Distribuidora Data:", distribuidora_data)

    # Preparar los datos para enviarlos al template
    context = {
        'labels': labels,
        'consumo_data': consumo_data,
        'tco2_data': tco2_data,
        'distribuidora_labels': distribuidora_labels,
        'distribuidora_data': distribuidora_data
    }

    return render(request, 'recomendaciones.html', context)

### revisar
from langchain_openai import ChatOpenAI  # Actualizado a la nueva versión
from langchain.prompts import ChatPromptTemplate

def get_recommendation(request):
    graph_type = request.GET.get('type')
    labels = request.GET.getlist('labels[]')
    data = [float(value) for value in request.GET.getlist('data[]')]

    # Configurar el prompt dinámico basado en el gráfico seleccionado
    prompts = {
        'consumo': f"Dado los datos de consumo mensual: Labels: {labels} y Consumo Data: {data}, ¿cuál es tu recomendación para reducir el consumo de energía y mejorar la huella de carbono?",
        'TCO2': f"Dado los datos de emisiones mensuales de TCO2: Labels: {labels} y TCO2 Data: {data}, ¿cuál es tu recomendación para reducir las emisiones de carbono?",
    }

    prompt = prompts.get(graph_type)
    if not prompt:
        return JsonResponse({'recommendation': 'Tipo de gráfico no reconocido.'})

    # Usar el modelo GPT-4o
    llm = ChatOpenAI(model="gpt-4o", openai_api_key=settings.OPENAI_API_KEY)

    try:
        # Pasar el prompt directamente como una cadena
        recommendation_response = llm.invoke(prompt)
        recommendation_text = recommendation_response.content  # Acceder directamente al contenido del mensaje
    except Exception as e:
        return JsonResponse({'recommendation': f"Error al obtener la recomendación: {str(e)}"}, status=500)

    return JsonResponse({'recommendation': recommendation_text})

def alcance1(request):
    return render(request, 'alcance1.html')

def alcance2(request):
    return render(request, 'alcance2.html')

def alcance3(request):  
    return render(request, 'alcance3.html')

from django.http import JsonResponse
from google.cloud import bigquery

def obtener_datos_bigquery(request):
    client = bigquery.Client()
    query = """
    SELECT 
    c.nombre AS categoria, 
    s.nombre AS subcategoria, 
    e.nombre AS elemento,
    u.unidad AS unidad
    FROM `proyectocarbonia.datacarbonia.categoria` c
    JOIN `proyectocarbonia.datacarbonia.subcategoria` s 
    ON c.id_categoria = s.id_categoria
    JOIN `proyectocarbonia.datacarbonia.elemento` e 
    ON s.id_subcategoria = e.id_subcategoria
    JOIN `proyectocarbonia.datacarbonia.unidad_medida` u 
    ON e.id_elemento = u.id_elemento
    JOIN `proyectocarbonia.datacarbonia.alcance` a
    ON c.id_alcance = a.id_alcance
    WHERE a.id_alcance = 3
    """
    query_job = client.query(query)
    resultados = query_job.result()

    data = {}
    for row in resultados:
        categoria = row.categoria
        subcategoria = row.subcategoria
        elemento = row.elemento
        unidad = row.unidad
        
        if categoria not in data:
            data[categoria] = {}
        if subcategoria not in data[categoria]:
            data[categoria][subcategoria] = []
        data[categoria][subcategoria].append({'elemento': elemento, 'unidad': unidad})
    
    return JsonResponse(data)

#subir datos a bigquery
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import json
from google.cloud import bigquery
from datetime import datetime

@csrf_protect
@require_POST
def upload_to_bigquery(request):
    try:
        data = json.loads(request.body)

        # Validación de datos
        for item in data:
            required_fields = ['categoria', 'subcategoria', 'elemento', 'valor', 'unidad', 'fechaRegistro']
            for field in required_fields:
                if field not in item or not item[field]:
                    return JsonResponse({'message': f'El campo {field} es requerido.'}, status=400)

        client = bigquery.Client()
        table_id = 'proyectocarbonia.alcance3.alcance3_data'

        # Preparar filas para insertar
        rows_to_insert = []
        for item in data:
            # Convertir valor a float
            try:
                valor = float(item["valor"])
            except ValueError:
                return JsonResponse({'message': f'El valor "{item["valor"]}" no es un número válido.'}, status=400)

            # Convertir fecha a formato DATE
            try:
                fecha_registro = datetime.strptime(item["fechaRegistro"], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'message': f'La fecha "{item["fechaRegistro"]}" no tiene el formato correcto YYYY-MM-DD.'}, status=400)

            row = {
                "id_cliente": 1,          # Se establece como None
                "nombre_cliente": "Nombre de prueba",      # Se establece como None
                "rut": "00000000-0" ,                 # Se establece como None
                "categoria": item["categoria"],
                "subcategoria": item["subcategoria"],
                "elemento": item["elemento"],
                "valor": valor,
                "unidad": item["unidad"],
                "fecha_registro": str(fecha_registro)
            }

            rows_to_insert.append(row)

        # Obtener la tabla para asegurar que el esquema coincide
        table = client.get_table(table_id)

        errors = client.insert_rows_json(table, rows_to_insert)

        if not errors:
            return JsonResponse({'message': 'Datos subidos exitosamente'})
        else:
            # Imprimir errores para depuración
            print('Errors:', errors)
            return JsonResponse({'message': 'Error al subir los datos', 'errors': errors}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'message': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        # Imprimir excepción para depuración
        print('Exception:', str(e))
        return JsonResponse({'message': f'Error del servidor: {str(e)}'}, status=500)
