from pydantic import BaseModel, Field
from typing import List


class EvaluationResult(BaseModel):
    score : int = Field(..., description="Puntuación final del 0 al 100. Si hay un requisito obligatorio no cumplido, debe ser 0.")
    discarded : bool = Field(..., description="True si el candidato no cumple algún requisito obligatorio, False en caso contrario.")
    matching_requirements : List[str] = Field(..., description="Lista de requisitos de la oferta que el candidato SÍ cumple.")
    unmatching_requirements: List[str] = Field(default_factory=list, description="Lista de requisitos que el candidato explícitamente NO cumple (aparecen en el CV pero no alcanzan el nivel o son negativos).")
    not_found_requirements: List[str] = Field(default_factory=list,description="Lista de requisitos de la oferta que NO se mencionan en absoluto en el CV (información faltante).")
    explaination: str = Field(default="", description="Explicación detallada del análisis realizado por el LLM.")