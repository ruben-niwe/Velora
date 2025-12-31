import streamlit as st
import uuid
import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

# --- IMPORTACIONES PROPIAS ---
from src.core.evaluator import CVAnalyzer
from src.core.interviewer import Interviewer
from src.llm.factory import get_safe_content

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Velora AI Recruiter", layout="wide", page_icon="🤖")

# --- FUNCIÓN DE VISUALIZACIÓN COMÚN ---
def mostrar_informe_final(result, initial_score=None):
    """
    Renderiza el informe final con métricas, decisión, explicación y JSON.
    Se usa tanto para resultados directos (Fase 1) como post-entrevista (Fase 3).
    """
    st.divider()
    st.subheader("🏁 Informe Técnico Final")

    # 1. Métricas (KPIs)
    col1, col2, col3 = st.columns(3)
    
    # Si no hay score inicial (Fase 1 directa), el inicial es igual al final
    start_score = initial_score if initial_score is not None else result.score
    delta = result.score - start_score
    
    col1.metric("Score Inicial", f"{start_score}/100")
    col2.metric("Score Final", f"{result.score}/100", delta=delta if delta != 0 else None)
    
    decision_label = "✅ CONTRATAR" if not result.discarded else "❌ DESCARTAR"
    # Color visual para la decisión
    decision_color = "green" if not result.discarded else "red"
    col3.markdown(f"**Decisión:** :{decision_color}[{decision_label}]")

    # 2. Explicación Detallada
    st.markdown("### 📝 Evaluación Detallada")
    with st.container(border=True):
        st.markdown(result.explaination)
    
    # 3. Datos Técnicos (JSON)
    with st.expander("💾 Ver JSON Técnico (Datos Crudos)"):
        st.json(result.model_dump())


# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Variables de flujo
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "finished" not in st.session_state:
    st.session_state.finished = False
if "locked" not in st.session_state:
    st.session_state.locked = False 

# Variables de datos
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interviewer" not in st.session_state:
    st.session_state.interviewer = None 
if "current_score" not in st.session_state:
    st.session_state.current_score = 0
if "offer_text" not in st.session_state:
    st.session_state.offer_text = ""
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""
if "active_requirements" not in st.session_state:
    st.session_state.active_requirements = []

# Inicializamos el proveedor por defecto
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "openai"

# --- UI PRINCIPAL ---
st.title("🤖 Velora: AI Technical Recruiter")

# ==========================================
# BARRA LATERAL
# ==========================================
with st.sidebar:
    st.header("Configuración")
    
    # 1. SELECTOR DE MODELO
    st.selectbox(
        "Proveedor de IA",
        options=["openai", "gemini"],
        key="selected_provider", 
        disabled=st.session_state.locked, 
        help="El modelo se bloqueará una vez inicies el análisis."
    )
    
    if st.session_state.locked:
        st.caption(f"🔒 Motor bloqueado en: **{st.session_state.selected_provider.upper()}**")

    st.divider()

    # 2. CARGA DE ARCHIVOS
    if not st.session_state.analysis_done:
        offer_file = st.file_uploader(
            "Oferta (TXT)", 
            type="txt", 
            disabled=st.session_state.locked
        )
        cv_file = st.file_uploader(
            "CV (TXT)", 
            type="txt", 
            disabled=st.session_state.locked
        )
    else:
        # Panel de información post-análisis (solo si hubo entrevista)
        st.metric("Score CV", f"{st.session_state.current_score}/100")
        if st.session_state.active_requirements:
            with st.expander("Requisitos a Evaluar"):
                df = pd.DataFrame(st.session_state.active_requirements, columns=["Skill Faltante"])
                st.dataframe(df, hide_index=True, width='stretch')

    st.divider()
    
    # Botón de reinicio
    if st.button("Reiniciar Todo", type="primary"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# LÓGICA DE EJECUCIÓN
# ==========================================

# --- FASE 1: ANÁLISIS ---
if not st.session_state.analysis_done:
    if 'offer_file' in locals() and offer_file and 'cv_file' in locals() and cv_file:
        
        # Botón de inicio
        if not st.session_state.locked:
            if st.button("Analizar Candidato"):
                st.session_state.locked = True
                st.rerun() 
        
        # Ejecución lógica
        if st.session_state.locked:
            provider_actual = st.session_state.selected_provider
            st.toast(f"Iniciando motor con: {provider_actual.upper()}")

            try:
                # Lectura
                offer_file.seek(0)
                cv_file.seek(0)
                st.session_state.offer_text = offer_file.read().decode("utf-8")
                st.session_state.cv_text = cv_file.read().decode("utf-8")
                
                # Análisis
                analyzer = CVAnalyzer(provider=provider_actual)
                
                with st.spinner(f"Velora está analizando tu CV..."):
                    result = analyzer.analyze(st.session_state.offer_text, st.session_state.cv_text)
                
                st.session_state.current_score = result.score
                
                # --- DECISIÓN DEL SISTEMA ---
                
                # CASO A: Pasamos a entrevista (No descartado Y faltan requisitos)
                if not result.discarded and result.not_found_requirements:
                    st.session_state.analysis_done = True
                    st.session_state.active_requirements = result.not_found_requirements
                    
                    st.session_state.interviewer = Interviewer(provider=provider_actual)
                    
                    initial_msg = st.session_state.interviewer.initialize_interview(
                        result.not_found_requirements, 
                        st.session_state.session_id
                    )
                    st.session_state.messages.append(initial_msg)
                    st.rerun()
                
                # CASO B: Resultado Directo (Descartado O Perfecto)
                else:
                    # Aquí usamos la nueva función para mostrar el informe COMPLETO
                    # Pasamos initial_score=result.score para que el delta sea 0
                    mostrar_informe_final(result, initial_score=result.score)
                    
                    # Mensaje extra visual
                    if result.discarded:
                        st.error("El proceso se ha detenido automáticamente por criterios de descarte.")
                    else:
                        st.success("¡Perfil 100% compatible! No se requiere entrevista adicional.")

            except ValueError as ve:
                st.error(str(ve))
                st.session_state.locked = False
            except Exception as e:
                st.error(f"Error inesperado: {e}")
                st.session_state.locked = False

# --- FASE 2: CHAT ---
if st.session_state.analysis_done and not st.session_state.finished:
    
    # Contenedor de chat
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            content = get_safe_content(msg.content)
            clean_text = content.replace("[FIN_ENTREVISTA]", "")
            
            if isinstance(msg, AIMessage) and clean_text.strip():
                with st.chat_message("assistant"):
                    st.write(clean_text)
            elif isinstance(msg, HumanMessage):
                with st.chat_message("user"):
                    st.write(content)

    # Input de usuario
    if prompt := st.chat_input("Escribe tu respuesta..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Velora..."):
                try:
                    response = st.session_state.interviewer.process_message(
                        prompt, st.session_state.session_id
                    )
                    st.session_state.messages.append(response)
                    
                    resp_str = get_safe_content(response.content)
                    st.write(resp_str.replace("[FIN_ENTREVISTA]", ""))
                    
                    if "[FIN_ENTREVISTA]" in resp_str:
                        st.session_state.finished = True
                        st.rerun()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

# --- FASE 3: RESULTADOS (Solo tras entrevista) ---
if st.session_state.finished:
    
    if st.button("Ver Informe Final Actualizado"):
        with st.spinner("Generando valoración final..."):
            try:
                final = st.session_state.interviewer.reevaluate(
                    st.session_state.offer_text, 
                    st.session_state.cv_text, 
                    st.session_state.session_id
                )
                
                # Usamos la misma función visual
                mostrar_informe_final(final, initial_score=st.session_state.current_score)

            except Exception as e:
                st.error(f"Error generando reporte: {e}")