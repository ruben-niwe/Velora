from typing import List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from src.llm.factory import get_llm
from src.core.evaluator import CVAnalyzer

class Interviewer:
    def __init__(self):
        self.llm = get_llm()
        self.chat_history = []

    def conduct_interview(self, missing_requirements: List[str]):
        """
        Ejecuta la entrevista gestionando el estado de forma local y aislada.
        """
        # 1. ESTADO LOCAL (Solo existe durante esta ejecución de la función)
        # Usamos una lista mutable para que la herramienta interna pueda modificarla
        local_pending_skills = missing_requirements.copy()

        print(f"\n--- INICIANDO ENTREVISTA BREVE ---")

        # 2. DEFINICIÓN DE LA HERRAMIENTA (Closure)
        # Al definirla aquí dentro, tiene acceso a 'local_pending_skills' de esta sesión específica.
        
        @tool
        def registrar_validacion(skill: str, conclusion: str):
            """
            Usa esta herramienta para guardar la conclusión sobre una skill y marcarla como revisada.
            """
            # Accedemos a la variable LOCAL de la función padre
            skill_clean = skill.lower().strip()
            found = False
            
            # Iteramos sobre una copia para poder borrar de la original
            for req in local_pending_skills[:]:
                if req.lower() in skill_clean or skill_clean in req.lower():
                    local_pending_skills.remove(req)
                    found = True
            
            # Feedback para el LLM (Invisible al usuario)
            remaining_str = ", ".join(local_pending_skills) if local_pending_skills else "NINGUNO"
            
            if found:
                return f"OK. '{skill}' registrada y borrada de la lista. Faltan por validar: {remaining_str}"
            else:
                return f"OK. '{skill}' registrada (era extra). Faltan por validar: {remaining_str}"

        # 3. VINCULACIÓN
        # Vinculamos esta herramienta específica (con su estado local) al LLM
        llm_with_tools = self.llm.bind_tools([registrar_validacion])

        # 4. CONFIGURACIÓN DEL SISTEMA
        reqs_str = ", ".join(missing_requirements)
        sys_msg = f"""
        Eres un reclutador técnico profesional encargado de validar los siguientes requisitos: [{reqs_str}].

        OBJETIVO:
        - Validar cada requisito del candidato a través de conversación natural, haciendo que explique su experiencia con ejemplos concretos, pero solo a nivel general.

        SECUENCIA DE LA CONVERSACIÓN:
        1. SALUDO: Comienza saludando al candidato y pregunta su nombre. Espera su respuesta antes de continuar.
        2. ENTREVISTA: Valida los requisitos uno a uno.
        - Haz preguntas simples: "Cuéntame un proyecto donde usaste X tecnología" o "¿Cómo la aplicaste en tu trabajo?".
        - Pide **una descripción general** de la experiencia y rol del candidato.
        - Si la respuesta es vaga, insiste **solo una vez** de manera educada: "Genial, ¿puedes contarme un poco más sobre tu rol o lo que construiste en ese proyecto?".
        - Si el candidato indica que no puede dar más información, **registra lo que haya mencionado** y pasa al siguiente requisito sin insistir más.
        - Evita preguntas técnicas o implementación detallada.

        REGLAS DE INTERACCIÓN:
        - No combines el saludo con la primera pregunta técnica; cada turno debe ser independiente.
        - Haz preguntas de una por una, centradas en un requisito a la vez.
        - Después de que el candidato responda o se niegue a dar más detalles, usa inmediatamente `registrar_validacion`.
        - Comunica en texto plano, conversacional y breve. No uses listas.
        - Sé paciente y respetuoso.

        CRITERIO DE FINALIZACIÓN:
        - La herramienta indicará qué skills faltan. Cuando la lista indique “NINGUNO”, despídete cordialmente del candidato.
        """
        
        self.chat_history.append(SystemMessage(content=sys_msg))
        
        # Trigger Inicial
        start_msg = "Saluda, si no sabes el nombre pregúntalo, y lanza la primera pregunta técnica."
        response = llm_with_tools.invoke(self.chat_history + [HumanMessage(content=start_msg)])
        self.chat_history.append(response)
        
        print(f"\n🤖 Agente: {response.content}")

        # 5. BUCLE PRINCIPAL
        active = True
        while active:
            # A. Input Usuario
            user_input = input("👤 Candidato: ")
            self.chat_history.append(HumanMessage(content=user_input))

            # B. Razonamiento del Agente
            response = llm_with_tools.invoke(self.chat_history)
            self.chat_history.append(response)

            # C. Ejecución de Herramientas
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    # Invocamos la función local
                    tool_output = registrar_validacion.invoke(tool_call["args"])
                    
                    self.chat_history.append(ToolMessage(
                        content=tool_output, 
                        tool_call_id=tool_call["id"]
                    ))

                # D. Respuesta Post-Herramienta (Follow-up)
                follow_up = llm_with_tools.invoke(self.chat_history)
                self.chat_history.append(follow_up)
                print(f"\n🤖 Agente: {follow_up.content}")
                
                # E. Verificación de Estado (Usamos la variable local)
                if not local_pending_skills:
                    # Si la IA ya se despidió o dice que terminó, cortamos
                    low_content = follow_up.content.lower()
                    if any(x in low_content for x in ["gracias", "adiós", "un placer", "terminado"]):
                        active = False

            else:
                # El agente decidió solo hablar (sin usar herramientas)
                print(f"\n🤖 Agente: {response.content}")
                
                # Safety check: Si ya no hay pendientes y se despide
                if not local_pending_skills and "gracias" in response.content.lower():
                    active = False

        print("\n✅ Entrevista finalizada.")

    def reevaluate(self, offer_text: str, original_cv: str):
        # (Sin cambios lógicos, solo procesa el historial)
        print("\n... Re-calculando ...")
        
        transcript = ""
        for msg in self.chat_history:
            if isinstance(msg, AIMessage) and msg.content:
                transcript += f"Recruiter: {msg.content}\n"
            elif isinstance(msg, HumanMessage):
                transcript += f"Candidato: {msg.content}\n"
            elif isinstance(msg, ToolMessage):
                 transcript += f"[SISTEMA - CONCLUSIÓN]: {msg.content}\n"

        augmented_cv = f"""
        {original_cv}
        === TRANSCRIPCIÓN ENTREVISTA ===
        {transcript}
        """

        analyzer = CVAnalyzer()
        return analyzer.analyze(offer_text, augmented_cv)