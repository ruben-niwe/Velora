import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Importación correcta basada en tu estructura de carpetas
from src.core.interviewer import Interviewer, AgentState

class TestInterviewer:

    @pytest.fixture
    def mock_llm_setup(self):
        """
        Crea mocks separados para el LLM base y el LLM con herramientas.
        Esto evita confusión y asegura que 'invoke' sea siempre un Mock.
        """
        mock_base = MagicMock()
        mock_with_tools = MagicMock()
        
        # Configuramos para que al hacer bind_tools devuelva el segundo mock
        mock_base.bind_tools.return_value = mock_with_tools
        
        return mock_base, mock_with_tools

    @pytest.fixture
    def interviewer(self, mock_llm_setup):
        """
        Fixture que instancia el Interviewer con el get_llm parcheado CORRECTAMENTE.
        Usamos la ruta completa: 'src.core.interviewer.get_llm'
        """
        mock_base, mock_with_tools = mock_llm_setup
        
        # IMPORTANTE: La ruta del patch debe ser donde se USA get_llm
        with patch('src.core.interviewer.get_llm', return_value=mock_base):
            interviewer_instance = Interviewer(provider="openai")
            return interviewer_instance

    def test_initialize_interview_structure(self, interviewer):
        thread_id = "test_thread_1"
        missing_reqs = ["Python", "Docker"]
        
        # Mockeamos la memoria/estado del grafo
        interviewer.graph.update_state = MagicMock()
        interviewer.graph.invoke = MagicMock(return_value={"messages": [AIMessage(content="Hola")]})

        interviewer.initialize_interview(missing_reqs, thread_id)

        args, _ = interviewer.graph.update_state.call_args
        state_passed = args[1]
        
        # Validamos que se creó el mensaje de sistema correctamente
        sys_msg = state_passed["messages"][0]
        assert "Python, Docker" in sys_msg.content

    def test_process_message_calls_graph(self, interviewer):
        thread_id = "test_thread_2"
        user_input = "Hola"
        expected_response = AIMessage(content="Hola")
        
        interviewer.graph.invoke = MagicMock(return_value={"messages": [expected_response]})

        response = interviewer.process_message(user_input, thread_id)
        assert response == expected_response

    # IMPORTANTE: Parcheamos la clase EN el módulo interviewer
    @patch('src.core.interviewer.CVAnalyzer') 
    def test_reevaluate_logic(self, mock_analyzer_cls, interviewer):
        thread_id = "test_thread_3"
        offer_text = "Oferta"
        original_cv = "CV"
        
        # 1. Configurar el grafo para devolver historial
        mock_state = MagicMock()
        mock_state.values = {"messages": [AIMessage(content="Test")]}
        interviewer.graph.get_state = MagicMock(return_value=mock_state)

        # 2. Configurar el mock de CVAnalyzer
        mock_instance = MagicMock()
        mock_analyzer_cls.return_value = mock_instance # Cuando se instancie, devuelve esto
        
        # 3. Ejecutar
        interviewer.reevaluate(offer_text, original_cv, thread_id)

        # 4. Verificar
        # Ahora sí debería funcionar porque hemos interceptado la clase correcta
        mock_instance.analyze.assert_called_once()
        
        # Verificamos que se pasó el texto concatenado
        args = mock_instance.analyze.call_args[0]
        assert "=== TRANSCRIPCIÓN ENTREVISTA ===" in args[1]

    def test_logic_skill_removal_mocking_llm(self, interviewer):
        """
        Verifica la lógica de eliminación de skills simulando la respuesta del LLM.
        """
        # 1. Preparar la respuesta simulada del LLM (Tool Call)
        tool_call_mock = {
            "name": "registrar_validacion",
            "args": {"skill": "Python", "conclusion": "Ok"},
            "id": "call_1"
        }
        
        ai_msg_with_tool = AIMessage(content="", tool_calls=[tool_call_mock])
        final_msg = AIMessage(content="Fin")

        # 2. Inyectar el comportamiento en el LLM mockeado
        # interviewer.llm_with_tools es un MagicMock gracias al fixture corregido
        interviewer.llm_with_tools.invoke.side_effect = [ai_msg_with_tool, final_msg]

        # 3. Configurar estado inicial
        initial_state = {
            "messages": [HumanMessage(content="Go")],
            "skills_pending": ["Python", "Java"]
        }
        config = {"configurable": {"thread_id": "thread_logic"}}
        interviewer.graph.update_state(config, initial_state)

        # 4. Ejecutar el grafo REAL (sin mockear graph.invoke)
        # Esto ejecutará custom_tool_node
        interviewer.graph.invoke(None, config=config)

        # 5. Verificar resultado en el estado
        final_state = interviewer.graph.get_state(config).values
        
        # Python debe haber sido eliminado de la lista
        assert "Python" not in final_state["skills_pending"]
        assert "Java" in final_state["skills_pending"]