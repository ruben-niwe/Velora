import operator
import json
from typing import Annotated, List, TypedDict, Union

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.llm.factory import get_llm
from src.core.evaluator import CVAnalyzer

# --- 1. ESTADO DEL AGENTE ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    skills_pending: List[str] # Esta lista se irá vaciando automáticamente

# --- 2. HERRAMIENTA ---
@tool
def registrar_validacion(skill: str, conclusion: str):
    """
    Usa esta herramienta para guardar la evaluación de una skill.
    """
    return f"Validación guardada para '{skill}'."

# --- 3. CLASE INTERVIEWER ---
class Interviewer:
    def __init__(self, provider="gemini"):
        self.llm = get_llm(model_name=provider)
        self.tools = [registrar_validacion]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        
        # --- NODO CHATBOT (CEREBRO) ---
        def chatbot_node(state: AgentState):
            messages = state["messages"]
            pending = state.get("skills_pending", [])
            
            # --- LÓGICA DE TERMINACIÓN FORZADA ---
            # Si la lista está vacía, inyectamos una instrucción oculta
            # para OBLIGAR al LLM a poner el token de fin, diga lo que diga el usuario.
            if not pending:
                force_exit_msg = SystemMessage(content="""
                SISTEMA: Ya no quedan requisitos pendientes. 
                Tu misión ha terminado.
                Despídete amablemente si aún no lo has hecho y escribe OBLIGATORIAMENTE: [FIN_ENTREVISTA]
                """)
                # Invocamos al LLM con esta instrucción extra al final
                response = self.llm_with_tools.invoke(messages + [force_exit_msg])
                return {"messages": [response]}
            
            # Comportamiento normal (Entrevista)
            return {"messages": [self.llm_with_tools.invoke(messages)]}

        # --- NODO DE HERRAMIENTAS PERSONALIZADO ---
        # Este nodo ejecuta la herramienta Y ADEMÁS actualiza la lista 'skills_pending'
        def custom_tool_node(state: AgentState):
            messages = state["messages"]
            last_message = messages[-1]
            pending = state["skills_pending"].copy()
            
            tool_outputs = []
            
            # Iteramos sobre las llamadas a herramientas que pidió el LLM
            for tool_call in last_message.tool_calls:
                if tool_call["name"] == "registrar_validacion":
                    # 1. Ejecutar la lógica de la herramienta (Simulada o real)
                    skill_evaluated = tool_call["args"]["skill"]
                    output_text = registrar_validacion.invoke(tool_call) # Ejecución real
                    
                    # 2. Crear el mensaje de respuesta de la herramienta
                    tool_outputs.append(ToolMessage(
                        content=output_text,
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"]
                    ))
                    
                    # 3. ACTUALIZAR EL ESTADO (Borrar skill de la lista)
                    # Buscamos coincidencias flexibles (ignorando mayúsculas)
                    for req in pending[:]:
                        if req.lower() in skill_evaluated.lower() or skill_evaluated.lower() in req.lower():
                            if req in pending:
                                pending.remove(req)
            
            # Devolvemos los mensajes de las tools Y la nueva lista actualizada
            return {
                "messages": tool_outputs,
                "skills_pending": pending
            }

        # --- DEFINICIÓN DEL GRAFO ---
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", chatbot_node)
        workflow.add_node("tools", custom_tool_node) # Usamos nuestro nodo inteligente

        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=self.memory)

    def initialize_interview(self, missing_requirements: List[str], thread_id: str):
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
        
        IMPORTANTE: 
        Llevamos un control automático. Cuando valides todo, el sistema te avisará para que te despidas.
        Siempre usa el token [FIN_ENTREVISTA] al final de tu despedida.
        """
        
        initial_state = {
            "messages": [SystemMessage(content=sys_msg)],
            "skills_pending": missing_requirements
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        self.graph.update_state(config, initial_state)
        
        events = self.graph.invoke(
            {"messages": [HumanMessage(content="Saluda.")]},
            config=config
        )
        return events["messages"][-1]

    def process_message(self, user_input: str, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        events = self.graph.invoke(
            {"messages": [HumanMessage(content=user_input)]}, 
            config=config
        )
        return events["messages"][-1]

    def get_transcript(self, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        messages = state.values.get("messages", [])
        txt = ""
        for msg in messages:
            if isinstance(msg, AIMessage):
                txt += f"Recruiter: {msg.content}\n"
            elif isinstance(msg, HumanMessage):
                txt += f"Candidato: {msg.content}\n"
        return txt

    def reevaluate(self, offer_text: str, original_cv: str, thread_id: str):
        transcript = self.get_transcript(thread_id)
        augmented_cv = f"{original_cv}\n=== TRANSCRIPCIÓN ENTREVISTA ===\n{transcript}"
        analyzer = CVAnalyzer()
        return analyzer.analyze(offer_text, augmented_cv)