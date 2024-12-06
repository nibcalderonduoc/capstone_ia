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
    query = f"""
    SELECT FORMAT_TIMESTAMP('%m', hc.Fecha_Termino) as `Mes Boleta`, hc.Numero_Boleta AS `Número Boleta`, hc.num_cli AS `Número Cliente`, 
           hc.consumo as Consumo, hc.unidad as Unidad, e.nombre as `Nombre Elemento`, hc.TCO2_Calculado as `Total CO2`, hc.link_pdf AS `Link PDF`
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` hc
    JOIN `proyectocarbonia-443321.datacarbonia.elemento` e ON hc.id_elemento = e.id_elemento
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
# alcance 3 subiendo datos.
def upload_to_bigquery(request):
    try:
        print("Contenido de la solicitud:", request.body)

        data = json.loads(request.body)
        print("Datos JSON recibidos:", data)

        # Validación de datos
        for item in data:
            required_fields = ['categoria', 'subcategoria', 'elemento', 'valor', 'unidad', 'fechaRegistro']
            for field in required_fields:
                if field not in item or not item[field]:
                    return JsonResponse({'message': f'El campo {field} es requerido.'}, status=400)

        # Obtener datos del perfil desde la sesión
        id_cliente = request.session.get('rut', 'No Disponible')
        nombre_cliente = request.session.get('profile_name', 'No Disponible')

        if id_cliente == 'No Disponible' or nombre_cliente == 'No Disponible':
            return JsonResponse({'message': 'Los datos del perfil del cliente no están completos.'}, status=400)

        # Crear cliente BigQuery
        client = bigquery.Client()
        table_id = 'proyectocarbonia-443321.datacarbonia.huella_carbono'

        # Consultar datos relacionados
        categoria_table = 'proyectocarbonia-443321.datacarbonia.categoria'
        subcategoria_table = 'proyectocarbonia-443321.datacarbonia.subcategoria'
        elemento_table = 'proyectocarbonia-443321.datacarbonia.elemento'
        unidad_table = 'proyectocarbonia-443321.datacarbonia.unidad_medida'

        query_categorias = f"SELECT id_categoria, nombre FROM `{categoria_table}`"
        query_subcategorias = f"SELECT id_subcategoria, nombre FROM `{subcategoria_table}`"
        query_elementos = f"SELECT id_elemento, nombre, CO2, N2O, CH4, HFC, TCO2 FROM `{elemento_table}`"
        query_unidades = f"SELECT id_unidad_medida, id_elemento, unidad FROM `{unidad_table}`"

        categorias_data = {row['nombre']: row['id_categoria'] for row in client.query(query_categorias).result()}
        subcategorias_data = {row['nombre']: row['id_subcategoria'] for row in client.query(query_subcategorias).result()}
        elementos_data = {row['nombre']: row for row in client.query(query_elementos).result()}
        unidades_data = [
            {"id_unidad_medida": row["id_unidad_medida"], "id_elemento": row["id_elemento"], "unidad": row["unidad"]}
            for row in client.query(query_unidades).result()
        ]

        rows_to_insert = []
        for item in data:
            unique_id = int(time.time() * 1000)

            # Validar y convertir consumo (valor) a float
            try:
                consumo = float(item["valor"])
            except ValueError:
                return JsonResponse({'message': f'El valor "{item["valor"]}" no es un número válido.'}, status=400)

            # Convertir fechaRegistro a formato TIMESTAMP
            try:
                fecha_registro = datetime.strptime(item["fechaRegistro"], '%Y-%m-%d').isoformat()
            except ValueError:
                return JsonResponse({'message': f'La fecha "{item["fechaRegistro"]}" no tiene el formato correcto YYYY-MM-DD.'}, status=400)

            # Buscar id_categoria
            nombre_categoria = item["categoria"]
            id_categoria = categorias_data.get(nombre_categoria)
            if not id_categoria:
                print(f"No se encontró la categoría: {nombre_categoria}")
                return JsonResponse({'message': f'Categoría "{nombre_categoria}" no existe.'}, status=400)

            # Buscar id_subcategoria
            nombre_subcategoria = item["subcategoria"]
            id_subcategoria = subcategorias_data.get(nombre_subcategoria)
            if not id_subcategoria:
                print(f"No se encontró la subcategoría: {nombre_subcategoria}")
                return JsonResponse({'message': f'Subcategoría "{nombre_subcategoria}" no existe.'}, status=400)

            # Buscar id_elemento
            nombre_elemento = item["elemento"]
            elemento_factors = elementos_data.get(nombre_elemento)
            if not elemento_factors:
                print(f"No se encontró el elemento: {nombre_elemento}")
                return JsonResponse({'message': f'Elemento "{nombre_elemento}" no existe.'}, status=400)

            id_elemento = elemento_factors['id_elemento']

            # Buscar id_unidad_medida
            unidad = item["unidad"]
            id_unidad_medida = None
            for unidad_row in unidades_data:
                if unidad_row["id_elemento"] == id_elemento and unidad_row["unidad"] == unidad:
                    id_unidad_medida = unidad_row["id_unidad_medida"]
                    break

            if not id_unidad_medida:
                print(f"No se encontró unidad de medida para elemento: {id_elemento}, unidad: {unidad}")
                return JsonResponse({'message': f'Unidad "{unidad}" no existe para el elemento "{nombre_elemento}".'}, status=400)

            # Calcular emisiones
            co2_factor = elemento_factors['CO2']
            n2o_factor = elemento_factors['N2O']
            ch4_factor = elemento_factors['CH4']
            hfc_factor = elemento_factors['HFC']
            emision_co2 = round(consumo * co2_factor, 4)
            emision_n2o = round(consumo * n2o_factor, 4)
            emision_ch4 = round(consumo * ch4_factor, 4)
            emision_hfc = round(consumo * hfc_factor, 4)
            tco2_calculado = round((emision_co2 + emision_n2o + emision_ch4 + emision_hfc) / 1000, 4)

            # Construir la fila a insertar
            row = {
                "id": unique_id,
                "fecha_registro": fecha_registro,
                "Rut_Cliente": id_cliente,
                "Nombre_Cliente": nombre_cliente.title(),
                "consumo": consumo,
                "id_unidad_medida": id_unidad_medida,
                "unidad": unidad,
                "Alcance": "3",
                "id_categoria": id_categoria,
                "id_subcategoria": id_subcategoria,
                "id_elemento": id_elemento,
                "Emision_CO2": emision_co2,
                "Emision_N2O": emision_n2o,
                "Emision_CH4": emision_ch4,
                "Emision_HFC": emision_hfc,
                "TCO2_Calculado": tco2_calculado
            }

            rows_to_insert.append(row)

        # Insertar filas en BigQuery
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if not errors:
            return JsonResponse({'message': 'Datos subidos exitosamente'})
        else:
            print('Errors:', errors)
            return JsonResponse({'message': 'Error al subir los datos', 'errors': errors}, status=400)

    except Exception as e:
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
import pandas as pd
import plotly.express as px
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from django.conf import settings
from django.contrib.auth.decorators import login_required
@login_required
def alcance1(request):
    client = bigquery.Client()

    # Capturar filtros desde la solicitud GET
    direcciones_filtro = request.GET.getlist('direcciones')
    year_filtro = request.GET.get('year', 'Todos')
    month_filtro = request.GET.get('month', 'Todos')

    if not direcciones_filtro or "Todos" in direcciones_filtro:
        direcciones_filtro = None

    # Construir consulta SQL con JOIN para incluir el nombre del elemento y el cliente
    query = """
    SELECT 
        EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year,
        EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month,
        e.nombre AS elemento,
        hc.Nombre_Cliente AS cliente,
        {}
        SUM(hc.consumo) AS consumo_total,
        SUM(hc.TCO2_Calculado) AS emisiones_totales
    FROM 
        `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    JOIN 
        `proyectocarbonia-443321.datacarbonia.elemento` AS e
    ON 
        hc.id_elemento = e.id_elemento
    WHERE 
        hc.Alcance = '1'
    """

    if direcciones_filtro:
        direcciones_str = ", ".join([f"'{direccion}'" for direccion in direcciones_filtro])
        query += f" AND hc.Direccion_Cliente IN ({direcciones_str})"
        query = query.format("hc.Direccion_Cliente AS direccion,")
    else:
        query = query.format("'Total' AS direccion,")

    if year_filtro != 'Todos':
        query += f" AND EXTRACT(YEAR FROM hc.Fecha_Inicio) = {year_filtro}"
    if month_filtro != 'Todos':
        query += f" AND EXTRACT(MONTH FROM hc.Fecha_Inicio) = {month_filtro}"

    query += """
    GROUP BY year, month, elemento, cliente, direccion
    ORDER BY year, month;
    """

    query_job = client.query(query)
    data = [
        {
            'year': row.year,
            'month': row.month,
            'elemento': row.elemento,
            'cliente': row.cliente,
            'direccion': row.direccion,
            'consumo': row.consumo_total,
            'emisiones': row.emisiones_totales,
        }
        for row in query_job.result()
    ]
    df = pd.DataFrame(data)

    # Consultar años, meses y direcciones únicas
    query_years = """
    SELECT DISTINCT EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY year;
    """
    years_unicos = [int(row.year) for row in client.query(query_years).result()]

    query_months = """
    SELECT DISTINCT EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY month;
    """
    months_unicos = [int(row.month) for row in client.query(query_months).result()]

    query_direcciones = """
    SELECT DISTINCT hc.Direccion_Cliente AS direccion
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '1'
    ORDER BY direccion;
    """
    direcciones_unicas = [row.direccion for row in client.query(query_direcciones).result()]

    # Generar gráficos con Plotly
    if not df.empty:
        fig1 = px.line(
            df,
            x="month",
            y="emisiones",
            color="direccion",
            title=f"Emisiones Totales por Mes ({'Total Consolidado' if not direcciones_filtro else 'Por Dirección'})",
            labels={"month": "Mes", "emisiones": "Emisiones (tCO2e)", "direccion": "Dirección"}
        )

        fig2 = px.bar(
            df,
            x="month",
            y="consumo",
            color="direccion",
            title=f"Consumo Total por Mes ({'Total Consolidado' if not direcciones_filtro else 'Por Dirección'})",
            labels={"month": "Mes", "consumo": "Consumo Total (m³)", "direccion": "Dirección"}
        )

        graph1_html = fig1.to_html(full_html=False)
        graph2_html = fig2.to_html(full_html=False)
    else:
        graph1_html = graph2_html = "<p>No hay datos para mostrar.</p>"

    # Generar análisis con LangChain
    if not df.empty:
        elemento = df['elemento'].iloc[0]
        cliente = df['cliente'].iloc[0]

        # Prompt para Emisiones
        emisiones_summary = df.groupby('direccion')[['emisiones']].sum().to_dict(orient="index")
        template_emisiones = """
Eres un experto en eficiencia energética y de gran conocimiento en proyecto de Huellas Chile,  estás presentando un informe a un gerente de la empresa. Analiza el consumo energético en metros cúbicos para el cliente {cliente}, quien utiliza {elemento}. Este informe ayudará al gerente a tomar decisiones estratégicas para mejorar la eficiencia energética.
revisa los datos mensuales para no tener sesgos en los datos y no hacer comparaciones incorrectas.
Datos de Emisión:
{emisiones_summary}

Instrucciones para el análisis:
1. Proporciona un análisis conciso de emisiones de tCO2e, identificando patrones o tendencias de interés estratégico.
2. Ofrece 2-3 recomendaciones técnicas y concretas para reducir el consumo en los próximos meses, que sean prácticas y ejecutables a corto plazo.
3. Realiza comparaciones clave entre direcciones, solo si es aplicable. Si no hay suficientes direcciones para comparar, omite esta sección.

Resultados esperados:
1. Análisis del Emisiones de tCO2e.
2. Recomendaciones técnicas.
3. Comparaciones clave entre direcciones, Si no hay suficientes direcciones para comparar, omite esta sección.
"""
        prompt_emisiones = PromptTemplate(
            input_variables=["cliente", "elemento", "emisiones_summary"],
            template=template_emisiones,
        )
        prompt_text_emisiones = prompt_emisiones.format(
            cliente=cliente,
            elemento=elemento,
            emisiones_summary=emisiones_summary,
        )

        # Prompt para Consumo
        consumo_summary = df.groupby('direccion')[['consumo']].sum().to_dict(orient="index")
        template_consumo ="""
Eres un experto en eficiencia energética y de gran onocimiento en proyecto de Huellas Chile,  estás presentando un informe a un gerente de la empresa. Analiza el consumo energético en metros cúbicos para el cliente {cliente}, quien utiliza {elemento}. Este informe ayudará al gerente a tomar decisiones estratégicas para mejorar la eficiencia energética.
revisa los datos mensuales para no tener sesgos en los datos y no hacer comparaciones incorrectas.

Datos de Consumo:
{consumo_summary}

Instrucciones para el análisis:
1. Proporciona un análisis conciso del consumo total, identificando patrones o tendencias de interés estratégico.
2. Ofrece 2-3 recomendaciones técnicas y concretas para reducir el consumo en los próximos meses, que sean prácticas y ejecutables a corto plazo.
3. Realiza comparaciones clave entre direcciones, solo si es aplicable. Si no hay suficientes direcciones para comparar, omite esta sección.

Resultados esperados:
1. Análisis del consumo total.
2. Recomendaciones técnicas.
3. Comparaciones clave entre direcciones, Si no hay suficientes direcciones para comparar, omite esta sección.
"""
        prompt_consumo = PromptTemplate(
            input_variables=["cliente", "elemento", "consumo_summary"],
            template=template_consumo,
        )
        prompt_text_consumo = prompt_consumo.format(
            cliente=cliente,
            elemento=elemento,
            consumo_summary=consumo_summary,
        )

        # Llamadas a la API de LangChain y generación de recomendaciones
    llm = ChatOpenAI(temperature=0.5, model="gpt-4o", openai_api_key=settings.OPENAI_API_KEY)
    recommendations_emisiones = llm.invoke(prompt_text_emisiones).content
    recommendations_consumo = llm.invoke(prompt_text_consumo).content

    # Limpieza y formateo de las recomendaciones
    clean_recommendations_emisiones = clean_markdown(recommendations_emisiones)
    clean_recommendations_consumo = clean_markdown(recommendations_consumo)

    
    # Preparar el contexto para el template
    context = {
        'data': data,
        'direcciones_unicas': direcciones_unicas,
        'years_unicos': years_unicos,
        'months_unicos': months_unicos,
        'direcciones_filtro': direcciones_filtro,
        'year_filtro': year_filtro,
        'month_filtro': month_filtro,
        'graph1': graph1_html,
        'graph2': graph2_html,
        'recommendations_emisiones': clean_recommendations_emisiones,
        'recommendations_consumo': clean_recommendations_consumo,
         }

    return render(request, 'alcance1.html', context)


from django.shortcuts import render
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def alcance2(request):
    client = bigquery.Client()

    # Capturar filtros desde la solicitud GET
    direcciones_filtro_2 = request.GET.getlist('direcciones_2')
    year_filtro_2 = request.GET.get('year_2', 'Todos')
    month_filtro_2 = request.GET.get('month_2', 'Todos')

    if not direcciones_filtro_2 or "Todos" in direcciones_filtro_2:
        direcciones_filtro_2 = None

    # Construir consulta SQL con JOIN para incluir el nombre del elemento y el cliente
    query_2 = """
    SELECT 
        EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year,
        EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month,
        e.nombre AS elemento_2,
        hc.Nombre_Cliente AS cliente_2,
        {}
        SUM(hc.consumo) AS consumo_total_2,
        SUM(hc.TCO2_Calculado) AS emisiones_totales_2
    FROM 
        `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    JOIN 
        `proyectocarbonia-443321.datacarbonia.elemento` AS e
    ON 
        hc.id_elemento = e.id_elemento
    WHERE 
        hc.Alcance = '2'
    """

    if direcciones_filtro_2:
        direcciones_str_2 = ", ".join([f"'{direccion}'" for direccion in direcciones_filtro_2])
        query_2 += f" AND hc.Direccion_Cliente IN ({direcciones_str_2})"
        query_2 = query_2.format("hc.Direccion_Cliente AS direccion_2,")
    else:
        query_2 = query_2.format("'Total' AS direccion_2,")

    if year_filtro_2 != 'Todos':
        query_2 += f" AND EXTRACT(YEAR FROM hc.Fecha_Inicio) = {year_filtro_2}"
    if month_filtro_2 != 'Todos':
        query_2 += f" AND EXTRACT(MONTH FROM hc.Fecha_Inicio) = {month_filtro_2}"

    query_2 += """
    GROUP BY year, month, elemento_2, cliente_2, direccion_2
    ORDER BY year, month;
    """

    query_job_2 = client.query(query_2)
    data_2 = [
        {
            'year': row.year,
            'month': row.month,
            'elemento_2': row.elemento_2,
            'cliente_2': row.cliente_2,
            'direccion_2': row.direccion_2,
            'consumo_2': row.consumo_total_2,
            'emisiones_2': row.emisiones_totales_2,
        }
        for row in query_job_2.result()
    ]
    df_2 = pd.DataFrame(data_2)

    # Consultar años, meses y direcciones únicas para alcance 2
    query_years_2 = """
    SELECT DISTINCT EXTRACT(YEAR FROM hc.Fecha_Inicio) AS year
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '2'
    ORDER BY year;
    """
    years_unicos_2 = [int(row.year) for row in client.query(query_years_2).result()]

    query_months_2 = """
    SELECT DISTINCT EXTRACT(MONTH FROM hc.Fecha_Inicio) AS month
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '2'
    ORDER BY month;
    """
    months_unicos_2 = [int(row.month) for row in client.query(query_months_2).result()]

    query_direcciones_2 = """
    SELECT DISTINCT hc.Direccion_Cliente AS direccion
    FROM `proyectocarbonia-443321.datacarbonia.huella_carbono` AS hc
    WHERE hc.Alcance = '2'
    ORDER BY direccion;
    """
    direcciones_unicas_2 = [row.direccion for row in client.query(query_direcciones_2).result()]

    # Generar gráficos con Plotly para alcance 2
    if not df_2.empty:
        fig1_2 = px.line(
            df_2,
            x="month",
            y="emisiones_2",
            color="direccion_2",
            title=f"Emisiones Totales por Mes (Alcance 2)",
            labels={"month": "Mes", "emisiones_2": "Emisiones (tCO2e)", "direccion_2": "Dirección"}
        )

        fig2_2 = px.bar(
            df_2,
            x="month",
            y="consumo_2",
            color="direccion_2",
            title=f"Consumo Total por Mes (Alcance 2)",
            labels={"month": "Mes", "consumo_2": "Consumo Total (m³)", "direccion_2": "Dirección"}
        )

        graph1_html_2 = fig1_2.to_html(full_html=False)
        graph2_html_2 = fig2_2.to_html(full_html=False)
    else:
        graph1_html_2 = graph2_html_2 = "<p>No hay datos para mostrar.</p>"

    # Preparar el contexto para el template
    context_2 = {
        'data_2': data_2,
        'direcciones_unicas_2': direcciones_unicas_2,
        'years_unicos_2': years_unicos_2,
        'months_unicos_2': months_unicos_2,
        'direcciones_filtro_2': direcciones_filtro_2,
        'year_filtro_2': year_filtro_2,
        'month_filtro_2': month_filtro_2,
        'graph1_2': graph1_html_2,
        'graph2_2': graph2_html_2,
    }

    return render(request, 'alcance2.html', context_2)



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

import pandas as pd
from django.http import HttpResponse
from google.cloud import bigquery

def infostoric_export_excel(request):
    """Exporta los datos de huella_carbono a un archivo Excel con hojas separadas."""
    client = bigquery.Client()
    alcance = request.GET.get('alcance', '')  # Obtiene el filtro de alcance desde la URL
    search_query = request.GET.get('search', '')  # Obtiene el término de búsqueda desde la URL

    # Crear el archivo Excel en memoria
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="huella_carbono.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        # Consulta completa para la hoja "Todos"
        base_query = "SELECT * FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`"
        full_query_job = client.query(base_query)
        full_results = full_query_job.result()
        full_data = [dict(row) for row in full_results]
        full_df = pd.DataFrame(full_data)

        # Convertir columnas con zona horaria
        for column in full_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
            full_df[column] = full_df[column].dt.tz_localize(None)

        # Escribir hoja "Todos"
        full_df.to_excel(writer, index=False, sheet_name='Todos')

        # Consultas separadas por alcance
        for alcance_num in [1, 2, 3]:
            alcance_query = f"""
            SELECT * FROM `proyectocarbonia-443321.datacarbonia.huella_carbono`
            WHERE CAST(Alcance AS STRING) = '{alcance_num}'
            """
            alcance_query_job = client.query(alcance_query)
            alcance_results = alcance_query_job.result()
            alcance_data = [dict(row) for row in alcance_results]
            alcance_df = pd.DataFrame(alcance_data)

            # Convertir columnas con zona horaria
            for column in alcance_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
                alcance_df[column] = alcance_df[column].dt.tz_localize(None)

            # Escribir hoja para cada alcance si hay datos
            if not alcance_df.empty:
                alcance_df.to_excel(writer, index=False, sheet_name=f'Alcance {alcance_num}')

        # Si hay un filtro, generar hoja filtrada
        if alcance or search_query:
            conditions = []
            if alcance:
                conditions.append(f"CAST(Alcance AS STRING) = '{alcance}'")
            if search_query:
                conditions.append(f"""
                (
                    CAST(Numero_Boleta AS STRING) LIKE '%{search_query}%' OR
                    Nombre_Cliente LIKE '%{search_query}%' OR
                    Direccion_Cliente LIKE '%{search_query}%' OR
                    Empresa_Distribuidora LIKE '%{search_query}%'
                )
                """)
            filtered_query = base_query + " WHERE " + " AND ".join(conditions)
            filtered_query_job = client.query(filtered_query)
            filtered_results = filtered_query_job.result()
            filtered_data = [dict(row) for row in filtered_results]
            filtered_df = pd.DataFrame(filtered_data)

            # Convertir columnas de zona horaria
            for column in filtered_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
                filtered_df[column] = filtered_df[column].dt.tz_localize(None)

            # Escribir hoja "Filtrado"
            if not filtered_df.empty:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtrado')

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

def clean_markdown(text):
    """
    Convierte los símbolos de Markdown en formato HTML limpio y elimina saltos de línea adicionales.
    """
    # Reemplazar títulos Markdown (###) por etiquetas <b>
    text = text.replace('###', '<b>').replace('\n', '</b><br>')

    # Reemplazar texto entre **...** con etiquetas <b>...</b>
    while '**' in text:
        text = text.replace('**', '<b>', 1).replace('**', '</b>', 1)
    
    # Eliminar saltos de línea adicionales
    text = text.replace('\n', '').strip()
    
    return text


