import streamlit as st
import uuid
import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

# --- IMPORTACIONES PROPIAS ---
from src.core.evaluator import CVAnalyzer
from src.core.interviewer import Interviewer
from src.llm.factory import get_safe_content

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Velora AI Recruiter", layout="wide")

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Variables de flujo
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "finished" not in st.session_state:
    st.session_state.finished = False
if "locked" not in st.session_state:
    st.session_state.locked = False # Variable maestra para bloquear la UI

# Variables de datos
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interviewer" not in st.session_state:
    st.session_state.interviewer = None # Aquí guardaremos la instancia del entrevistador
if "current_score" not in st.session_state:
    st.session_state.current_score = 0
if "offer_text" not in st.session_state:
    st.session_state.offer_text = ""
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""
if "active_requirements" not in st.session_state:
    st.session_state.active_requirements = []

# Inicializamos el proveedor por defecto si no existe
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "openai"

# --- UI PRINCIPAL ---
st.title("🤖 Velora: AI Technical Recruiter")

# ==========================================
# BARRA LATERAL
# ==========================================
with st.sidebar:
    st.header("Configuración")
    
    # 1. SELECTOR DE MODELO (CON BLOQUEO)
    # Usamos 'key' para vincularlo a session_state automáticamente.
    # Usamos 'disabled' para que se ponga gris y no se pueda cambiar si ya empezamos.
    st.selectbox(
        "Proveedor de IA",
        options=["openai", "gemini"],
        key="selected_provider", 
        disabled=st.session_state.locked, 
        help="El modelo se bloqueará una vez inicies el análisis."
    )
    
    # Mensaje de estado del bloqueo
    if st.session_state.locked:
        st.caption(f"Motor bloqueado en: **{st.session_state.selected_provider.upper()}**")

    st.divider()

    # 2. CARGA DE ARCHIVOS
    # También bloqueamos la subida de nuevos archivos si ya estamos analizando
    if not st.session_state.analysis_done:
        offer_file = st.file_uploader("Oferta (TXT)", type="txt", disabled=st.session_state.locked)
        cv_file = st.file_uploader("CV (TXT)", type="txt", disabled=st.session_state.locked)
    else:
        # Panel de información durante la entrevista
        st.metric("Score CV", f"{st.session_state.current_score}/100")
        if st.session_state.active_requirements:
            with st.expander("Requisitos a Evaluar"):
                df = pd.DataFrame(st.session_state.active_requirements, columns=["Skill Faltante"])
                st.dataframe(df, hide_index=True, width='stretch')

    st.divider()
    
    # Botón de reinicio completo
    if st.button("Reiniciar Todo", type="primary"):
        st.session_state.clear()
        st.rerun()

# ==========================================
# LÓGICA DE EJECUCIÓN
# ==========================================

# --- FASE 1: ANÁLISIS ---
if not st.session_state.analysis_done:
    if 'offer_file' in locals() and offer_file and 'cv_file' in locals() and cv_file:
        
        if st.button("Analizar Candidato"):
            
            # 1. BLOQUEAR LA INTERFAZ
            st.session_state.locked = True
            
            # 2. CAPTURAR PROVEEDOR ACTUAL
            provider_actual = st.session_state.selected_provider
            
            # Toast de confirmación visual
            st.toast(f"Iniciando motor con: {provider_actual.upper()}")

            try:
                # 3. LEER ARCHIVOS
                st.session_state.offer_text = offer_file.read().decode("utf-8")
                st.session_state.cv_text = cv_file.read().decode("utf-8")
                
                # 4. INSTANCIAR ANALYZER (Aquí saltará el error si falta la Key)
                # Pasamos explícitamente el proveedor seleccionado
                analyzer = CVAnalyzer(provider=provider_actual)
                
                with st.spinner(f"Velora esta analizando tu CV..."):
                    result = analyzer.analyze(st.session_state.offer_text, st.session_state.cv_text)
                
                # Guardar score inicial
                st.session_state.current_score = result.score
                
                # --- DECISIÓN DEL SISTEMA ---
                if not result.discarded and result.not_found_requirements:
                    # A. PASA A ENTREVISTA
                    st.session_state.analysis_done = True
                    st.session_state.active_requirements = result.not_found_requirements
                    
                    # 5. INSTANCIAR INTERVIEWER (Con el mismo proveedor)
                    st.session_state.interviewer = Interviewer(provider=provider_actual)
                    
                    # Generar primera pregunta
                    initial_msg = st.session_state.interviewer.initialize_interview(
                        result.not_found_requirements, 
                        st.session_state.session_id
                    )
                    st.session_state.messages.append(initial_msg)
                    st.rerun()
                
                else:
                    # B. RESULTADO FINAL DIRECTO
                    st.divider()
                    if result.discarded:
                        st.error(f"Candidato Descartado. Score: {result.score}")
                        st.markdown(f"**Motivo:** {result.explaination}")
                    else:
                        st.balloons()
                        st.success(f"Candidato Perfecto. Score: {result.score}")
                        st.markdown(f"**Detalle:** {result.explaination}")
            
            except ValueError as ve:
                # Captura específica de errores de tu Factory (Falta de API Key)
                st.error(str(ve))
                st.session_state.locked = False # Desbloqueamos para permitir cambiar modelo
            except Exception as e:
                # Otros errores
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
            with st.spinner("Pensando..."):
                try:
                    # Usamos la instancia persistente en session_state (la correcta)
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

# --- FASE 3: RESULTADOS ---
if st.session_state.finished:
    st.divider()
    st.success("🏁 Entrevista Finalizada")
    
    if st.button("Ver Informe Final"):
        with st.spinner("Generando reporte definitivo..."):
            try:
                final = st.session_state.interviewer.reevaluate(
                    st.session_state.offer_text, 
                    st.session_state.cv_text, 
                    st.session_state.session_id
                )
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Score Inicial", st.session_state.current_score)
                c2.metric("Score Final", final.score, delta=final.score - st.session_state.current_score)
                decision = "CONTRATAR" if not final.discarded else "DESCARTAR"
                c3.metric("Decisión", decision)
                
                st.subheader("Informe Técnico")
                st.info(final.explaination)
                
                with st.expander("JSON Técnico"):
                    st.json(final.model_dump())

            except Exception as e:
                st.error(f"Error generando reporte: {e}")