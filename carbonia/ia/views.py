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
from datetime import date
from google.cloud import bigquery
# Vista para subir un archivo y procesarlo

from django.shortcuts import render
from django.conf import settings
from google.cloud import storage
from datetime import timedelta
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required

#@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def upload_to_gcs_and_generate_signed_url(file, perfil_id, alcance, bucket_name):
    """Sube un archivo a Google Cloud Storage y retorna la URL pública."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Agrega el alcance al nombre del archivo para rastrearlo fácilmente en el storage
    alcance_prefix = f"alcance_{alcance}_"
    blob = bucket.blob(alcance_prefix + file.name)

    # Verifica si el archivo es un PDF y ajusta el tipo MIME
    mime_type = 'application/pdf' if file.name.endswith('.pdf') else 'application/octet-stream'

    # Sube el archivo especificando el tipo MIME
    blob.upload_from_file(file, content_type=mime_type)

    # Generar la URL pública directa
    public_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"

    # Agrega metadatos al archivo, incluyendo el perfil_id como RUT, alcance, y la URL pública
    blob.metadata = {
        'perfil_id': perfil_id, 
        'alcance': alcance,
        'public_url': public_url  # Almacenar la URL pública como metadato
    }
    blob.patch()  # Guarda los metadatos

    return public_url



def get_bucket_name(alcance):
    # Mapea el alcance a su bucket correspondiente
    if alcance == '1':
        return settings.GS_BUCKET_NAME_ALCANCE1
    elif alcance == '2':
        return settings.GS_BUCKET_NAME_ALCANCE2    
    return settings.GS_BUCKET_NAME_ALCANCE1  # Bucket predeterminado si no se especifica un alcance

@login_required
def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        uploaded_file = request.FILES['pdf_file']
        perfil_id = request.session.get('rut', 'No Disponible')  # Default value if RUT is not in session
        alcance = request.POST.get('alcance', 'default')

        bucket_name = get_bucket_name(alcance)
        public_file_url = upload_to_gcs_and_generate_signed_url(uploaded_file, perfil_id, alcance, bucket_name)
        
        request.session['file_url'] = public_file_url  # Guarda la URL pública en la sesión
        return redirect('result')  # Redirecciona a la vista de resultado
    
    return render(request, 'index.html')  # Retorna el formulario de subida si no es POST



# Vista para mostrar previsualización de informe
from google.cloud import bigquery
@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def result(request):
    client = bigquery.Client()
    query = """
    SELECT
    num_cli AS numero_cliente,
    Numero_Boleta AS numero_boleta,
    (SELECT nombre_comuna FROM `proyectocarbonia-443321.datacarbonia.comuna` WHERE id_comuna = hc.id_comuna) AS comuna,
    consumo,
    unidad,
    (SELECT nombre FROM `proyectocarbonia-443321.datacarbonia.elemento` WHERE id_elemento = hc.id_elemento) AS elemento,
    fecha_registro AS updated
FROM
    `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
ORDER BY
    updated DESC
LIMIT 1;
    """
    query_job = client.query(query)
    results = query_job.result()
    extracted_info = [dict(row.items()) for row in results]

    file_url = request.session.get('file_url', None)  # Suponiendo que el archivo subido se almacena en la sesión

    context = {
        'file_url': file_url,
        'extracted_info': extracted_info
    }
    return render(request, 'result.html', context)






# Vista para mostrar empresas-registradas
#def empresas_registradas(request):  
    return render(request, 'empresas-registradas.html')

# Vista para mostrar Header
@login_required
def base(request):
    return render(request, 'base.html')

# Vista para mostrar sidebar
@login_required
def sidebar(request):
    return render(request, 'sidebar.html')

# Vista para mostrar content
@login_required
def content(request):
    return render(request, 'content.html')

# Vista para mostrar recomendaciones
@login_required
def recomendaciones(request):
    return render(request, 'recomendaciones.html')

# Vista para mostrar carga-item-alcance3
@login_required
def carga_item_alcance3(request):
    return render(request, 'carga-item-alcance3.html')

# Vista para mostrar base-admin
@login_required
def base_admin(request):
    return render(request, 'base-admin.html')

# Vista para mostrar dashboard-admin
@login_required
def dashboard_admin(request):
    return render(request, 'dashboard-admin.html')

# Vista para mostrar registro-admin 
@login_required
def registro_admin(request):
    return render(request, 'registro-admin.html')

# Vista para mostrar login-admin
@login_required
def login_admin(request):
    return render(request, 'login-admin.html')

# Vista para mostrar sidebar-admin
@login_required
def sidebar_admin(request):
    return render(request, 'sidebar-admin.html')

# Vista para mostrar infostoric
from django.shortcuts import render
from google.cloud import bigquery

@login_required
def infostoric(request):
    """Muestra los datos históricos de la tabla huella_carbono con filtro por alcance."""
    client = bigquery.Client()

    # Obtener el parámetro de filtro por alcance
    alcance = request.GET.get('alcance', '')

    # Consulta base
    query = """
    SELECT * 
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
    """
    
    # Modificar consulta si se aplica el filtro
    if alcance:
        query += f" WHERE Alcance = '{alcance}'"

    query += " ORDER BY fecha_registro DESC"

    # Ejecutar consulta
    query_job = client.query(query)
    results = query_job.result()

    # Convertir los resultados en una lista de diccionarios
    data = [dict(row) for row in results]

    # Pasar los datos al template
    context = {
        'data': data,
        'alcance': alcance,  # Mantener el alcance seleccionado en el formulario
    }

    return render(request, 'infostoric.html', context)

# Vista para obtener los datos de BigQuery y mostrarlos en el dashboard
from google.cloud import bigquery
from django.shortcuts import render
from google.cloud import bigquery
from django.shortcuts import render
from django.views.decorators.cache import cache_control


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def dashboard(request):
    if 'email' not in request.session:
        return redirect('login')  # Redirigir al inicio de sesión si no está autenticado

    client = bigquery.Client()
    
    try:
        # Consulta para obtener la suma total de TCO2 Calculado (Alcance 1)
        tco2_total_query = """
        SELECT
            ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado
        FROM
            `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '1'
        """
        tco2_total_result = client.query(tco2_total_query).result()
        total_tco2_calculado = next(tco2_total_result).total_tco2_calculado

        # Consulta para obtener la suma total de TCO2 Calculado (Alcance 2)
        tco2_total_query2 = """
        SELECT
            ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado2
        FROM
            `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '2'
        """
        tco2_total_result2 = client.query(tco2_total_query2).result()
        total_tco2_calculado2 = next(tco2_total_result2).total_tco2_calculado2

        # Consulta para obtener la suma total de TCO2 Calculado (Alcance 3)
        tco2_total_query3 = """
        SELECT
            ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado3
        FROM
            `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '3'
        """
        tco2_total_result3 = client.query(tco2_total_query3).result()
        total_tco2_calculado3 = next(tco2_total_result3).total_tco2_calculado3

        # Consulta para obtener datos de TCO2 Calculado por mes para cada alcance
        alcance1_query = """
        SELECT 
          EXTRACT(YEAR FROM Fecha_Inicio) AS year,
          EXTRACT(MONTH FROM Fecha_Termino) AS month,
          ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado
        FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '1'
        GROUP BY year, month
        ORDER BY year, month
        """
        alcance1_results = client.query(alcance1_query).result()

        alcance2_query = """
        SELECT 
          EXTRACT(YEAR FROM Fecha_Inicio) AS year,
          EXTRACT(MONTH FROM Fecha_Termino) AS month,
          ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado2
        FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '2'
        GROUP BY year, month
        ORDER BY year, month
        """
        alcance2_results = client.query(alcance2_query).result()

        alcance3_query = """
        SELECT 
          EXTRACT(YEAR FROM Fecha_Inicio) AS year,
          EXTRACT(MONTH FROM Fecha_Termino) AS month,
          ROUND(SUM(TCO2_Calculado), 4) AS total_tco2_calculado3
        FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
        WHERE Alcance = '3'
        GROUP BY year, month
        ORDER BY year, month
        """
        alcance3_results = client.query(alcance3_query).result()

        # Preparar datos para los gráficos
        alcance1_labels = []
        alcance1_data = []
        for row in alcance1_results:
            year = int(row.year) if row.year is not None else 0
            month = int(row.month) if row.month is not None else 0
            alcance1_labels.append(f"{year}-{month:02d}")
            alcance1_data.append(row.total_tco2_calculado)

        alcance2_labels = []
        alcance2_data = []
        for row in alcance2_results:
            year = int(row.year) if row.year is not None else 0
            month = int(row.month) if row.month is not None else 0
            alcance2_labels.append(f"{year}-{month:02d}")
            alcance2_data.append(row.total_tco2_calculado2)

        alcance3_labels = []
        alcance3_data = []
        for row in alcance3_results:
            year = int(row.year) if row.year is not None else 0
            month = int(row.month) if row.month is not None else 0
            alcance3_labels.append(f"{year}-{month:02d}")
            alcance3_data.append(row.total_tco2_calculado3)

        # Contexto con todos los datos
        context = {
            'total_tco2_calculado': total_tco2_calculado,
            'total_tco2_calculado2': total_tco2_calculado2,
            'total_tco2_calculado3': total_tco2_calculado3,
            'alcance1_labels': alcance1_labels,
            'alcance1_data': alcance1_data,
            'alcance2_labels': alcance2_labels,
            'alcance2_data': alcance2_data,
            'alcance3_labels': alcance3_labels,
            'alcance3_data': alcance3_data,
        }

    except Exception as e:
        print(f"Error ejecutando las consultas: {e}")
        context = {
            'total_tco2_calculado': 0,
            'total_tco2_calculado2': 0,
            'total_tco2_calculado3': 0,
            'alcance1_labels': [],
            'alcance1_data': [],
            'alcance2_labels': [],
            'alcance2_data': [],
            'alcance3_labels': [],
            'alcance3_data': [],
        }

    # Renderizar la página con el contexto
    return render(request, 'dashboard.html', context)



## ver graficos en combobox y recomendaciones
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def recomendaciones(request):
    client = bigquery.Client()

    # Consultas para los gráficos de consumo y TCO2 mensual
    query = """
    SELECT 
      EXTRACT(YEAR FROM fec_ter) AS year,
      EXTRACT(MONTH FROM fec_ter) AS month,
      SUM(consumo) AS total_consumo,
      SUM(TCO2) AS total_TCO2
    FROM `proyectocarbonia-443321.alcance2.silver_parse_table`
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
    FROM `proyectocarbonia-443321.alcance2.silver_parse_table`
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



from google.cloud import bigquery
from django.shortcuts import render
from django.http import JsonResponse

#def alcance1(request):
 #    return render(request, 'alcance1.html')

@login_required
def alcance2(request):
    return render(request, 'alcance2.html')

#def alcance3(request):  
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
    FROM `proyectocarbonia-443321.datacarbonia.categoria` c
    JOIN `proyectocarbonia-443321.datacarbonia.subcategoria` s 
    ON c.id_categoria = s.id_categoria
    JOIN `proyectocarbonia-443321.datacarbonia.elemento` e 
    ON s.id_subcategoria = e.id_subcategoria
    JOIN `proyectocarbonia-443321.datacarbonia.unidad_medida` u 
    ON e.id_elemento = u.id_elemento
    JOIN `proyectocarbonia-443321.datacarbonia.alcance` a
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

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from google.cloud import bigquery
import json
from datetime import datetime
import time

@csrf_protect
@require_POST
def upload_to_bigquery(request):
    try:
        # Depuración para ver el contenido del cuerpo de la solicitud
        print("Contenido de la solicitud:", request.body)
        
        # Intentar cargar los datos JSON
        data = json.loads(request.body)
        print("Datos JSON recibidos:", data)

        # Validación de datos
        for item in data:
            required_fields = ['categoria', 'subcategoria', 'elemento', 'valor', 'unidad', 'fechaRegistro']
            for field in required_fields:
                if field not in item or not item[field]:
                    return JsonResponse({'message': f'El campo {field} es requerido.'}, status=400)

        # Obtener datos del perfil desde la sesión
        rut = request.session.get('rut', 'No Disponible')
        nombre_cliente = request.session.get('profile_name', 'No Disponible')
        encargado = request.session.get('encargado', 'No Disponible')
        
        # Imprimir datos de sesión para depuración
        print("Datos de la sesión - RUT:", rut)
        print("Datos de la sesión - Nombre del cliente:", nombre_cliente)
        print("Datos de la sesión - Encargado:", encargado)

        # Verificación adicional de los datos esenciales del perfil
        if rut == 'No Disponible' or nombre_cliente == 'No Disponible':
            return JsonResponse({'message': 'Los datos del perfil del cliente no están completos.'}, status=400)

        # Asegurarse de que id_cliente (rut) sea enviado como STRING
        id_cliente = str(rut)

        client = bigquery.Client()
        table_id = 'proyectocarbonia-443321.alcance3.alcance3_data'

        # Preparar filas para insertar
        rows_to_insert = []
        for item in data:
            # Generar un ID único basado en el tiempo en milisegundos
            unique_id = int(time.time() * 1000)

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

            # Crear el diccionario de la fila a insertar
            row = {
                "id": unique_id,                  # ID único para cada registro, basado en tiempo en milisegundos
                "id_cliente": id_cliente,         # RUT como id_cliente en STRING
                "nombre_cliente": nombre_cliente, # Nombre del cliente desde el perfil
                "rut": rut,                       # RUT completo con guion
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

        # Insertar filas en BigQuery
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
        fecha_registro = date.today().isoformat()

        # Configura el cliente de BigQuery
        client = bigquery.Client()

        # Define tu dataset y tabla proyectocarbonia-443321.datacarbonia.cliente
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
from django.shortcuts import render, redirect
from django.http import JsonResponse
from google.cloud import bigquery
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from django.contrib.sessions.models import Session
from django.conf import settings
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Configura el cliente de BigQuery
        client = bigquery.Client()

        # Define tu dataset y tabla
        dataset_id = 'datacarbonia'
        table_id = 'cliente'

        try:
            # Realiza la consulta a BigQuery para buscar el usuario por correo
            query = f"""
                SELECT id_cliente, nomcliente, emailcliente, psscliente 
                FROM `{dataset_id}.{table_id}`
                WHERE emailcliente = @correo
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("correo", "STRING", email)]
            )
            query_job = client.query(query, job_config=job_config)
            results = query_job.result()

            # Verificar si el usuario existe y si la contraseña coincide
            user_data = None
            for row in results:
                user_data = row
                if check_password(password, row.psscliente):  # Validar contraseña encriptada
                    # Guarda los datos del usuario en la sesión
                    request.session['id_cliente'] = row.id_cliente
                    request.session['email'] = row.emailcliente
                    request.session['nombre_cliente'] = row.nomcliente

                    # Simula el inicio de sesión con Django
                    user, created = User.objects.get_or_create(username=row.emailcliente)
                    if created:
                        user.set_password(password)  # Establece una contraseña temporal
                        user.save()
                    login(request, user)

                    # Redirige al dashboard si el login es exitoso
                    return redirect('dashboard')
                else:
                    messages.error(request, "Correo o contraseña incorrectos.")
                    return render(request, 'login.html')

            if not user_data:
                messages.error(request, "Usuario no encontrado.")
                return render(request, 'login.html')

        except Exception as e:
            print(f"Error al autenticar: {e}")
            messages.error(request, "Ocurrió un error durante el inicio de sesión.")
            return render(request, 'login.html')

    return render(request, 'login.html')



from django.http import JsonResponse
from ia.context_processors import perfil_cliente

def initialize_profile(request):
    # Ejecuta el context processor y guarda los datos en la sesión
    perfil_data = perfil_cliente(request)

    # Comprobar si los datos se inicializaron correctamente
    if perfil_data.get('rut') and perfil_data.get('profile_name'):
        return JsonResponse({'message': 'Datos de perfil inicializados correctamente en la sesión.'})
    else:
        return JsonResponse({'message': 'No se pudieron inicializar los datos del perfil.'}, status=400)

from django.shortcuts import render
from google.cloud import bigquery
import json
from google.cloud import bigquery

@login_required
def alcance3(request):
    # Inicializa el cliente de BigQuery
    client = bigquery.Client()

    # Define la consulta modificada para usar "anio" en lugar de "año"
    query = """
    SELECT 
        categoria,
        subcategoria,
        elemento,
        SUM(valor) AS total_valor,
        EXTRACT(MONTH FROM fecha_registro) AS mes,
        EXTRACT(YEAR FROM fecha_registro) AS anio
    FROM `proyectocarbonia-443321.alcance3.alcance3_data`
    GROUP BY categoria, subcategoria, elemento, mes, anio
    ORDER BY anio, mes
    """
    
    # Ejecuta la consulta
    query_job = client.query(query)
    results = query_job.result()

    # Prepara los datos para los gráficos
    categorias_data = {}
    evolucion_data = {}
    for row in results:
        categoria = row.categoria
        subcategoria = row.subcategoria
        elemento = row.elemento
        total_valor = row.total_valor
        mes = row.mes
        anio = row.anio

        # Agrupar datos para el gráfico de torta
        if categoria not in categorias_data:
            categorias_data[categoria] = {}
        if subcategoria not in categorias_data[categoria]:
            categorias_data[categoria][subcategoria] = {}
        
        categorias_data[categoria][subcategoria][elemento] = total_valor

        # Agrupar datos para el gráfico de líneas (evolución en el tiempo)
        if categoria not in evolucion_data:
            evolucion_data[categoria] = {}
        if subcategoria not in evolucion_data[categoria]:
            evolucion_data[categoria][subcategoria] = {}
        if anio not in evolucion_data[categoria][subcategoria]:
            evolucion_data[categoria][subcategoria][anio] = {}
        evolucion_data[categoria][subcategoria][anio][mes] = total_valor

    # Convertir datos a JSON para la plantilla
    context = {
        "categorias_data": json.dumps(categorias_data),
        "evolucion_data": json.dumps(evolucion_data)
    }

    return render(request, 'alcance3.html', context)
    


from django.http import JsonResponse
from google.cloud import bigquery

def get_regions(request):
    """Obtiene todas las regiones desde BigQuery."""
    client = bigquery.Client()
    query = """
    SELECT DISTINCT id_region, nombre_region
    FROM `proyectocarbonia-443321.datacarbonia.region`
    ORDER BY nombre_region
    """
    query_job = client.query(query)
    results = query_job.result()

    regions = [{'id': row.id_region, 'name': row.nombre_region} for row in results]
    return JsonResponse({'regions': regions})


def get_provinces(request):
    """Obtiene las provincias según la región seleccionada."""
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse({'error': 'region_id es requerido'}, status=400)

    client = bigquery.Client()
    query = f"""
    SELECT DISTINCT id_provincia, nombre_provincia
    FROM `proyectocarbonia-443321.datacarbonia.provincia`
    WHERE id_region = {region_id}
    ORDER BY nombre_provincia
    """
    query_job = client.query(query)
    results = query_job.result()

    provinces = [{'id': row.id_provincia, 'name': row.nombre_provincia} for row in results]
    return JsonResponse({'provinces': provinces})


def get_communes(request):
    """Obtiene las comunas según la provincia seleccionada."""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse({'error': 'province_id es requerido'}, status=400)

    client = bigquery.Client()
    query = f"""
    SELECT DISTINCT id_comuna, nombre_comuna
    FROM `proyectocarbonia-443321.datacarbonia.comuna`
    WHERE id_provincia = {province_id}
    ORDER BY nombre_comuna
    """
    query_job = client.query(query)
    results = query_job.result()

    communes = [{'id': row.id_comuna, 'name': row.nombre_comuna} for row in results]
    return JsonResponse({'communes': communes})


def get_statistics(request):
    """Obtiene estadísticas y lista todas las direcciones únicas con TCO2 calculado para la comuna seleccionada."""
    commune_id = request.GET.get('commune_id')
    if not commune_id:
        return JsonResponse({'error': 'commune_id es requerido'}, status=400)

    client = bigquery.Client()
    # Suponiendo que puedas obtener el nombre de la comuna en una consulta separada o mediante un JOIN
    query = f"""
    SELECT 
        c.nombre_comuna,
        d.Direccion_Cliente,
        SUM(d.TCO2_Calculado) AS total_tco2
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` d
    JOIN `proyectocarbonia-443321.datacarbonia.comuna` c ON d.id_comuna = c.id_comuna
    WHERE d.id_comuna = {commune_id}
    GROUP BY c.nombre_comuna, d.Direccion_Cliente
    """
    query_job = client.query(query)
    results = query_job.result()

    direcciones = []
    nombre_comuna = ""
    for row in results:
        if not nombre_comuna:  # Asignar el nombre de la comuna desde la primera fila
            nombre_comuna = row.nombre_comuna
        direcciones.append({
            'direccion': row.Direccion_Cliente,
            'tco2_calculado': row.total_tco2
        })

    data = {
        'commune_name': nombre_comuna,  # Usar el nombre de la comuna en lugar del ID
        'direcciones': direcciones
    }

    return JsonResponse(data)




from django.shortcuts import render, redirect
from django.http import JsonResponse
from google.cloud import bigquery
import uuid
import json

# Listar empresas registradas
@login_required
def empresas_registradas(request):
    """Lista todas las empresas y cuenta sus sucursales."""
    client = bigquery.Client()

    # Query para obtener empresas y contar sucursales
    query = """
    SELECT 
        e.rut, 
        e.nombre_cliente, 
        e.email_cliente, 
        e.direccion, 
        r.nombre_region AS region, 
        COUNT(s.id_sucursal) AS sucursal_count
    FROM `proyectocarbonia-443321.datacarbonia.empresa` e
    LEFT JOIN `proyectocarbonia-443321.datacarbonia.sucursal` s ON e.rut = s.rut_empresa
    LEFT JOIN `proyectocarbonia-443321.datacarbonia.region` r ON e.id_region = r.id_region
    GROUP BY e.rut, e.nombre_cliente, e.email_cliente, e.direccion, region
    ORDER BY e.nombre_cliente
    """
    query_job = client.query(query)
    empresas = query_job.result()

    # Preparar datos para el template
    empresas_data = [
        {
            "rut": row.rut,
            "nombre_cliente": row.nombre_cliente,
            "email_cliente": row.email_cliente,
            "direccion": row.direccion,
            "region": row.region,
            "sucursal_count": row.sucursal_count,
        }
        for row in empresas
    ]

    return render(request, 'empresas-registradas.html', {'empresas': empresas_data})


# Ver sucursales de una empresa específica
@login_required
def sucursales_registradas(request, rut_empresa):
    """Muestra las sucursales de una empresa específica."""
    client = bigquery.Client()

    # Query para obtener sucursales de la empresa
    query = f"""
    SELECT 
        s.nombre_sucursal, 
        s.direccion_sucursal, 
        r.nombre_region AS region, 
        p.nombre_provincia AS provincia, 
        c.nombre_comuna AS comuna
    FROM `proyectocarbonia-443321.datacarbonia.sucursal` s
    LEFT JOIN `proyectocarbonia-443321.datacarbonia.region` r ON s.id_region = r.id_region
    LEFT JOIN `proyectocarbonia-443321.datacarbonia.provincia` p ON s.id_provincia = p.id_provincia
    LEFT JOIN `proyectocarbonia-443321.datacarbonia.comuna` c ON s.id_comuna = c.id_comuna
    WHERE s.rut_empresa = '{rut_empresa}'
    ORDER BY s.nombre_sucursal
    """
    query_job = client.query(query)
    sucursales = query_job.result()

    sucursales_data = [
        {
            "nombre_sucursal": row.nombre_sucursal,
            "direccion_sucursal": row.direccion_sucursal,
            "region": row.region,
            "provincia": row.provincia,
            "comuna": row.comuna,
        }
        for row in sucursales
    ]

    # Obtener información de la empresa
    empresa_query = f"""
    SELECT nombre_cliente
    FROM `proyectocarbonia-443321.datacarbonia.empresa`
    WHERE rut = '{rut_empresa}'
    """
    empresa_job = client.query(empresa_query)
    empresa = empresa_job.result().to_dataframe().iloc[0]

    return render(request, 'sucursales-registradas.html', {'sucursales': sucursales_data, 'empresa': empresa})


# Registrar una nueva empresa
@login_required
def registro_empresa(request):
    """Registra una empresa nueva."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rut = data.get('rut')
            nombre_cliente = data.get('nomcliente')
            direccion = data.get('dircliente')
            id_region = data.get('region')
            id_provincia = data.get('provincia')
            id_comuna = data.get('comuna')
            email_cliente = data.get('emailcliente')

            if not all([rut, nombre_cliente, direccion, id_region, id_provincia, id_comuna, email_cliente]):
                return JsonResponse({'error': 'Todos los campos son obligatorios.'}, status=400)

            client = bigquery.Client()

            # Insertar empresa
            empresa_table = 'proyectocarbonia-443321.datacarbonia.empresa'
            empresa_row = {
                'rut': rut,
                'nombre_cliente': nombre_cliente,
                'direccion': direccion,
                'id_region': int(id_region),
                'id_provincia': int(id_provincia),
                'id_comuna': int(id_comuna),
                'email_cliente': email_cliente,
            }
            errors = client.insert_rows_json(empresa_table, [empresa_row])

            if errors:
                return JsonResponse({'error': f'Error al registrar la empresa: {errors}'}, status=500)

            return JsonResponse({'message': 'Empresa registrada exitosamente.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

    return render(request, 'registro-empresa.html')


# Registrar una sucursal para una empresa
@login_required
def registro_sucursal(request, rut_empresa):
    """Registra una nueva sucursal para una empresa existente."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_sucursal = data.get('nomsucursal')
            direccion_sucursal = data.get('dirsucursal')
            id_region = data.get('regionsucursal')
            id_provincia = data.get('provinciasucursal')
            id_comuna = data.get('comunasucursal')

            if not all([nombre_sucursal, direccion_sucursal, id_region, id_provincia, id_comuna]):
                return JsonResponse({'error': 'Todos los campos de la sucursal son obligatorios.'}, status=400)

            client = bigquery.Client()

            # Insertar sucursal
            sucursal_table = 'proyectocarbonia-443321.datacarbonia.sucursal'
            sucursal_row = {
                'id_sucursal': str(uuid.uuid4()),  # ID único para la sucursal
                'rut_empresa': rut_empresa,
                'nombre_sucursal': nombre_sucursal,
                'direccion_sucursal': direccion_sucursal,
                'id_region': int(id_region),
                'id_provincia': int(id_provincia),
                'id_comuna': int(id_comuna),
            }
            errors = client.insert_rows_json(sucursal_table, [sucursal_row])

            if errors:
                return JsonResponse({'error': f'Error al registrar la sucursal: {errors}'}, status=500)

            return JsonResponse({'message': 'Sucursal registrada exitosamente.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

    return render(request, 'registrar-sucursal.html', {'rut_empresa': rut_empresa})

from django.http import JsonResponse
from google.cloud import bigquery

def get_locations_with_data(request):
    """Devuelve regiones, provincias y comunas con datos disponibles."""
    client = bigquery.Client()

    try:
        # Consulta para obtener las ubicaciones con datos
        query = """
        SELECT
            r.nombre_region AS region,
            p.nombre_provincia AS provincia,
            c.nombre_comuna AS comuna,
            d.Direccion_Cliente AS direccion
        FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` h
        JOIN `proyectocarbonia-443321.datacarbonia.region` r ON h.id_region = r.id_region
        JOIN `proyectocarbonia-443321.datacarbonia.provincia` p ON h.id_provincia = p.id_provincia
        JOIN `proyectocarbonia-443321.datacarbonia.comuna` c ON h.id_comuna = c.id_comuna
        LEFT JOIN `proyectocarbonia-443321.datacarbonia.direcciones` d ON h.id_comuna = d.id_comuna
        GROUP BY region, provincia, comuna, direccion
        """
        query_job = client.query(query)
        results = query_job.result()

        # Organizar los resultados en un formato estructurado
        data = {}
        for row in results:
            region = row.region
            provincia = row.provincia
            comuna = row.comuna
            direccion = row.direccion

            if region not in data:
                data[region] = {}
            if provincia not in data[region]:
                data[region][provincia] = {}
            if comuna not in data[region][provincia]:
                data[region][provincia][comuna] = []

            if direccion:
                data[region][provincia][comuna].append(direccion)

        return JsonResponse({'locations': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from django.shortcuts import render
from google.cloud import bigquery

@login_required
def alcance1(request):
    client = bigquery.Client()
    data = []
    consolidated_data = []
    direcciones_unicas = []
    years_unicos = []
    months_unicos = []

    # Obtener los valores de los filtros desde la solicitud GET
    direccion_filtro = request.GET.get('direccion', 'Todos')
    year_filtro = request.GET.get('year', 'Todos')
    month_filtro = request.GET.get('month', 'Todos')

    # Consulta para obtener direcciones únicas
    query_direcciones = """
    SELECT DISTINCT hc.Direccion_Cliente AS direccion
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY direccion;
    """

    # Consulta para obtener años únicos
    query_years = """
    SELECT DISTINCT EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY year;
    """

    # Consulta para obtener meses únicos
    query_months = """
    SELECT DISTINCT EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY month;
    """

    # Consulta principal: Datos detallados
    query1 = """
    SELECT 
        EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year,
        EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month,
        hc.Direccion_Cliente as direccion,
        c.nombre_comuna AS comuna,
        hc.consumo AS consumo,
        hc.unidad AS unidad,
        e.nombre AS elemento,
        SUM(hc.TCO2_Calculado) AS total_TCO2_mensual
    FROM
        `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
        INNER JOIN `proyectocarbonia-443321.datacarbonia.comuna` AS c ON hc.id_comuna = c.id_comuna
        INNER JOIN `proyectocarbonia-443321.datacarbonia.elemento` AS e ON hc.id_elemento = e.id_elemento
    WHERE 
        hc.Alcance = '1'
    """

    # Aplicar filtros dinámicos
    if direccion_filtro != "Todos":
        query1 += f" AND hc.Direccion_Cliente = '{direccion_filtro}'"
    if year_filtro != "Todos":
        query1 += f" AND EXTRACT(YEAR FROM hc.Fecha_Inicio) = {year_filtro}"
    if month_filtro != "Todos":
        query1 += f" AND EXTRACT(MONTH FROM hc.Fecha_Inicio) = {month_filtro}"

    query1 += """
    GROUP BY 
        year, month, hc.Direccion_Cliente, comuna, e.nombre, hc.consumo, hc.unidad
    ORDER BY 
        year, month;
    """

    # Consulta consolidada
    query2 = """
    SELECT 
        hc.Direccion_Cliente AS direccion,
        SUM(hc.TCO2_Calculado) AS total_TCO2,
        COUNT(*) AS registros
    FROM
        `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE 
        hc.Alcance = '1'
    """
    if direccion_filtro != "Todos":
        query2 += f" AND hc.Direccion_Cliente = '{direccion_filtro}'"
    if year_filtro != "Todos":
        query2 += f" AND EXTRACT(YEAR FROM hc.Fecha_Inicio) = {year_filtro}"
    if month_filtro != "Todos":
        query2 += f" AND EXTRACT(MONTH FROM hc.Fecha_Inicio) = {month_filtro}"

    query2 += """
    GROUP BY 
        direccion
    ORDER BY 
        total_TCO2 DESC;
    """

    try:
        # Ejecutar consulta de direcciones únicas
        query_job_direcciones = client.query(query_direcciones)
        for row in query_job_direcciones.result():
            direcciones_unicas.append(row.direccion)

        # Ejecutar consulta de años únicos
        query_job_years = client.query(query_years)
        for row in query_job_years.result():
            years_unicos.append(int(row.year) if row.year is not None else None)

        # Ejecutar consulta de meses únicos
        query_job_months = client.query(query_months)
        for row in query_job_months.result():
            months_unicos.append(int(row.month) if row.month is not None else None)

        # Ejecutar consulta principal
        query_job1 = client.query(query1)
        for row in query_job1.result():
            data.append({
                'year': row.year,
                'month': row.month,
                'direccion': row.direccion,
                'comuna': row.comuna,
                'consumo': row.consumo,
                'unidad': row.unidad,
                'elemento': row.elemento,
                'total_TCO2': row.total_TCO2_mensual,
            })

        # Ejecutar consulta consolidada
        query_job2 = client.query(query2)
        for row in query_job2.result():
            consolidated_data.append({
                'direccion': row.direccion,
                'total_TCO2': row.total_TCO2,
                'registros': row.registros,
            })

    except Exception as e:
        print(f"Error ejecutando las consultas: {e}")

    # Pasar datos al contexto
    context = {
        'data': data,  # Datos detallados
        'filtered_data': data,  # Datos filtrados
        'consolidated_data': consolidated_data,  # Datos consolidados
        'direccion_filtro': direccion_filtro,  # Filtro seleccionado (dirección)
        'year_filtro': year_filtro,  # Filtro seleccionado (año)
        'month_filtro': month_filtro,  # Filtro seleccionado (mes)
        'direcciones_unicas': direcciones_unicas,  # Direcciones únicas
        'years_unicos': [y for y in years_unicos if y is not None],  # Años únicos
        'months_unicos': [m for m in months_unicos if m is not None],  # Meses únicos
    }

    return render(request, 'alcance1.html', context)

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.cache import cache_control
from django.contrib.sessions.models import Session

# Otros imports necesarios
from google.cloud import bigquery, storage
import json
from datetime import date

# --- Función para verificar sesión ---
def verify_session(request):
    """Verifica si hay una sesión activa, si no, redirige al login."""
    if not request.session.get('email'):
        return redirect('login')
    
    # --- Vista para el cierre de sesión ---
def logout_view(request):
    """Cierra la sesión del usuario."""
    request.session.flush()  # Limpia la sesión actual
    return redirect('login')  # Redirige al inicio de sesión

from django.shortcuts import render
@login_required
def logout_confirmation(request):
    """Vista para confirmar el cierre de sesión."""
    return render(request, 'logout_confirmation.html')

#exportar excel
import pandas as pd
from django.http import HttpResponse
from google.cloud import bigquery

def infostoric_export_excel(request):
    """Exporta los datos filtrados de huella_carbono a un archivo Excel."""
    client = bigquery.Client()
    alcance = request.GET.get('alcance', '')  # Obtiene el filtro de alcance desde la URL
    search_query = request.GET.get('search', '')  # Obtiene el término de búsqueda desde la URL

    # Construir la consulta basada en el filtro de alcance y la búsqueda
    query = """
    SELECT * FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
    """
    conditions = []
    if alcance:
        conditions.append(f"Alcance = '{alcance}'")
    if search_query:
        conditions.append(f"""
        (
            CAST(Numero_Boleta AS STRING) LIKE '%{search_query}%' OR
            Nombre_Cliente LIKE '%{search_query}%' OR
            Direccion_Cliente LIKE '%{search_query}%' OR
            Empresa_Distribuidora LIKE '%{search_query}%'
        )
        """)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Ejecutar la consulta
    query_job = client.query(query)
    results = query_job.result()

    # Convertir los resultados de la consulta en un DataFrame
    data = [dict(row) for row in results]
    df = pd.DataFrame(data)

    # Si no hay datos, devolver un mensaje
    if df.empty:
        response = HttpResponse("No hay datos para exportar con este filtro o búsqueda.", content_type="text/plain")
        response.status_code = 404
        return response

    # Eliminar la información de zona horaria en columnas de tipo datetime
    for column in df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
        df[column] = df[column].dt.tz_localize(None)

    # Procesar la columna 'link_pdf' para agregar hipervínculos visibles en Excel
    if 'link_pdf' in df.columns:
        df['link_pdf'] = df['link_pdf'].apply(lambda x: f'=HYPERLINK("{x}", "Ver PDF")' if pd.notnull(x) else None)

    # Crear el archivo Excel en memoria
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="huella_carbono_{alcance or "todos"}_filtered.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos Filtrados')

    return response

import pandas as pd
from django.http import JsonResponse, HttpResponse
import json

def export_filtered_excel(request):
    if request.method == 'POST':
        try:
            filtered_data = json.loads(request.body).get('data', [])
            df = pd.DataFrame(filtered_data)

            # Crear archivo Excel
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="filtrado_huella_carbono.xlsx"'

            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtrado')

            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


