import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # Carga las variables de entorno desde el archivo .env

def get_safe_content(msg_content):
    """
    Extrae el texto de un mensaje de LangChain de forma segura,
    - Maneja diferentes formatos de contenido:
    - string simples para OpenAI
    - listas de bloques para Gemini.
    """
    if isinstance(msg_content, str):
        return msg_content
    elif isinstance(msg_content, list):
        # Si es una lista, concatenamos las partes de texto
        text_parts = []
        for item in msg_content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return "".join(text_parts)
    return ""

def get_llm_openai():
    """
    Instancia específica para OpenAI.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Api Key de OpenAI no encontrada en variables de entorno.")

    return ChatOpenAI(
        model="gpt-5", 
        api_key=api_key,
        temperature=0
    )

def get_llm_gemini():
    """
    Instancia específica para Gemini.
    """

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Api Key de Google no encontrada en variables de entorno.")

    return ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        google_api_key=api_key,
        temperature=0
    )

def get_llm(model_name: str):
    """
    Instancia el LLM según el proveedor indicado.
    Soporta 'openai' y 'gemini'.
    Por defecto, usa OpenAI.
    """

    if model_name.lower() == "openai":
        return get_llm_openai()

    elif model_name.lower() == "gemini":
        return get_llm_gemini()
    else:
        return get_llm_openai()  # Por defecto OpenAI
