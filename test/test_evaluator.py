import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.core.evaluator import CVAnalyzer 

class MockEvaluationResult:
    def __init__(self, score, comments):
        self.score = score
        self.comments = comments

    def __eq__(self, other):
        return self.score == other.score and self.comments == other.comments

class TestCVAnalyzer:

    @pytest.fixture
    def mock_dependencies(self):
        offer_text = "Se busca desarrollador Python senior."
        cv_text = "Experiencia en Python y Django."
        expected_result = MockEvaluationResult(score=85, comments="Buen perfil")
        
        return offer_text, cv_text, expected_result

    @patch('src.core.evaluator.get_llm') 
    @patch('src.core.evaluator.ChatPromptTemplate') 
    def test_analyze_flow_success(self, mock_prompt_cls, mock_get_llm, mock_dependencies):
        """
        Testea que el método analyze configura la cadena y devuelve el resultado esperado
        sin hacer llamadas externas.
        """
        # 1. Desempaquetar datos de prueba
        offer_text, cv_text, expected_result = mock_dependencies
        
        # 2. Configurar el Mock del LLM (el objeto que devuelve get_llm)
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        
        # Configurar el 'structured_llm'
        mock_structured_llm = MagicMock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm

        # 3. Configurar el Mock del PromptTemplate
        mock_prompt_instance = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt_instance

        mock_chain = MagicMock()
        mock_prompt_instance.__or__.return_value = mock_chain
        
        # 4. Configurar el resultado de .invoke()
        mock_chain.invoke.return_value = expected_result

        # 5. Ejecutar la clase bajo test
        analyzer = CVAnalyzer(provider="openai")
        result = analyzer.analyze(offer_text, cv_text)

        # 6. Aserciones 
        # Verificamos que obtuvimos el resultado esperado
        assert result == expected_result
        
        # Verificamos que se llamó a get_llm con el proveedor correcto
        mock_get_llm.assert_called_once_with(model_name="openai")
        
        # Verificamos que se configuró la salida estructurada
        mock_llm_instance.with_structured_output.assert_called_once()
        
        # Verificamos que se creó el template de mensajes
        mock_prompt_cls.from_messages.assert_called_once()
        
        mock_prompt_instance.__or__.assert_called_once_with(mock_structured_llm)
        

        args_passed_to_invoke = mock_chain.invoke.call_args[0][0]
        
        assert args_passed_to_invoke["offer_text"] == offer_text
        assert args_passed_to_invoke["cv_text"] == cv_text
        # Verificamos que la fecha es la de hoy
        assert args_passed_to_invoke["current_date"] == datetime.now().strftime("%d/%m/%Y")