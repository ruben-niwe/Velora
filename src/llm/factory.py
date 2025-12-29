import os
from langchain_openai import ChatOpenAI
# Si usaras Gemini: from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv

load_dotenv()  # Carga las variables de entorno desde el archivo .env
api_key = os.getenv("OPENAI_API_KEY")

def get_llm():
    """
    Instancia y devuelve el modelo de lenguaje configurado.
    Cambia este código para cambiar de proveedor (OpenAI, Gemini, Claude, etc).
    """
    
    # Asegúrate de tener OPENAI_API_KEY en tus variables de entorno o .env
    if not api_key:
        raise ValueError("La variable de entorno OPENAI_API_KEY no está configurada.")

    # Configuramos temperatura a 0 para máxima determinismo en la evaluación
    llm = ChatOpenAI(
        model="gpt-5",  # O "gpt-3.5-turbo" si quieres ahorrar
        temperature=0,
        api_key=api_key
    )
    
    return llm