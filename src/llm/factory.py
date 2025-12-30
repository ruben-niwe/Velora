import os
from dotenv import load_dotenv

# Importaciones de LangChain
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # Carga las variables de entorno desde el archivo .env

def get_llm_openai(model_name="gpt-5", temperature=0):
    """
    Instancia específica para OpenAI.
    Mantiene 'gpt-5' por defecto como pediste.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ Error: OPENAI_API_KEY no encontrada en variables de entorno.")

    return ChatOpenAI(
        model=model_name, 
        api_key=api_key,
        temperature=temperature
    )

def get_llm_gemini(model_name="gemini-3-pro-preview", temperature=0):
    """
    Instancia específica para Google Gemini.
    Modelos comunes: 'gemini-1.5-flash' (rápido) o 'gemini-1.5-pro' (potente).
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ Error: GOOGLE_API_KEY no encontrada en variables de entorno.")

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature
    )

def get_llm(provider="gemini", model_name=None, temperature=0):
    """
    Función genérica (Factory) que decide qué modelo devolver.
    
    Args:
        provider (str): "openai" o "gemini".
        model_name (str): Opcional. Si es None, usa el default de cada función específica.
        temperature (float): 0 para determinismo, 1 para creatividad.
    """
    
    if provider.lower() == "openai":
        # Si no pasan modelo, usamos el default de la función (gpt-5)
        target_model = model_name if model_name else "gpt-5"
        return get_llm_openai(model_name=target_model, temperature=temperature)

    elif provider.lower() == "gemini":
        # Si no pasan modelo, usamos el default de la función (gemini-1.5-flash)
        return get_llm_gemini()

    else:
        raise ValueError(f"Proveedor '{provider}' no soportado. Usa 'openai' o 'gemini'.")