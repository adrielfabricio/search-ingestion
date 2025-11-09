import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from search import (
	get_embeddings,
	get_vectorstore,
	search_prompt,
	create_rag_chain,
	PROMPT_TEMPLATE
)


class TestGetEmbeddings(unittest.TestCase):
	"""Testes para obtenção de embeddings."""

	@patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
	@patch('langchain_openai.OpenAIEmbeddings')
	def test_get_embeddings_openai(self, mock_embeddings_class):
		"""Testa obtenção de embeddings OpenAI."""
		mock_embeddings = Mock()
		mock_embeddings_class.return_value = mock_embeddings

		result = get_embeddings()

		self.assertEqual(result, mock_embeddings)
		mock_embeddings_class.assert_called_once()

	@patch.dict(os.environ, {}, clear=True)
	def test_get_embeddings_no_key(self):
		"""Testa erro quando não há API key."""
		with self.assertRaises(ValueError):
			get_embeddings()


class TestGetVectorstore(unittest.TestCase):
	"""Testes para obtenção do vectorstore."""

	@patch('search.get_embeddings')
	@patch('search.PGVector')
	@patch.dict(os.environ, {
		'POSTGRES_CONNECTION_STRING': 'postgresql://test',
		'OPENAI_API_KEY': 'test-key'
	}, clear=True)
	def test_get_vectorstore(self, mock_pgvector_class, mock_get_embeddings):
		"""Testa obtenção do vectorstore."""
		mock_embeddings = Mock()
		mock_get_embeddings.return_value = mock_embeddings

		mock_vectorstore = Mock()
		mock_pgvector_class.return_value = mock_vectorstore

		result = get_vectorstore()

		self.assertEqual(result, mock_vectorstore)
		mock_get_embeddings.assert_called_once()
		call_args = mock_pgvector_class.call_args
		self.assertEqual(call_args.kwargs['embeddings'], mock_embeddings)
		self.assertEqual(call_args.kwargs['connection'], 'postgresql://test')
		self.assertEqual(call_args.kwargs['use_jsonb'], True)

	@patch.dict(os.environ, {}, clear=True)
	def test_get_vectorstore_no_connection_string(self):
		"""Testa erro quando não há string de conexão."""
		with self.assertRaises(ValueError):
			get_vectorstore()


class TestSearchPrompt(unittest.TestCase):
	"""Testes para busca e montagem de prompt."""

	@patch('search.get_vectorstore')
	def test_search_prompt_success(self, mock_get_vectorstore):
		"""Testa busca bem-sucedida e montagem de prompt."""
		# Mock do vectorstore
		mock_vectorstore = Mock()
		mock_doc1 = Mock()
		mock_doc1.page_content = "Contexto 1"
		mock_doc2 = Mock()
		mock_doc2.page_content = "Contexto 2"
		mock_vectorstore.similarity_search_with_score.return_value = [
			(mock_doc1, 0.1),
			(mock_doc2, 0.2)
		]
		mock_get_vectorstore.return_value = mock_vectorstore

		# Executar
		result = search_prompt("Qual o faturamento?")

		# Verificar
		self.assertIsNotNone(result)
		self.assertIn("CONTEXTO:", result)
		self.assertIn("Contexto 1", result)
		self.assertIn("Contexto 2", result)
		self.assertIn("Qual o faturamento?", result)
		self.assertIn("PERGUNTA DO USUÁRIO:", result)
		mock_vectorstore.similarity_search_with_score.assert_called_once_with(
			query="Qual o faturamento?",
			k=10
		)

	def test_search_prompt_empty_question(self):
		"""Testa retorno None para pergunta vazia."""
		result = search_prompt("")
		self.assertIsNone(result)

		result = search_prompt(None)
		self.assertIsNone(result)

	@patch('search.get_vectorstore')
	def test_search_prompt_error(self, mock_get_vectorstore):
		"""Testa tratamento de erro na busca."""
		mock_get_vectorstore.side_effect = Exception("Erro de conexão")

		result = search_prompt("Teste")
		self.assertIsNone(result)


class TestCreateRagChain(unittest.TestCase):
	"""Testes para criação da chain RAG."""

	@patch('search.PromptTemplate')
	@patch('search.LLMChain')
	def test_create_rag_chain(self, mock_chain_class, mock_prompt_class):
		"""Testa criação da chain RAG."""
		mock_llm = Mock()
		mock_prompt_template = Mock()
		mock_prompt_class.return_value = mock_prompt_template

		mock_chain = Mock()
		mock_chain_class.return_value = mock_chain

		# Executar
		result = create_rag_chain(mock_llm)

		# Verificar
		self.assertEqual(result, mock_chain)
		mock_prompt_class.assert_called_once_with(
			template=PROMPT_TEMPLATE,
			input_variables=["context", "query"]
		)
		mock_chain_class.assert_called_once_with(
			llm=mock_llm,
			prompt=mock_prompt_template
		)


class TestPromptTemplate(unittest.TestCase):
	"""Testes para o template de prompt."""

	def test_prompt_template_structure(self):
		"""Testa estrutura do template de prompt."""
		self.assertIn("CONTEXTO:", PROMPT_TEMPLATE)
		self.assertIn("REGRAS:", PROMPT_TEMPLATE)
		self.assertIn("EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:", PROMPT_TEMPLATE)
		self.assertIn("PERGUNTA DO USUÁRIO:", PROMPT_TEMPLATE)
		self.assertIn("{context}", PROMPT_TEMPLATE)
		self.assertIn("{query}", PROMPT_TEMPLATE)

	def test_prompt_template_formatting(self):
		"""Testa formatação do template."""
		context = "Contexto de teste"
		query = "Pergunta de teste"

		formatted = PROMPT_TEMPLATE.format(context=context, query=query)

		self.assertIn(context, formatted)
		self.assertIn(query, formatted)
		self.assertNotIn("{context}", formatted)
		self.assertNotIn("{query}", formatted)


if __name__ == '__main__':
	unittest.main()

