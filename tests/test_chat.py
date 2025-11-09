import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chat import get_llm


class TestGetLLM(unittest.TestCase):
    """Testes para obtenção do LLM."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('chat.ChatOpenAI')
    def test_get_llm_openai(self, mock_chat_class):
        """Testa obtenção de LLM OpenAI."""
        mock_llm = Mock()
        mock_chat_class.return_value = mock_llm
        
        result = get_llm()
        
        self.assertEqual(result, mock_llm)
        mock_chat_class.assert_called_once_with(
            model="gpt-3.5-turbo",
            temperature=0.0,
            max_tokens=500
        )
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}, clear=True)
    @patch('chat.ChatGoogleGenerativeAI')
    def test_get_llm_google(self, mock_chat_class):
        """Testa obtenção de LLM Google."""
        mock_llm = Mock()
        mock_chat_class.return_value = mock_llm
        
        result = get_llm()
        
        self.assertEqual(result, mock_llm)
        mock_chat_class.assert_called_once_with(
            model="gemini-2.5-flash",
            temperature=0.0,
            max_output_tokens=500
        )
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_no_key(self):
        """Testa erro quando não há API key."""
        with self.assertRaises(ValueError):
            get_llm()


# Nota: Testes de integração do main() são mais complexos devido ao input()
# e podem ser feitos manualmente ou com ferramentas como pytest-cov
# Para testes automatizados do loop de chat, seria necessário mockar input()

if __name__ == '__main__':
    unittest.main()

