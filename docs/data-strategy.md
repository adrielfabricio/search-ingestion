# Estratégia de Dados - Ingestão e Busca Semântica

## Visão Geral

Este documento descreve a estratégia de processamento, armazenamento e recuperação de dados para o sistema de busca semântica.

## Pipeline de Ingestão

### 1. Carregamento do PDF

**Ferramenta**: `PyPDFLoader` (LangChain)

**Processo:**
- Lê arquivo PDF do sistema de arquivos
- Extrai texto de todas as páginas
- Converte em objetos `Document` do LangChain
- Cada página vira um documento inicial

**Exemplo:**
```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("document.pdf")
documents = loader.load()
```

### 2. Divisão em Chunks (Text Splitting)

**Ferramenta**: `RecursiveCharacterTextSplitter` (LangChain)

**Parâmetros:**
- **chunk_size**: 1000 caracteres
- **chunk_overlap**: 150 caracteres
- **separators**: Padrão do LangChain (recursivo)

**Por que 1000 caracteres?**
- Tamanho suficiente para contexto completo de informações
- Não excede limites de tokens do modelo de embedding
- Balance entre precisão e granularidade

**Por que 150 caracteres de overlap?**
- Evita perda de informação nas bordas dos chunks
- Garante que palavras/conceitos não sejam cortados ao meio
- Melhora a recuperação de informações que aparecem no final de um chunk e início do próximo

**Processo:**
1. Tenta dividir por parágrafos
2. Se não possível, divide por sentenças
3. Se ainda não possível, divide por palavras
4. Se ainda não possível, divide por caracteres

**Exemplo:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150
)
chunks = text_splitter.split_documents(documents)
```

### 3. Geração de Embeddings

**Modelos Disponíveis:**
- **OpenAI**: `text-embedding-3-small` ou `text-embedding-3-large`
- **Google Gemini**: `text-embedding-004`

**Processo:**
- Cada chunk é convertido em um vetor numérico
- Dimensão típica: 1536 (OpenAI) ou 768 (Gemini)
- Embeddings capturam semântica do texto

**Exemplo:**
```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])
```

**Características:**
- Embeddings são normalizados (vetores unitários)
- Textos semanticamente similares têm embeddings próximos
- Usa distância cosseno para comparação

### 4. Armazenamento no PostgreSQL + pgVector

**Ferramenta**: `PGVector` (LangChain)

**Estrutura da Tabela:**
- Criada automaticamente pelo LangChain
- Contém:
  - `id`: UUID único
  - `embedding`: Vetor de embedding (tipo `vector`)
  - `document`: Texto original do chunk
  - `metadata`: JSON com metadados opcionais

**Índices:**
- Índice HNSW (Hierarchical Navigable Small World) para busca rápida
- Otimizado para busca por similaridade vetorial

**Conexão:**
- Usa `psycopg` para conexão com PostgreSQL
- Pool de conexões para performance
- Configuração via string de conexão

**Exemplo:**
```python
from langchain_postgres import PGVector

vectorstore = PGVector(
    embeddings=embeddings,
    connection=connection_string,
    use_jsonb=True
)
vectorstore.add_documents(chunks)
```

## Estratégia de Busca

### 1. Vetorização da Pergunta

**Processo:**
- Usa o mesmo modelo de embeddings da ingestão
- Converte pergunta do usuário em vetor
- Mantém consistência com embeddings armazenados

### 2. Busca por Similaridade

**Método**: `similarity_search_with_score()`

**Parâmetros:**
- **query**: Texto da pergunta
- **k**: 10 (número de chunks a retornar)
- **score_threshold**: Opcional (filtrar por relevância mínima)

**Algoritmo:**
- Calcula distância cosseno entre embedding da pergunta e todos os embeddings armazenados
- Retorna os k chunks com menor distância (maior similaridade)
- Score indica nível de similaridade (0 = idêntico, 1 = completamente diferente)

**Exemplo:**
```python
results = vectorstore.similarity_search_with_score(
    query=pergunta,
    k=10
)
```

### 3. Montagem do Contexto

**Processo:**
- Combina os 10 chunks retornados
- Ordena por score (mais relevantes primeiro)
- Formata para incluir no prompt

**Formato:**
```
CONTEXTO:
[Chunk 1]
[Chunk 2]
...
[Chunk 10]
```

## Modelo de Dados

### Schema do Banco de Dados

```sql
-- Tabela criada automaticamente pelo LangChain
CREATE TABLE langchain_pg_embedding (
    id UUID PRIMARY KEY,
    embedding vector(1536),  -- Dimensão varia por modelo
    document TEXT,
    metadata JSONB,
    -- Índices adicionais criados automaticamente
);
```

### Metadados Opcionais

Estrutura sugerida para metadados:
```json
{
    "source": "document.pdf",
    "page": 1,
    "chunk_index": 0,
    "total_chunks": 150
}
```

## Estratégia de Chunking Detalhada

### RecursiveCharacterTextSplitter

**Separadores (em ordem de prioridade):**
1. `\n\n` - Parágrafos
2. `\n` - Linhas
3. ` ` - Espaços
4. `""` - Caracteres vazios

**Vantagens:**
- Preserva estrutura do documento
- Respeita limites naturais de texto
- Mantém contexto semântico

### Exemplo de Chunking

**Texto Original:**
```
A Empresa SuperTechIABrazil foi fundada em 2020. 
O faturamento em 2023 foi de 10 milhões de reais.
A empresa possui 50 funcionários.
```

**Chunks (1000 chars, 150 overlap):**
- Chunk 1: "A Empresa SuperTechIABrazil foi fundada em 2020. O faturamento em 2023 foi de 10 milhões de reais..."
- Chunk 2: "...faturamento em 2023 foi de 10 milhões de reais. A empresa possui 50 funcionários..."

## Qualidade de Dados

### Validação na Ingestão

- Verificar se PDF foi carregado corretamente
- Validar que chunks não estão vazios
- Confirmar que embeddings foram gerados
- Verificar conexão com banco de dados

### Tratamento de Erros

- PDF corrompido: Retornar erro claro
- Falha na geração de embedding: Retry com backoff
- Erro de conexão: Verificar banco e credenciais
- Chunks muito grandes: Ajustar tamanho

## Performance e Otimização

### Ingestão

- **Processamento**: Pode ser lento para PDFs grandes
- **Otimização**: Processar em lotes (batch)
- **Paralelização**: Possível para geração de embeddings

### Busca

- **Índices**: pgVector cria índices automaticamente
- **Cache**: Embeddings podem ser cacheados (não implementado)
- **Limite**: k=10 é um bom balance

### Escalabilidade

- **Múltiplos PDFs**: Cada um pode ser ingerido separadamente
- **Volume**: PostgreSQL pode lidar com milhões de chunks
- **Concorrência**: Buscas podem ser paralelas

## Limitações e Considerações

### Limitações

- **Chunking**: Informações podem ser cortadas
- **Contexto**: Limitado aos 10 chunks retornados
- **Multilíngue**: Funciona melhor com texto em português/inglês
- **Formatação**: PDFs com imagens/tabelas podem perder informação

### Melhorias Futuras

- Adicionar metadados mais ricos
- Implementar re-ranking de resultados
- Suportar múltiplos documentos
- Adicionar filtros por metadados
- Implementar cache de embeddings

## Backup e Recuperação

### Estratégia Atual

- Dados armazenados no volume Docker (`postgres_data`)
- Backup manual necessário

### Recomendações

- Backup regular do volume PostgreSQL
- Exportar dados periodicamente
- Versionar schema do banco

