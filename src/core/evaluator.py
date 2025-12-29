from langchain_core.prompts import ChatPromptTemplate
from src.llm.factory import get_llm
from src.llm.prompts import sys_prompt_evaluator
from src.models.schemas import EvaluationResult
from datetime import datetime

class CVAnalyzer:
    def __init__(self):
        self.llm = get_llm()

    def analyze(self, offer_text: str, cv_text:str) -> EvaluationResult:
        """
        Analiza el CV contra la oferta y devuelve un objeto EvaluationResult con la puntuación y detalles.
        """
        # 1. Def prompt
        system_prompt = sys_prompt_evaluator
        current_date = datetime.now().strftime("%d/%m/%Y")

        # 2. Crear plantilla de prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", f"OFERTA DE TRABAJO:\n{offer_text}\n\nCV DEL CANDIDATO:\n{cv_text}\n\n \n\nHoy es: {current_date}"),
        ])

        structured_llm = self.llm.with_structured_output(EvaluationResult)

        chain = prompt_template | structured_llm

        print("Consultando al LLM (FASE 1 de EVALUACIÓN)...")

        result = chain.invoke({
            "offer": offer_text,
            "cv": cv_text
        })
        print("LLM ha respondido con el resultado estructurado:")
        print(result)
        return result