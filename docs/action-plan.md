# Plano de Ação - Implementação do Sistema de Ingestão e Busca Semântica

## Visão Geral

Este documento apresenta um plano de ação passo a passo para implementar o sistema completo de ingestão e busca semântica baseado em RAG (Retrieval Augmented Generation) usando LangChain, PostgreSQL com pgVector.

## 📋 Pré-requisitos

Antes de começar, verifique:

- [ ] Python 3.9+ instalado
- [ ] Docker e Docker Compose instalados
- [ ] Git instalado (opcional)
- [ ] Conta OpenAI ou Google Gemini com API Key
- [ ] Arquivo PDF para ingestão (`document.pdf`)

## 🎯 Fase 1: Configuração do Ambiente

### Passo 1.1: Preparar Estrutura do Projeto

```bash
# 1. Navegar para o diretório do projeto
cd search-ingestion

# 2. Criar ambiente virtual Python
python3 -m venv venv

# 3. Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Verificar Python e pip
python --version
pip --version
```

**Checkpoint**: Ambiente virtual criado e ativado.

### Passo 1.2: Instalar Dependências

```bash
# Instalar todas as dependências do requirements.txt
pip install -r requirements.txt

# Verificar instalação das principais bibliotecas
python -c "import langchain; print('LangChain OK')"
python -c "import langchain_openai; print('LangChain OpenAI OK')"
python -c "import langchain_postgres; print('LangChain Postgres OK')"
```

**Checkpoint**: Todas as dependências instaladas sem erros.

### Passo 1.3: Configurar Variáveis de Ambiente

```bash
# 1. Criar arquivo .env a partir do template
cp .env.example .env

# 2. Editar .env com suas credenciais
# Usar editor de sua preferência (nano, vim, code, etc.)
nano .env
```

**Arquivo `.env` deve conter:**

```env
# OpenAI (para embeddings e LLM)
OPENAI_API_KEY=sk-...

# OU Google Gemini (alternativa)
# GOOGLE_API_KEY=...

# Caminho do PDF
PDF_PATH=document.pdf

# String de conexão do PostgreSQL
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/rag
```

**Checkpoint**: Arquivo `.env` criado e configurado corretamente.

### Passo 1.4: Verificar PDF Disponível

```bash
# Verificar se o PDF existe
ls -lh document.pdf

# Ou verificar caminho configurado no .env
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('PDF_PATH'))"
```

**Checkpoint**: PDF existe e caminho está correto.

## 🗄️ Fase 2: Configuração do Banco de Dados

### Passo 2.1: Iniciar PostgreSQL com Docker

```bash
# 1. Subir serviços do Docker Compose
docker compose up -d

# 2. Verificar se os containers estão rodando
docker compose ps

# 3. Ver logs para confirmar inicialização
docker compose logs postgres

# Aguardar mensagem: "database system is ready to accept connections"
```

**Checkpoint**: PostgreSQL está rodando e saudável.

### Passo 2.2: Verificar Extensão pgVector

```bash
# 1. Conectar ao banco de dados
docker compose exec postgres psql -U postgres -d rag

# 2. Dentro do psql, verificar extensão
\dx

# Deve mostrar: vector | 0.7.0 | public | pgvector

# 3. Sair do psql
\q
```

**Checkpoint**: Extensão pgVector criada com sucesso.

### Passo 2.3: Testar Conexão Python

```python
# Criar script temporário de teste
# test_connection.py
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

connection_string = os.getenv("POSTGRES_CONNECTION_STRING")

try:
    conn = psycopg.connect(connection_string)
    print("✅ Conexão com PostgreSQL estabelecida!")
    conn.close()
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
```

```bash
python test_connection.py
# Deve imprimir: ✅ Conexão com PostgreSQL estabelecida!
```

**Checkpoint**: Conexão Python → PostgreSQL funcionando.

## 📥 Fase 3: Implementação do Módulo de Ingestão

### Passo 3.1: Implementar Carregamento do PDF

**Arquivo**: `src/ingest.py`

```python
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

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

# Teste
if __name__ == "__main__":
    docs = load_pdf(PDF_PATH)
    print(f"Primeira página: {docs[0].page_content[:100]}...")
```

**Ação**: Implementar e testar.

```bash
python src/ingest.py
```

**Checkpoint**: PDF é carregado corretamente.

### Passo 3.2: Implementar Divisão em Chunks

**Arquivo**: `src/ingest.py` (continuar)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
```

**Ação**: Adicionar função e testar.

```bash
python src/ingest.py
# Deve mostrar número de chunks criados
```

**Checkpoint**: Chunks são criados corretamente (1000 chars, 150 overlap).

### Passo 3.3: Configurar Embeddings

**Arquivo**: `src/ingest.py` (continuar)

```python
from langchain_openai import OpenAIEmbeddings
# OU
# from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_embeddings():
    """Retorna instância de embeddings configurada."""
    # Verificar qual API key está disponível
    if os.getenv("OPENAI_API_KEY"):
        print("🔑 Usando OpenAI Embeddings")
        return OpenAIEmbeddings()
    elif os.getenv("GOOGLE_API_KEY"):
        print("🔑 Usando Google Gemini Embeddings")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings()
    else:
        raise ValueError("Nenhuma API key encontrada no .env!")
```

**Ação**: Implementar e testar.

**Checkpoint**: Embeddings configurados corretamente.

### Passo 3.4: Implementar Armazenamento no PostgreSQL

**Arquivo**: `src/ingest.py` (continuar)

```python
from langchain_postgres import PGVector

def store_documents(chunks, embeddings, connection_string):
    """Armazena chunks e embeddings no PostgreSQL."""
    print("💾 Armazenando no banco de dados...")
    try:
        vectorstore = PGVector(
            embeddings=embeddings,
            connection=connection_string,
            use_jsonb=True
        )
        
        # Adicionar documentos
        vectorstore.add_documents(chunks)
        print(f"✅ {len(chunks)} documentos armazenados com sucesso!")
        return vectorstore
    except Exception as e:
        print(f"❌ Erro ao armazenar: {e}")
        raise
```

**Ação**: Implementar e testar.

**Checkpoint**: Documentos são armazenados no banco.

### Passo 3.5: Implementar Função Principal de Ingestão

**Arquivo**: `src/ingest.py` (completar)

```python
def ingest_pdf():
    """Função principal para ingestão completa do PDF."""
    try:
        # 1. Carregar PDF
        documents = load_pdf(PDF_PATH)
        
        # 2. Dividir em chunks
        chunks = split_documents(documents)
        
        # 3. Configurar embeddings
        embeddings = get_embeddings()
        
        # 4. Obter string de conexão
        connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("POSTGRES_CONNECTION_STRING não encontrada no .env!")
        
        # 5. Armazenar no banco
        vectorstore = store_documents(chunks, embeddings, connection_string)
        
        print("\n🎉 Ingestão concluída com sucesso!")
        return vectorstore
        
    except Exception as e:
        print(f"\n❌ Erro na ingestão: {e}")
        raise

if __name__ == "__main__":
    ingest_pdf()
```

**Ação**: Implementar função completa e executar.

```bash
python src/ingest.py
```

**Checkpoint**: Ingestão completa funciona end-to-end.

### Passo 3.6: Verificar Dados no Banco

```bash
# Conectar ao banco
docker compose exec postgres psql -U postgres -d rag

# Verificar quantidade de chunks
SELECT COUNT(*) FROM langchain_pg_embedding;

# Ver alguns chunks
SELECT 
    id, 
    LEFT(document, 100) as preview,
    array_length(embedding::float[], 1) as embedding_dim
FROM langchain_pg_embedding 
LIMIT 5;

# Sair
\q
```

**Checkpoint**: Dados estão no banco, embeddings têm dimensão correta.

## 🔍 Fase 4: Implementação do Módulo de Busca

### Passo 4.1: Implementar Função de Busca Vetorial

**Arquivo**: `src/search.py` (atualizar)

```python
import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
# OU from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{context}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{query}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def get_vectorstore():
    """Retorna instância do vectorstore conectado ao banco."""
    connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
    
    # Configurar embeddings (mesmo da ingestão)
    if os.getenv("OPENAI_API_KEY"):
        embeddings = OpenAIEmbeddings()
    elif os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings = GoogleGenerativeAIEmbeddings()
    else:
        raise ValueError("Nenhuma API key encontrada!")
    
    # Conectar ao vectorstore existente
    vectorstore = PGVector(
        embeddings=embeddings,
        connection=connection_string,
        use_jsonb=True
    )
    
    return vectorstore

def search_prompt(question: str):
    """Busca chunks relevantes e monta prompt com contexto."""
    if not question:
        return None
    
    try:
        # 1. Obter vectorstore
        vectorstore = get_vectorstore()
        
        # 2. Buscar k=10 chunks mais relevantes
        results = vectorstore.similarity_search_with_score(
            query=question,
            k=10
        )
        
        # 3. Montar contexto com os chunks
        context_parts = []
        for doc, score in results:
            context_parts.append(doc.page_content)
        
        context = "\n\n".join(context_parts)
        
        # 4. Montar prompt completo
        prompt = PROMPT_TEMPLATE.format(
            context=context,
            query=question
        )
        
        return prompt
        
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return None
```

**Ação**: Implementar e testar função.

```python
# Teste rápido
from search import search_prompt
prompt = search_prompt("Qual o faturamento?")
print(prompt[:500])  # Primeiros 500 caracteres
```

**Checkpoint**: Função de busca retorna prompt formatado.

## 💬 Fase 5: Implementação do Módulo de Chat

### Passo 5.1: Configurar LLM

**Arquivo**: `src/chat.py` (atualizar)

```python
import os
from dotenv import load_dotenv
from search import search_prompt

load_dotenv()

def get_llm():
    """Retorna instância do LLM configurado."""
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.0,
            max_tokens=500
        )
    elif os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.0,
            max_output_tokens=500
        )
    else:
        raise ValueError("Nenhuma API key encontrada!")
```

**Checkpoint**: LLM configurado corretamente.

### Passo 5.2: Implementar Loop de Chat

**Arquivo**: `src/chat.py` (continuar)

```python
def main():
    """Função principal do chat CLI."""
    print("🤖 Chat de Busca Semântica")
    print("=" * 50)
    print("Digite 'sair' para encerrar\n")
    
    try:
        # Inicializar LLM
        llm = get_llm()
        print("✅ LLM inicializado com sucesso!\n")
    except Exception as e:
        print(f"❌ Erro ao inicializar LLM: {e}")
        return
    
    while True:
        try:
            # Receber pergunta do usuário
            pergunta = input("Faça sua pergunta: ").strip()
            
            # Verificar se quer sair
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Encerrando chat...")
                break
            
            # Verificar se pergunta não está vazia
            if not pergunta:
                print("⚠️  Por favor, digite uma pergunta válida.\n")
                continue
            
            # Buscar contexto e montar prompt
            print("\n🔍 Buscando informações...")
            prompt = search_prompt(pergunta)
            
            if not prompt:
                print("❌ Erro ao buscar informações. Tente novamente.\n")
                continue
            
            # Chamar LLM
            print("💭 Gerando resposta...\n")
            response = llm.invoke(prompt)
            
            # Extrair conteúdo da resposta
            if hasattr(response, 'content'):
                resposta = response.content
            else:
                resposta = str(response)
            
            # Exibir resposta formatada
            print("PERGUNTA:", pergunta)
            print("RESPOSTA:", resposta)
            print("\n" + "-" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando chat...")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")
            continue

if __name__ == "__main__":
    main()
```

**Ação**: Implementar função completa.

**Checkpoint**: Chat CLI funciona corretamente.

### Passo 5.3: Melhorar Integração com LangChain

**Arquivo**: `src/search.py` (melhorar)

```python
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def create_rag_chain(llm):
    """Cria chain RAG completa."""
    prompt_template = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "query"]
    )
    
    return LLMChain(
        llm=llm,
        prompt=prompt_template
    )
```

**Arquivo**: `src/chat.py` (atualizar para usar chain)

```python
from search import get_vectorstore, create_rag_chain

def main():
    # ... código anterior ...
    
    # Criar chain RAG
    chain = create_rag_chain(llm)
    vectorstore = get_vectorstore()
    
    # No loop:
    # Buscar contexto
    results = vectorstore.similarity_search_with_score(pergunta, k=10)
    context = "\n\n".join([doc.page_content for doc, _ in results])
    
    # Executar chain
    response = chain.invoke({"context": context, "query": pergunta})
    resposta = response["text"]
```

**Checkpoint**: Integração com LangChain completa.

## 🧪 Fase 6: Testes e Validação

### Passo 6.1: Testar Ingestão Completa

```bash
# 1. Limpar dados anteriores (se necessário)
docker compose down -v
docker compose up -d

# 2. Executar ingestão
python src/ingest.py

# 3. Verificar logs e output
# Deve mostrar: PDF carregado, chunks criados, documentos armazenados
```

**Checkpoint**: Ingestão completa sem erros.

### Passo 6.2: Testar Busca e Respostas

```bash
# Executar chat
python src/chat.py

# Testar perguntas:
# 1. Pergunta que deve estar no PDF
# 2. Pergunta que não deve estar no PDF
# 3. Pergunta que requer opinião
# 4. Pergunta sobre conhecimento geral
```

**Checkpoint**: Todas as respostas são apropriadas.

### Passo 6.3: Validar Comportamento Esperado

**Cenários de Teste:**

1. **Pergunta com resposta no contexto**
   - Input: "Qual o faturamento da empresa?"
   - Output esperado: Resposta baseada no PDF

2. **Pergunta sem resposta no contexto**
   - Input: "Quantos clientes temos em 2024?"
   - Output esperado: "Não tenho informações necessárias..."

3. **Pergunta que requer opinião**
   - Input: "Você acha isso bom ou ruim?"
   - Output esperado: "Não tenho informações necessárias..."

4. **Pergunta sobre conhecimento geral**
   - Input: "Qual é a capital da França?"
   - Output esperado: "Não tenho informações necessárias..."

**Checkpoint**: Todos os cenários funcionam corretamente.

## 🔧 Fase 7: Melhorias e Ajustes

### Passo 7.1: Adicionar Tratamento de Erros Robusto

- Validar entrada do usuário
- Tratar erros de conexão
- Tratar erros de API
- Mensagens de erro amigáveis

### Passo 7.2: Adicionar Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Passo 7.3: Melhorar UX do CLI

- Indicadores de progresso
- Formatação melhorada
- Cores (opcional com `colorama`)
- Histórico de perguntas (opcional)

### Passo 7.4: Validação de Dados

- Verificar se PDF existe antes de processar
- Verificar se banco está acessível
- Verificar API keys antes de usar
- Validar formato do PDF

## 📊 Checklist Final de Implementação

### Configuração
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Arquivo `.env` configurado
- [ ] PostgreSQL rodando
- [ ] pgVector instalado

### Ingestão (`src/ingest.py`)
- [ ] Carregamento de PDF implementado
- [ ] Divisão em chunks (1000 chars, 150 overlap)
- [ ] Geração de embeddings
- [ ] Armazenamento no PostgreSQL
- [ ] Função `ingest_pdf()` completa

### Busca (`src/search.py`)
- [ ] Template de prompt definido
- [ ] Função `get_vectorstore()` implementada
- [ ] Função `search_prompt()` implementada
- [ ] Busca vetorial (k=10) funcionando

### Chat (`src/chat.py`)
- [ ] LLM configurado
- [ ] Loop de chat implementado
- [ ] Integração com busca
- [ ] Formatação de resposta
- [ ] Tratamento de saída

### Validação
- [ ] Ingestão completa funciona
- [ ] Chat funciona corretamente
- [ ] Respostas baseadas no contexto
- [ ] Respostas para perguntas fora do contexto
- [ ] Tratamento de erros

## 🚀 Ordem de Execução Final

```bash
# 1. Configurar ambiente
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar variáveis
cp .env.example .env
# Editar .env

# 3. Iniciar banco
docker compose up -d

# 4. Ingerir PDF
python src/ingest.py

# 5. Executar chat
python src/chat.py
```

## 📝 Notas Importantes

1. **API Keys**: Nunca commitar arquivo `.env` no Git
2. **Custos**: Cada ingestão e pergunta gera custos na API
3. **Performance**: Ingestão pode ser lenta para PDFs grandes
4. **Embeddings**: Use o mesmo modelo de embeddings na ingestão e busca
5. **Banco de Dados**: Dados persistem no volume Docker

## 🐛 Troubleshooting Rápido

| Problema               | Solução                                      |
| ---------------------- | -------------------------------------------- |
| PDF não encontrado     | Verificar `PDF_PATH` no `.env`               |
| Erro de conexão        | Verificar `docker compose ps`                |
| API Key inválida       | Verificar `.env` e créditos na conta         |
| Embeddings não gerados | Verificar API key e conexão                  |
| Respostas incorretas   | Verificar se ingestão foi feita corretamente |

## 📚 Referências

- Arquitetura: `docs/architecture.md`
- Estratégia de Dados: `docs/data-strategy.md`
- Prompt Engineering: `docs/prompt-engineering.md`
- Deployment: `docs/deployment.md`
- Requisitos: `docs/requirements.md`

---

**Status**: 📋 Plano de ação pronto para implementação

**Próximo passo**: Começar pela Fase 1 e seguir sequencialmente cada passo.

