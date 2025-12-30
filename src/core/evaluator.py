from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

# Asumo que estos imports existen en tu proyecto
from src.llm.factory import get_llm
from src.llm.prompts import sys_prompt_evaluator
from src.models.schemas import EvaluationResult

class CVAnalyzer:
    def __init__(self, provider="gemini"):
        # Instanciamos el modelo base
        self.llm = get_llm(model_name=provider)

    def analyze(self, offer_text: str, cv_text: str) -> EvaluationResult:
        """
        Analiza el CV contra la oferta y devuelve un objeto EvaluationResult.
        """
        
        # 1. Preparar variables auxiliares
        current_date = datetime.now().strftime("%d/%m/%Y")

        # 2. Crear plantilla de prompt CORREGIDA
        # CAMBIO CLAVE: No usamos f-strings (f"") aquí. 
        # Usamos llaves {} para definir "placeholders" que LangChain rellenará después.
        # Usamos "human" en lugar de "user" para mayor estandarización en LangChain.
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", sys_prompt_evaluator),
            ("human", """OFERTA DE TRABAJO:
{offer_text}

CV DEL CANDIDATO:
{cv_text}

---
Hoy es: {current_date}
""")
        ])

        # 3. Configurar LLM con salida estructurada
        # Esto funciona tanto para OpenAI (tools/json_schema) como Gemini (pydantic)
        structured_llm = self.llm.with_structured_output(EvaluationResult)

        # 4. Crear la cadena (Chain)
        chain = prompt_template | structured_llm

        print(f"Consultando al LLM ({self.llm.name if hasattr(self.llm, 'name') else 'Generico'})...")

        # 5. Invocar la cadena
        # CAMBIO CLAVE: Aquí pasamos el diccionario con los valores reales
        # Las llaves del diccionario deben coincidir con los nombres dentro de {} en el paso 2.
        result = chain.invoke({
            "offer_text": offer_text,
            "cv_text": cv_text,
            "current_date": current_date
        })

        print("LLM ha respondido con el resultado estructurado.")
        # print(result) # Opcional: imprimir para debug
        
        return result