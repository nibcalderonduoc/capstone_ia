from django.shortcuts import render
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from PyPDF2 import PdfReader
from langchain import OpenAI  # Asegúrate de usar la versión correcta
from langchain.chains.question_answering import load_qa_chain
from langchain.docstore.document import Document

# Configurar OpenAI con la clave API directamente
openai_api_key = "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"  # Mantener la clave API directamente en el código
llm = OpenAI(api_key=openai_api_key)

# Vista para subir un archivo y procesarlo
def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        # Obtener el archivo subido
        uploaded_file = request.FILES['pdf_file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        uploaded_file_url = fs.url(filename)

        # Procesar el archivo PDF
        pdf_path = os.path.join(settings.MEDIA_ROOT, filename)
        text_content = extract_text_from_pdf(pdf_path)

        # Usar LangChain para desglosar la información del PDF
        extracted_info = process_with_langchain(text_content)

        # Pasar la información procesada al contexto para mostrarla en la plantilla
        context = {'extracted_info': extracted_info, 'file_url': uploaded_file_url}
        return render(request, 'result.html', context)

    return render(request, 'index.html')

# Función para extraer texto del PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Función para procesar el texto usando LangChain
def process_with_langchain(text):
    # Crear un documento de LangChain
    doc = Document(page_content=text)
    
    # Crear un QA Chain con LangChain
    chain = load_qa_chain(llm, chain_type="stuff")  # Usar 'stuff' como chain_type básico

    # Pregunta para desglosar información de la factura con un rol
    pregunta = """
    Actúa como un experto en facturación y análisis de documentos financieros. A continuación se te proporcionará
    el contenido de una factura en formato PDF. Necesito que extraigas y organizes la siguiente información 
    relevante de manera estructurada:
    
    1. Empresa Distribuidora
    2. Nombre del cliente
    3. Número del cliente
    4. Fechas de lectura del consumo(desde y hasta)
    5. Consumo total en kWh 
    
    en consuno total en kWh solo se necesita el valor numerico sin texto
    """
    
    # Ejecutar el chain con el documento y la pregunta
    result = chain.run(input_documents=[doc], question=pregunta)
    
    return result

# Vista para generar un plan (si tienes una función futura)
def generate_plan(request):
    return render(request, 'generate_plan.html')

#guardar los datos de la pregunta en una lista y traspasarlos a una base de datos de django
