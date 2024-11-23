import openai
from django.conf import settings

def generate_analysis_prompt_with_chatgpt(data):
    if not data:
        return "No hay datos suficientes para realizar un análisis."

    # Configurar la clave de API desde settings.py
    openai.api_key = settings.OPENAI_API_KEY

    # Preparar los datos para el análisis
    formatted_data = "\n".join(
        [f"Dirección: {item['direccion']}, Total TCO2: {item['total_TCO2']}, Registros: {item['registros']}" for item in data]
    )

    # Crear el prompt para la API de OpenAI
    prompt = f"""
    Estos son los datos consolidados de huella de carbono por dirección:
    {formatted_data}.
    
    Por favor, genera un análisis indicando:
    1. La dirección con mayor impacto en términos de emisiones.
    2. Comparaciones entre las principales direcciones.
    3. Sugerencias para reducir la huella de carbono.
    """

    # Llamar a la API de OpenAI
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Cambia el modelo si es necesario
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error al generar análisis con ChatGPT: {e}")
        return "Ocurrió un error al generar el análisis. Por favor, intente nuevamente."
