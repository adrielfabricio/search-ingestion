import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingest import (
    load_pdf,
    split_documents,
    get_embeddings,
    store_documents,
    ingest_pdf
)


class TestLoadPdf(unittest.TestCase):
    """Testes para carregamento de PDF."""
    
    @patch('ingest.PyPDFLoader')
    def test_load_pdf_success(self, mock_loader_class):
        """Testa carregamento bem-sucedido de PDF."""
        # Mock do loader
        mock_loader = Mock()
        mock_doc1 = Mock()
        mock_doc1.page_content = "Conteúdo da página 1"
        mock_doc2 = Mock()
        mock_doc2.page_content = "Conteúdo da página 2"
        mock_loader.load.return_value = [mock_doc1, mock_doc2]
        mock_loader_class.return_value = mock_loader
        
        # Executar
        result = load_pdf("test.pdf")
        
        # Verificar
        self.assertEqual(len(result), 2)
        mock_loader_class.assert_called_once_with("test.pdf")
        mock_loader.load.assert_called_once()
    
    @patch('ingest.PyPDFLoader')
    def test_load_pdf_file_not_found(self, mock_loader_class):
        """Testa erro quando PDF não é encontrado."""
        mock_loader_class.side_effect = FileNotFoundError("Arquivo não encontrado")
        
        # Executar e verificar exceção
        with self.assertRaises(FileNotFoundError):
            load_pdf("nonexistent.pdf")


class TestSplitDocuments(unittest.TestCase):
    """Testes para divisão de documentos em chunks."""
    
    @patch('ingest.RecursiveCharacterTextSplitter')
    def test_split_documents(self, mock_splitter_class):
        """Testa divisão de documentos em chunks."""
        # Mock dos documentos
        mock_doc1 = Mock()
        mock_doc1.page_content = "A" * 2000  # Texto grande
        mock_doc2 = Mock()
        mock_doc2.page_content = "B" * 500
        documents = [mock_doc1, mock_doc2]
        
        # Mock do splitter
        mock_splitter = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.page_content = "A" * 1000
        mock_chunk2 = Mock()
        mock_chunk2.page_content = "A" * 1000
        mock_chunk3 = Mock()
        mock_chunk3.page_content = "B" * 500
        mock_splitter.split_documents.return_value = [mock_chunk1, mock_chunk2, mock_chunk3]
        mock_splitter_class.return_value = mock_splitter
        
        # Executar
        result = split_documents(documents)
        
        # Verificar
        self.assertEqual(len(result), 3)
        mock_splitter_class.assert_called_once_with(
            chunk_size=1000,
            chunk_overlap=150
        )
        mock_splitter.split_documents.assert_called_once_with(documents)


class TestGetEmbeddings(unittest.TestCase):
    """Testes para configuração de embeddings."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_get_embeddings_openai(self, mock_embeddings_class):
        """Testa obtenção de embeddings OpenAI."""
        mock_embeddings = Mock()
        mock_embeddings_class.return_value = mock_embeddings
        
        # Executar
        result = get_embeddings()
        
        # Verificar
        self.assertEqual(result, mock_embeddings)
        mock_embeddings_class.assert_called_once()
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}, clear=True)
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_get_embeddings_google(self, mock_embeddings_class):
        """Testa obtenção de embeddings Google."""
        mock_embeddings = Mock()
        mock_embeddings_class.return_value = mock_embeddings
        
        # Executar
        result = get_embeddings("google")
        
        # Verificar
        self.assertEqual(result, mock_embeddings)
        mock_embeddings_class.assert_called_once_with(model="models/embedding-001")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_embeddings_no_key(self):
        """Testa erro quando não há API key."""
        with self.assertRaises(ValueError) as context:
            get_embeddings()
        
        self.assertIn("OPENAI_API_KEY não encontrada", str(context.exception))


class TestStoreDocuments(unittest.TestCase):
    """Testes para armazenamento de documentos."""
    
    @patch('ingest.PGVector')
    def test_store_documents(self, mock_pgvector_class):
        """Testa armazenamento de documentos."""
        # Mock do vectorstore
        mock_vectorstore = Mock()
        mock_vectorstore.add_documents = Mock()
        mock_pgvector_class.return_value = mock_vectorstore
        
        # Mock dos chunks e embeddings
        mock_chunks = [Mock(), Mock(), Mock()]
        mock_embeddings = Mock()
        connection_string = "postgresql://test"
        
        # Executar
        result = store_documents(mock_chunks, mock_embeddings, connection_string)
        
        # Verificar
        self.assertEqual(result, mock_vectorstore)
        mock_pgvector_class.assert_called_once_with(
            embeddings=mock_embeddings,
            connection=connection_string,
            use_jsonb=True
        )
        mock_vectorstore.add_documents.assert_called_once_with(mock_chunks)


class TestIngestPdf(unittest.TestCase):
    """Testes para função principal de ingestão."""
    
    @patch('ingest.store_documents')
    @patch('ingest.get_embeddings')
    @patch('ingest.split_documents')
    @patch('ingest.load_pdf')
    @patch.dict(os.environ, {
        'PDF_PATH': 'test.pdf',
        'POSTGRES_CONNECTION_STRING': 'postgresql://test'
    })
    def test_ingest_pdf_success(self, mock_load, mock_split, mock_embeddings, mock_store):
        """Testa ingestão completa bem-sucedida."""
        # Setup mocks
        mock_docs = [Mock()]
        mock_load.return_value = mock_docs
        
        mock_chunks = [Mock(), Mock()]
        mock_split.return_value = mock_chunks
        
        mock_emb = Mock()
        mock_embeddings.return_value = mock_emb
        
        mock_vectorstore = Mock()
        mock_store.return_value = mock_vectorstore
        
        # Executar
        result = ingest_pdf()
        
        # Verificar
        self.assertEqual(result, mock_vectorstore)
        mock_load.assert_called_once()
        mock_split.assert_called_once_with(mock_docs)
        mock_embeddings.assert_called_once()
        mock_store.assert_called_once()
    
    @patch('ingest.load_pdf')
    @patch('ingest.split_documents')
    @patch('ingest.get_embeddings')
    @patch.dict(os.environ, {
        'PDF_PATH': 'test.pdf',
        'OPENAI_API_KEY': 'test-key'
    }, clear=True)
    def test_ingest_pdf_no_connection_string(self, mock_get_embeddings, mock_split, mock_load):
        """Testa erro quando não há string de conexão."""
        # Setup mocks para passar até chegar na verificação da connection string
        mock_load.return_value = [Mock()]
        mock_split.return_value = [Mock()]
        mock_get_embeddings.return_value = Mock()
        
        with self.assertRaises(ValueError) as context:
            ingest_pdf()
        
        self.assertIn("DATABASE_URL ou POSTGRES_CONNECTION_STRING", str(context.exception))


if __name__ == '__main__':
    unittest.main()

