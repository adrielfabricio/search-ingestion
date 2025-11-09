import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector

load_dotenv()

PDF_PATH = os.getenv("PDF_PATH", "document.pdf")


def load_pdf(file_path: str):
    """Carrega arquivo PDF e extrai texto."""
    print(f"📄 Carregando PDF: {file_path}...")
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"✅ PDF carregado! {len(documents)} páginas encontradas.")
        return documents
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo {file_path} não encontrado!")
        raise
    except Exception as e:
        print(f"❌ Erro ao carregar PDF: {e}")
        raise


def split_documents(documents):
    """Divide documentos em chunks de 1000 caracteres com overlap de 150."""
    print("✂️  Dividindo documentos em chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✅ {len(chunks)} chunks criados!")
    return chunks


def get_embeddings(provider: str = "openai"):
    """Retorna instância de embeddings configurada.
    
    Args:
        provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")
    
    Returns:
        Instância de embeddings configurada
    """
    provider = provider.lower()
    
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY não encontrada no .env!")
        print("🔑 Usando OpenAI Embeddings")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    elif provider == "google":
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY não encontrada no .env!")
        print("🔑 Usando Google Gemini Embeddings")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    else:
        raise ValueError(f"Provider '{provider}' não suportado! Use 'openai' ou 'google'.")


def store_documents(chunks, embeddings, connection_string, collection_name=None):
    """Armazena chunks e embeddings no PostgreSQL."""
    print("💾 Armazenando no banco de dados...")
    try:
        vectorstore_params = {
            "embeddings": embeddings,
            "connection": connection_string,
            "use_jsonb": True
        }
        
        # Adicionar collection_name se fornecido
        if collection_name:
            vectorstore_params["collection_name"] = collection_name
        
        vectorstore = PGVector(**vectorstore_params)
        
        # Adicionar documentos
        vectorstore.add_documents(chunks)
        print(f"✅ {len(chunks)} documentos armazenados com sucesso!")
        return vectorstore
    except Exception as e:
        print(f"❌ Erro ao armazenar: {e}")
        raise


def ingest_pdf(provider: str = "openai"):
    """Função principal para ingestão completa do PDF.
    
    Args:
        provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")
    """
    try:
        # 1. Carregar PDF
        documents = load_pdf(PDF_PATH)
        
        # 2. Dividir em chunks
        chunks = split_documents(documents)
        
        # 3. Configurar embeddings
        embeddings = get_embeddings(provider)
        
        # 4. Obter string de conexão (suporta DATABASE_URL ou POSTGRES_CONNECTION_STRING)
        connection_string = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("DATABASE_URL ou POSTGRES_CONNECTION_STRING não encontrada no .env!")
        
        # 5. Obter nome da coleção (opcional)
        collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME") or os.getenv("PGVECTOR_COLLECTION")
        
        # 6. Armazenar no banco
        vectorstore = store_documents(chunks, embeddings, connection_string, collection_name)
        
        print("\n🎉 Ingestão concluída com sucesso!")
        return vectorstore
        
    except Exception as e:
        print(f"\n❌ Erro na ingestão: {e}")
        raise


if __name__ == "__main__":
    ingest_pdf()
