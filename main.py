import uuid
from src.utils.file_loader import read_data_file, read_data_file
from src.core.evaluator import CVAnalyzer
from src.core.interviewer import Interviewer 

def main():
    # 1. Cargar Archivos
    try:
        text_offer = read_data_file(filename="oferta1.txt") 
        text_cv = read_data_file(filename="cv_candidato1.txt")
    except Exception as e:
        print(f"Error: {e}")
        return

    # 2. Análisis Fase 1
    analyzer = CVAnalyzer()
    print("--- FASE 1: ANÁLISIS ESTÁTICO ---")
    result = analyzer.analyze(text_offer, text_cv)
    print(f"Score Inicial: {result.score}/100")
    
    # 3. Decisión
    if not result.discarded and result.not_found_requirements:
        print(f"\nRequisitos a validar: {result.not_found_requirements}")
        print(f"🚀 Iniciando Agente (LangGraph)...")
        
        interviewer = Interviewer()
        thread_id = str(uuid.uuid4())
        
        # Saludo
        bot_msg = interviewer.initialize_interview(result.not_found_requirements, thread_id)
        print(f"\n🤖 Agente: {bot_msg.content}")
        
        # Bucle
        active = True
        while active:
            user_input = input("👤 Candidato: ")
            
            # Procesar
            response = interviewer.process_message(user_input, thread_id)
            
            # Limpiar token para el usuario
            clean_response = response.content.replace("[FIN_ENTREVISTA]", "").strip()
            print(f"\n🤖 Agente: {clean_response}")
            
            # CHECK DE PARADA: El agente ahora está forzado a emitir esto si terminó
            if "[FIN_ENTREVISTA]" in response.content:
                print("\n✅ Entrevista finalizada. Procediendo a re-evaluación...")
                active = False # ROMPE EL BUCLE
        
        # 4. Reevaluación Automática
        print("\n... Generando informe final ...")
        final = interviewer.reevaluate(text_offer, text_cv, thread_id)
        
        print("\n=== 🏁 RESULTADO DEFINITIVO ===")
        print(f"Score Final: {final.score}/100")
        print(f"Decisión: {'⛔ DESCARTADO' if final.discarded else '🎉 CONTRATABLE'}")
        print(f"Explicación:\n{final.explaination}")

    elif result.discarded:
        print("Candidato descartado en fase 1.")
    else:
        print("Candidato directo.")

if __name__ == "__main__":
    main()