# ia/context_processors.py
from google.cloud import bigquery

def perfil_cliente(request):
    # Verificar si el usuario tiene una sesión iniciada con un email
    if 'email' not in request.session:
        return {}  # Devuelve un diccionario vacío si no hay email en la sesión

    email = request.session['email']

    # Inicializar cliente de BigQuery
    client = bigquery.Client()

    # Consulta para obtener los datos del cliente
    query = """
        SELECT id_cliente AS rut, nomcliente AS profile_name, encargado
        FROM `proyectocarbonia-443321.datacarbonia.cliente`
        WHERE emailcliente = @correo
        LIMIT 1
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("correo", "STRING", email)]
    )
    query_job = client.query(query, job_config=job_config)
    result = query_job.result()

    perfil_data = [dict(row) for row in result]

    # Guardar en la sesión si se encuentran los datos
    if perfil_data:
        request.session['rut'] = perfil_data[0].get('rut')
        request.session['profile_name'] = perfil_data[0].get('profile_name')
        request.session['encargado'] = perfil_data[0].get('encargado')
    else:
        # Si no hay datos disponibles, guarda valores predeterminados
        request.session['rut'] = 'No Disponible'
        request.session['profile_name'] = 'No Disponible'
        request.session['encargado'] = 'No Disponible'

    # Crear el contexto para la plantilla
    return {
        'rut': request.session.get('rut', 'No Disponible'),
        'profile_name': request.session.get('profile_name', 'No Disponible'),
        'encargado': request.session.get('encargado', 'No Disponible'),
    }
