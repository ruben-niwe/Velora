import streamlit as st
import uuid
from langchain_core.messages import AIMessage, HumanMessage

# Importaciones de tu lógica de negocio
from src.core.evaluator import CVAnalyzer
from src.core.interviewer import Interviewer

# Configuración de la página
st.set_page_config(page_title="Velora AI Agent", page_icon="🤖")

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Instanciamos el entrevistador una sola vez por sesión
if "interviewer" not in st.session_state:
    st.session_state.interviewer = Interviewer()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "finished" not in st.session_state:
    st.session_state.finished = False

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# Guardamos los textos originales para la reevaluación final (Igual que main.py)
if "offer_text" not in st.session_state:
    st.session_state.offer_text = ""
if "cv_text" not in st.session_state:
    st.session_state.cv_text = ""

# --- UI PRINCIPAL ---
st.title("🤖 Velora: Agente de Entrevistas")

# BARRA LATERAL (Carga de archivos)
with st.sidebar:
    st.header("Documentos")
    offer_file = st.file_uploader("Oferta (TXT)", type="txt")
    cv_file = st.file_uploader("CV (TXT)", type="txt")
    
    st.divider()
    if st.button("Reiniciar Proceso"):
        # Limpiamos todo para empezar de cero
        st.session_state.clear()
        st.rerun()

# --- FASE 1: ANÁLISIS Y DECISIÓN ---
# Solo ejecutamos si hay archivos y no hemos hecho el análisis aún
if offer_file and cv_file and not st.session_state.analysis_done:
    if st.button("Analizar Candidato"):
        # 1. Leer y guardar textos
        st.session_state.offer_text = offer_file.read().decode("utf-8")
        st.session_state.cv_text = cv_file.read().decode("utf-8")
        
        analyzer = CVAnalyzer()
        
        with st.spinner("Realizando análisis estático (Fase 1)..."):
            result = analyzer.analyze(st.session_state.offer_text, st.session_state.cv_text)
        
        # 2. LÓGICA DE DECISIÓN
        
        # CASO A: Requiere Entrevista (Pasa a la siguiente pantalla)
        if not result.discarded and result.not_found_requirements:
            st.session_state.analysis_done = True
            
            # Inicializamos el Agente
            initial_msg = st.session_state.interviewer.initialize_interview(
                result.not_found_requirements, 
                st.session_state.session_id
            )
            st.session_state.messages.append(initial_msg)
            st.rerun()
            
        # CASO B: Resultado Final Inmediato (Ya sea Descartado o Perfecto)
        else:
            st.divider()
            st.subheader("🏁 Resultado Fase 1")
            
            # Columnas de Métricas (Igual que en el reporte final)
            col1, col2 = st.columns(2)
            col1.metric("Score Inicial", f"{result.score}/100")
            
            # Determinamos el estado y el color del mensaje
            if result.discarded:
                col2.metric("Estado", "⛔ DESCARTADO")
                st.markdown("### 📝 Motivo del Descarte")
                st.error(result.explaination) # Caja roja estética
            else:
                col2.metric("Estado", "🎉 DIRECTO (CUMPLE TODO)")
                st.markdown("### 📝 Análisis")
                st.success(result.explaination) # Caja verde estética
            
            # JSON Técnico (Lo que pediste)
            with st.expander("Ver Datos Técnicos (JSON)"):
                st.json(result.model_dump())

                
# --- FASE 2: CHAT (ENTREVISTA) ---
if st.session_state.analysis_done and not st.session_state.finished:
    
    # 1. Renderizar historial
    for msg in st.session_state.messages:
        if isinstance(msg, AIMessage):
            # Limpiamos el token visualmente
            clean_text = msg.content.replace("[FIN_ENTREVISTA]", "")
            if clean_text.strip():
                with st.chat_message("assistant"):
                    st.write(clean_text)
        elif isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.write(msg.content)

    # 2. Input del Usuario
    if prompt := st.chat_input("Responde al entrevistador..."):
        # A. Mostrar mensaje usuario
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.write(prompt)

        # B. Procesar con el Agente
        with st.chat_message("assistant"):
            with st.spinner("..."):
                # Llamada al grafo (Igual que main.py: process_message)
                response = st.session_state.interviewer.process_message(
                    prompt, st.session_state.session_id
                )
                
                # Guardar en historial de sesión UI
                st.session_state.messages.append(response)
                
                # Mostrar respuesta limpia
                clean_response = response.content.replace("[FIN_ENTREVISTA]", "")
                st.write(clean_response)
                
                # C. Chequeo de Parada (Igual que main.py)
                if "[FIN_ENTREVISTA]" in response.content:
                    st.session_state.finished = True
                    st.rerun()

# --- FASE 3: RE-EVALUACIÓN FINAL ---
if st.session_state.finished:
    st.success("✅ Entrevista finalizada.")
    
    with st.spinner("Analizando la transcripción completa y re-calculando score..."):
        
        # 1. Llamada EXACTA a la lógica de main.py
        # Pasamos: Oferta Original, CV Original, ID de Hilo (para sacar la transcripción de memoria)
        final_result = st.session_state.interviewer.reevaluate(
            st.session_state.offer_text,
            st.session_state.cv_text,
            st.session_state.session_id
        )
        
        # 2. Mostrar Resultados
        st.divider()
        st.subheader("🏁 Resultado Definitivo")
        
        col1, col2 = st.columns(2)
        col1.metric("Score Final", f"{final_result.score}/100")
        col2.metric("Decisión", "🎉 CONTRATABLE" if not final_result.discarded else "⛔ DESCARTADO")
        
        st.markdown("### 📝 Explicación Detallada")
        st.info(final_result.explaination)
        
        # Opcional: Mostrar JSON crudo en un expander
        with st.expander("Ver JSON Técnico"):
            st.json(final_result.model_dump())