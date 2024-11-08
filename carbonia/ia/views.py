# Description: Vistas de Django para la aplicación de IA.
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password, check_password
from django.utils.html import *
# Importar las bibliotecas necesarias
from google.cloud import storage, bigquery
import openai
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
# Importar las bibliotecas necesarias
import os
import re
import json
from datetime import datetime

# Vista para subir un archivo y procesarlo
def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        # Obtener el archivo subido
        uploaded_file = request.FILES['pdf_file']
        
        # Obtener el RUT del cliente desde la sesión o contexto
        perfil_id = request.session.get('rut', 'No Disponible')  # Usa 'No Disponible' como valor predeterminado si no hay RUT

        # Subir el archivo a Google Cloud Storage con el RUT como perfil_id
        uploaded_file_url = upload_to_gcs(uploaded_file, perfil_id)
        
        # Pasar la URL del archivo al contexto para mostrarlo en la plantilla
        context = {'file_url': uploaded_file_url}
        return render(request, 'result.html', context)

    return render(request, 'index.html')

# Función para subir el archivo a Google Cloud Storage
def upload_to_gcs(file, perfil_id):
    """Sube el archivo a Google Cloud Storage y retorna la URL pública"""
    storage_client = storage.Client()
    bucket_name = settings.GS_BUCKET_NAME  # El nombre del bucket debe estar en settings.py
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file.name)

    # Verifica si el archivo es un PDF y ajusta el tipo MIME
    mime_type = 'application/pdf' if file.name.endswith('.pdf') else 'application/octet-stream'

    # Sube el archivo especificando el tipo MIME
    blob.upload_from_file(file, content_type=mime_type)

    # Agrega metadatos al archivo, incluyendo el perfil_id como RUT
    blob.metadata = {'perfil_id': perfil_id}  # Aquí, perfil_id ahora está definido correctamente
    blob.patch()  # Guarda los metadatos

    # Retorna la URL pública del archivo
    return f"https://storage.googleapis.com/{bucket_name}/{file.name}"


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

# Vista para obtener los datos de BigQuery y mostrarlos en el dashboard
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
# Vista para obtener recomendaciones basadas en los datos del gráfico

def get_recommendation(request):
    graph_type = request.GET.get('type')
    labels = request.GET.getlist('labels[]')
    data = [float(value) for value in request.GET.getlist('data[]')]

    # Configurar el prompt dinámico basado en el gráfico seleccionado
    prompts = {
        'consumo': f"A partir de los siguientes datos de consumo mensual, etiquetas: {labels} y datos de consumo: {data}, ¿qué estrategias específicas podrías recomendar para reducir el consumo de energía y mejorar la huella de carbono? Por favor, incluye de 1 o 2 medidas prácticas y efectivas, solo las más relevantes.",
        'TCO2': f"Dado el conjunto de datos de emisiones mensuales en TCO2, etiquetas: {labels} y datos de emisiones: {data}, ¿cuáles son 3 recomendaciones más efectivas para reducir las emisiones de carbono? Por favor, proporciona sugerencias orientadas a resultados medibles."
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

        # Escapar el texto para evitar problemas de seguridad
        recommendation_text = escape(recommendation_text)

        # Convertir **texto** a <strong>texto</strong> solo en las partes entre ** y no en todo el texto
        recommendation_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', recommendation_text)

        # Agregar saltos de línea después de cada sugerencia específica
        recommendation_text = recommendation_text.replace(" - ", "<br>- ")

        # Crear una lista HTML para las recomendaciones con espacio entre elementos
        recommendation_text = recommendation_text.replace("1.", "<li style='margin-bottom: 15px;'>").replace("2.", "</li><li style='margin-bottom: 15px;'>") + "</li>"
        recommendation_text = f"<ol style='text-align: justify;'>{recommendation_text}</ol>"

    except Exception as e:
        return JsonResponse({'recommendation': f"Error al obtener la recomendación: {str(e)}"}, status=500)

    return JsonResponse({'recommendation': recommendation_text})



def alcance1(request):
    return render(request, 'alcance1.html')

def alcance2(request):
    return render(request, 'alcance2.html')

def alcance3(request):  
    return render(request, 'alcance3.html')

# Vista para obtener los datos de BigQuery y mostrarlos en el dashboard

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

# Vista para mostrar la página de login
def login(request):
    return render(request, 'login.html')


# Vista para mostrar la página de registro
def registro(request):
    if request.method == 'POST':
        rut = request.POST['rut']
        username = request.POST['nomcliente']
        direccion = request.POST['dircliente']
        encargado = request.POST['encargado']
        email = request.POST['emailcliente']
        password = request.POST['psscliente']
        confirm_password = request.POST['psscliente2']

        # Verificar si las contraseñas coinciden
        if password != confirm_password:
            error_message = "Las contraseñas no coinciden."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message})
            else:
                return render(request, 'registro.html', {'error_message': error_message})

        # Hashear la contraseña
        hashed_password = make_password(password)

        # Formatea la fecha actual
        fecha_registro = datetime.date.today().isoformat()

        # Configura el cliente de BigQuery
        client = bigquery.Client()

        # Define tu dataset y tabla proyectocarbonia.datacarbonia.cliente
        dataset_id = 'datacarbonia'
        table_id = 'cliente'
        table_ref = client.dataset(dataset_id).table(table_id)

        # Verificar si el RUT ya está registrado
        query = f"""
            SELECT COUNT(1) as count
            FROM `{dataset_id}.{table_id}`
            WHERE id_cliente = @rut
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("rut", "STRING", rut)
            ]
        )
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        count = next(results).count

        if count > 0:
            error_message = "El RUT ya está registrado."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message})
            else:
                return render(request, 'registro.html', {'error_message': error_message})

        # Crea la fila para insertar
        rows_to_insert = [
            {
                "id_cliente": rut,  # RUT como id_cliente
                "nomcliente": username,
                "dircliente": direccion,
                "encargado": encargado,
                "emailcliente": email,
                "psscliente": hashed_password,  # Almacena la contraseña hasheada
                "fecha_registro": fecha_registro
            }
        ]

        # Inserta la fila en la tabla de BigQuery
        errors = client.insert_rows_json(table_ref, rows_to_insert)

        if not errors:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Datos registrados exitosamente.'})
            else:
                return redirect('success')
        else:
            error_message = f"Error al registrar los datos: {errors}. Por favor, intente nuevamente."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message})
            else:
                return render(request, 'registro.html', {'error_message': error_message})

    return render(request, 'registro.html')

# Vista para mostrar la página de éxito
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Configura el cliente de BigQuery
        client = bigquery.Client()
        
        # Define tu dataset y tabla
        dataset_id = 'datacarbonia'
        table_id = 'cliente'
        
        # Realiza la consulta a BigQuery para buscar el usuario por correo
        query = f"""
            SELECT psscliente FROM `{dataset_id}.{table_id}`
            WHERE emailcliente = @correo
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("correo", "STRING", email)
            ]
        )
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()

        # Verificar si el usuario existe y si la contraseña coincide
        user = None
        for row in results:
            if check_password(password, row.psscliente):
                user = True
                break
        
        if user:
            # Guardar el email en la sesión
            request.session['email'] = email  # Almacena el email en la sesión
            
            # Redirige a la página principal si el login es exitoso
            return redirect('index')
        else:
            error_message = "Correo o contraseña incorrectos."
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')
