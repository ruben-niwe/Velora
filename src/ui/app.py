import streamlit as st
import uuid
import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

# Importaciones de tu lógica de negocio
from src.core.evaluator import CVAnalyzer
from src.core.interviewer import Interviewer

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Velora AI Agent", layout="wide")

# --- FUNCIÓN AUXILIAR (CRUCIAL PARA GEMINI) ---
def get_safe_content(msg_content):
    """
    Extrae el texto de un mensaje de LangChain de forma segura,
    manejando tanto strings simples (OpenAI) como listas de bloques (Gemini).
    """
    if isinstance(msg_content, str):
        return msg_content
    elif isinstance(msg_content, list):
        # Si es una lista, concatenamos las partes de texto
        text_parts = []
        for item in msg_content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return "".join(text_parts)
    return ""

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "finished" not in st.session_state:
    st.session_state.finished = False

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# Textos originales
if "offer_text" not in st.session_state:
    st.session_state.offer_text = ""
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""

# Datos de control
if "active_requirements" not in st.session_state:
    st.session_state.active_requirements = []
if "current_score" not in st.session_state:
    st.session_state.current_score = 0

# --- UI PRINCIPAL ---
st.title("Velora: Agente de Entrevistas")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    
    # 1. Selector de Proveedor (Para cambiar entre OpenAI y Gemini fácilmente)
    llm_provider = st.selectbox(
        "Modelo IA",
        options=["openai", "gemini"],
        index=0, # Por defecto OpenAI, cambia a 1 para Gemini por defecto
        help="Selecciona el proveedor de LLM a utilizar."
    )
    
    # Instanciamos el entrevistador con el proveedor seleccionado
    # Si 'interviewer' no existe O si cambiamos de proveedor, lo recreamos
    if "interviewer" not in st.session_state or getattr(st.session_state.interviewer, "provider_check", "") != llm_provider:
        st.session_state.interviewer = Interviewer(provider=llm_provider)
        # Guardamos un atributo dummy para saber qué proveedor tiene cargado actualmente
        st.session_state.interviewer.provider_check = llm_provider

    st.divider()
    
    # 2. Lógica de Archivos vs Panel de Entrevista
    if not st.session_state.analysis_done:
        st.subheader("Documentos")
        offer_file = st.file_uploader("Oferta (TXT)", type="txt")
        cv_file = st.file_uploader("CV (TXT)", type="txt")
    
    else:
        st.subheader("🎯 Objetivo")
        st.info("Validando puntos débiles:")
        
        st.metric("Score Pre-Entrevista", f"{st.session_state.current_score}/100")
        
        if st.session_state.active_requirements:
            df_reqs = pd.DataFrame(
                st.session_state.active_requirements, 
                columns=["Requisitos"]
            )
            # Ajuste para evitar el warning de use_container_width
            st.dataframe(df_reqs, hide_index=True, width='stretch')
        else:
            st.write("Sin requisitos pendientes.")

    st.divider()
    if st.button("Reiniciar Proceso"):
        st.session_state.clear()
        st.rerun()

# --- FASE 1: ANÁLISIS Y DECISIÓN ---
if not st.session_state.analysis_done:
    if 'offer_file' in locals() and offer_file and 'cv_file' in locals() and cv_file:
        if st.button("Analizar Candidato"):
            
            st.session_state.offer_text = offer_file.read().decode("utf-8")
            st.session_state.cv_text = cv_file.read().decode("utf-8")
            
            # Pasamos el proveedor seleccionado al Analyzer
            analyzer = CVAnalyzer(provider=llm_provider)
            
            with st.spinner(f"Analizando con {llm_provider.upper()}..."):
                result = analyzer.analyze(st.session_state.offer_text, st.session_state.cv_text)
            
            # --- LÓGICA DE DECISIÓN ---
            
            # A: Pasa a Entrevista
            if not result.discarded and result.not_found_requirements:
                st.session_state.analysis_done = True
                
                st.session_state.active_requirements = result.not_found_requirements
                st.session_state.current_score = result.score
                
                initial_msg = st.session_state.interviewer.initialize_interview(
                    result.not_found_requirements, 
                    st.session_state.session_id
                )
                st.session_state.messages.append(initial_msg)
                st.rerun()
                
            # B: Resultado Final Directo
            else:
                st.divider()
                st.subheader("Resultado Fase 1")
                
                col1, col2 = st.columns(2)
                col1.metric("Score Inicial", f"{result.score}/100")
                
                if result.discarded:
                    col2.metric("Estado", "DESCARTADO")
                    st.error(result.explaination)
                else:
                    col2.metric("Estado", "PERFECTO")
                    st.success(result.explaination)
                
                with st.expander("JSON Técnico"):
                    st.json(result.model_dump())

# --- FASE 2: CHAT (ENTREVISTA) ---
if st.session_state.analysis_done and not st.session_state.finished:
    
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.messages:
            
            # 1. Usamos la función segura para obtener el texto
            content_str = get_safe_content(msg.content)
            
            if isinstance(msg, AIMessage):
                clean_text = content_str.replace("[FIN_ENTREVISTA]", "")
                if clean_text.strip():
                    with st.chat_message("assistant"):
                        st.write(clean_text)
            elif isinstance(msg, HumanMessage):
                with st.chat_message("user"):
                    st.write(content_str)

    if prompt := st.chat_input("Responde al entrevistador..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("..."):
                response = st.session_state.interviewer.process_message(
                    prompt, st.session_state.session_id
                )
                
                st.session_state.messages.append(response)
                
                # Procesamos respuesta segura
                response_str = get_safe_content(response.content)
                clean_response = response_str.replace("[FIN_ENTREVISTA]", "")
                
                st.write(clean_response)
                
                if "[FIN_ENTREVISTA]" in response_str:
                    st.session_state.finished = True
                    st.rerun()

# --- FASE 3: RE-EVALUACIÓN FINAL ---
if st.session_state.finished:
    st.success("Entrevista finalizada.")
    
    with st.spinner("Calculando resultado final..."):
        
        final_result = st.session_state.interviewer.reevaluate(
            st.session_state.offer_text,
            st.session_state.cv_text,
            st.session_state.session_id
        )
        
        st.divider()
        st.subheader("🏁 Resultado Definitivo")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Score Inicial", f"{st.session_state.current_score}/100")
        col2.metric("Score Final", f"{final_result.score}/100", delta=final_result.score - st.session_state.current_score)
        col3.metric("Decisión", "🎉 CONTRATABLE" if not final_result.discarded else "⛔ DESCARTADO")
        
        st.info(final_result.explaination)
        
        with st.expander("JSON Técnico"):
            st.json(final_result.model_dump())