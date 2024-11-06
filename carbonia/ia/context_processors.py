# ia/context_processors.py
from google.cloud import bigquery

# ia/context_processors.py

def perfil_cliente(request):
    print("Ejecutando context processor perfil_cliente")  # Línea de depuración
    # Verificar si el usuario está autenticado y tiene un email en la sesión
    if 'email' not in request.session:
        print("No se encontró email en la sesión")  # Línea de depuración
        return {}  # Retorna un contexto vacío si no hay email en la sesión

    # Obtener el email del cliente desde la sesión
    email = request.session['email']
    print("Email en la sesión:", email)  # Línea de depuración

    # (Resto del código para consultar BigQuery y obtener los datos)


    # Inicializar el cliente de BigQuery
    client = bigquery.Client()

    # Consulta SQL para obtener los datos del cliente
    query = """
        SELECT id_cliente, nomcliente, encargado
        FROM `proyectocarbonia.datacarbonia.cliente`
        WHERE emailcliente = @correo
        LIMIT 1
    """
    
    # Configuración de la consulta con parámetros
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("correo", "STRING", email)
        ]
    )
    
    # Ejecuta la consulta
    query_job = client.query(query, job_config=job_config)
    result = query_job.result()

    # Procesa los resultados
    perfil_data = [dict(row) for row in result]

    # Crear el contexto con los datos del perfil o con valores predeterminados si no hay datos
    context = {
        'rut': perfil_data[0].get('id_cliente', 'No Disponible') if perfil_data else 'No Disponible',
        'profile_name': perfil_data[0].get('nomcliente', 'No Disponible') if perfil_data else 'No Disponible',
        'encargado': perfil_data[0].get('encargado', 'No Disponible') if perfil_data else 'No Disponible',
    }
    return context
