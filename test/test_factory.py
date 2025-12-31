import pytest
import os
from unittest.mock import patch, MagicMock


from src.llm.factory import get_llm, get_safe_content

class TestContentParser:
    """Test para la función de utilidad get_safe_content"""

    def test_get_safe_content_string(self):
        """Si recibe un string, debe devolver el mismo string."""
        msg = "Hola mundo"
        assert get_safe_content(msg) == "Hola mundo"

    def test_get_safe_content_list_of_strings(self):
        """Si recibe una lista de strings, debe unirlos."""
        msg = ["Hola", " ", "mundo"]
        assert get_safe_content(msg) == "Hola mundo"

    def test_get_safe_content_list_of_dicts(self):
        """Si recibe una lista de diccionarios (formato Gemini), extrae el campo text."""
        msg = [{"text": "Hola"}, {"type": "image"}, {"text": " mundo"}]
        assert get_safe_content(msg) == "Hola mundo"

    def test_get_safe_content_mixed_empty(self):
        """Maneja listas vacías o tipos desconocidos devolviendo string vacío o parcial."""
        assert get_safe_content([]) == ""
        assert get_safe_content(None) == ""

class TestLLMFactory:
    """Tests para la creación de LLMs (OpenAI y Gemini)"""

    # ----------------------------------------------------------------
    # TESTS PARA OPENAI
    # ----------------------------------------------------------------

    @patch("src.llm.factory.ChatOpenAI") # Mockeamos la clase de LangChain
    def test_get_llm_openai_success(self, mock_chat_openai):
        """
        Verifica que si existe la API KEY, se instancia ChatOpenAI 
        con los parámetros correctos.
        """
        # Simulamos que existe la variable de entorno
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake-key-123"}):
            llm = get_llm("openai")

            # Verificamos que se llamó al constructor de ChatOpenAI
            mock_chat_openai.assert_called_once()
            
            # Verificamos los argumentos exactos pasados al constructor
            _, kwargs = mock_chat_openai.call_args
            assert kwargs["model"] == "gpt-5"
            assert kwargs["api_key"] == "sk-fake-key-123"
            assert kwargs["temperature"] == 0
            
            # Verificamos que devuelve la instancia mockeada
            assert llm == mock_chat_openai.return_value

    def test_get_llm_openai_missing_key(self):
        """
        Verifica que lance ValueError si no hay API Key.
        """
        # Simulamos que NO existe la variable de entorno (borrándola temporalmente)
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                get_llm("openai")
            
            assert "Api Key de OpenAI no encontrada" in str(excinfo.value)

    # ----------------------------------------------------------------
    # TESTS PARA GEMINI
    # ----------------------------------------------------------------

    @patch("src.llm.factory.ChatGoogleGenerativeAI") # Mockeamos la clase de Google
    def test_get_llm_gemini_success(self, mock_chat_google):
        """
        Verifica que si existe la API KEY, se instancia ChatGoogleGenerativeAI.
        """
        # Simulamos la variable de entorno de Google
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "google-fake-key-456"}):
            llm = get_llm("gemini")

            mock_chat_google.assert_called_once()
            
            # Verificamos argumentos
            _, kwargs = mock_chat_google.call_args
            assert kwargs["model"] == "gemini-3-pro-preview"
            assert kwargs["google_api_key"] == "google-fake-key-456"
            assert kwargs["temperature"] == 0

    def test_get_llm_gemini_missing_key(self):
        """
        Verifica error si falta la key de Google.
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                get_llm("gemini")
            
            assert "Api Key de Google no encontrada" in str(excinfo.value)

    # ----------------------------------------------------------------
    # TESTS DE LÓGICA GENERAL
    # ----------------------------------------------------------------

    @patch("src.llm.factory.get_llm_openai")
    def test_factory_case_insensitive(self, mock_get_openai):
        """Verifica que 'OpenAI', 'openai' y 'OPENAI' funcionen igual."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake"}):
            get_llm("OpenAI")
            get_llm("OPENAI")
            
            assert mock_get_openai.call_count == 2

    def test_factory_unknown_provider(self):
        """Verifica que devuelve None si el proveedor no existe."""
        result = get_llm("modelo_inventado")
        assert result is None