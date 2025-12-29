from src.utils.file_loader import load_cv, load_offer
from src.core.evaluator import CVAnalyzer
# Asegúrate de que el archivo anterior se llame 'interviewer.py' dentro de src/core/
from src.core.interviewer import Interviewer 

def main():
    # 1. Cargar Archivos
    try:
        text_offer = load_offer(filename="oferta1.txt")
        text_cv = load_cv(filename="cv_candidato1.txt")
    except FileNotFoundError as e:
        print(f"Error cargando archivos: {e}")
        return

    # 2. Análisis Fase 1
    analyzer = CVAnalyzer()
    print("--- ANALIZANDO CV INICIAL ---")
    result = analyzer.analyze(text_offer, text_cv)
    
    print("\n--- RESULTADO DE LA EVALUACIÓN (FASE 1) ---")
    print(f"Score: {result.score}/100")
    
    # 3. Decisión: ¿Entrevistar o no?
    if not result.discarded and result.not_found_requirements:
        print(f"\nRequisitos a validar: {result.not_found_requirements}")
        print(f"🚀 Iniciando Agente de Entrevista...")
        
        # Instancia correcta de la clase
        interviewer = Interviewer()
        
        # A) Ejecutar entrevista (Esto bloqueará la consola hasta que termine)
        interviewer.conduct_interview(result.not_found_requirements)
        
        # B) Re-evaluar con la información nueva
        final_result = interviewer.reevaluate(text_offer, text_cv)
        
        print("\n=== 🏁 RESULTADO FINAL DEFINITIVO ===")
        print(f"Score Final: {final_result.score}/100")

    elif result.discarded:
        print("\nEl candidato fue descartado en la fase 1. No se requiere entrevista.")
    else:
        print("\nEl candidato cumple todos los requisitos iniciales. No se requiere entrevista técnica extra.")

if __name__ == "__main__":
    main()