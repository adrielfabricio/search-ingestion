# Ingestão e Busca Semântica com LangChain e Postgres

Sistema de busca semântica (RAG) que permite consultar documentos PDF através de perguntas em linguagem natural, utilizando LangChain, PostgreSQL com pgVector e modelos de IA.

## Objetivo

- **Ingestão:** Ler um arquivo PDF e salvar suas informações em um banco de dados PostgreSQL com extensão pgVector.
- **Busca:** Permitir que o usuário faça perguntas via linha de comando (CLI) e receba respostas baseadas apenas no conteúdo do PDF.

## Quick Start

### Pré-requisitos

- Python 3.9+
- Docker e Docker Compose
- OpenAI API Key (ou Google Gemini API Key)

### Instalação

1. **Clone o repositório e entre no diretório:**
```bash
cd search-ingestion
```

2. **Crie e ative um ambiente virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

**Arquivo `.env` deve conter:**
```env
OPENAI_API_KEY=sk-...
# OU
GOOGLE_API_KEY=...
PDF_PATH=document.pdf
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/rag
```

### Execução

1. **Inicie o banco de dados PostgreSQL:**
```bash
docker compose up -d
```

2. **Execute a ingestão do PDF:**
```bash
python src/ingest.py
```

3. **Inicie o chat:**
```bash
python src/chat.py
```

## Exemplo de Uso

```bash
Faça sua pergunta (digite 'sair' para encerrar):
> Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhões de reais.

> Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

> sair
Encerrando chat...
```

## Arquitetura

O sistema utiliza uma arquitetura RAG (Retrieval Augmented Generation):

1. **Ingestão**: PDF → Chunks → Embeddings → PostgreSQL + pgVector
2. **Busca**: Pergunta → Embedding → Busca Vetorial → Contexto → LLM → Resposta

Para mais detalhes, consulte a [documentação de arquitetura](docs/architecture.md).

## Documentação

Documentação completa disponível em `docs/`:

- **[architecture.md](docs/architecture.md)**: Arquitetura do sistema e fluxo de dados
- **[data-strategy.md](docs/data-strategy.md)**: Estratégia de chunking, embeddings e busca
- **[prompt-engineering.md](docs/prompt-engineering.md)**: Design do prompt e estratégia RAG
- **[deployment.md](docs/deployment.md)**: Configuração e deployment detalhado
- **[requirements.md](docs/requirements.md)**: Especificações técnicas do projeto
- **[action-plan.md](docs/action-plan.md)**: Plano de ação passo a passo para implementação

## Tecnologias

- **Python 3.9+**: Linguagem de programação
- **LangChain**: Framework para aplicações LLM
- **PostgreSQL 17**: Banco de dados relacional
- **pgVector**: Extensão para busca vetorial
- **OpenAI / Google Gemini**: Modelos de embeddings e LLM
- **Docker**: Containerização do banco de dados

## Estrutura do Projeto

```bash
.
├── docker-compose.yml         # Configuração do PostgreSQL
├── requirements.txt           # Dependências Python
├── pytest.ini                 # Configuração do pytest
├── .env.example               # Template de variáveis de ambiente
├── .env                       # Variáveis de ambiente (criar)
├── document.pdf               # PDF para ingestão
├── src/
│   ├── ingest.py              # Script de ingestão do PDF
│   ├── search.py              # Módulo de busca e prompt
│   └── chat.py                # CLI para interação com usuário
├── tests/
│   ├── __init__.py            # Package de testes
│   ├── test_ingest.py         # Testes do módulo de ingestão
│   ├── test_search.py         # Testes do módulo de busca
│   └── test_chat.py           # Testes do módulo de chat
├── docs/
│   ├── architecture.md        # Arquitetura do sistema
│   ├── data-strategy.md       # Estratégia de dados
│   ├── prompt-engineering.md  # Prompt engineering
│   ├── deployment.md          # Configuração e deploy
│   ├── requirements.md        # Especificações técnicas
│   └── action-plan.md         # Plano de ação para implementação
└── README.md                  # Este arquivo
```

## Configuração

### Chunking

- **Tamanho do chunk**: 1000 caracteres
- **Overlap**: 150 caracteres
- **Método**: RecursiveCharacterTextSplitter

### Busca

- **Número de chunks (k)**: 10
- **Método**: Similarity search com distância cosseno
- **Score threshold**: Configurável

### Prompt

O sistema utiliza um prompt template que:
- Fornece contexto dos chunks relevantes
- Define regras claras de resposta
- Inclui exemplos de perguntas fora do contexto
- Garante respostas baseadas apenas no documento

Veja detalhes em [prompt-engineering.md](docs/prompt-engineering.md).

## Troubleshooting

### PostgreSQL não inicia

```bash
# Verificar se porta 5432 está livre
lsof -i :5432

# Parar e reiniciar
docker compose down
docker compose up -d
```

### Erro de conexão

- Verifique se PostgreSQL está rodando: `docker compose ps`
- Verifique a string de conexão no `.env`
- Verifique as credenciais (usuário, senha, banco)

### Erro de API Key

- Verifique se `.env` está configurado corretamente
- Verifique se a API key é válida
- Verifique se tem créditos na conta

### PDF não encontrado

- Verifique se `document.pdf` existe na raiz do projeto
- Verifique o caminho em `PDF_PATH` no `.env`
- Use caminho absoluto se necessário

Para mais informações, consulte [deployment.md](docs/deployment.md).

## Comandos Úteis

```bash
# Parar serviços
docker compose down

# Ver logs
docker compose logs -f

# Reiniciar serviços
docker compose restart

# Verificar dados no banco
docker compose exec postgres psql -U postgres -d rag
```

## Testes

### Testes Unitários

O projeto inclui testes unitários para validar os componentes principais:

```bash
# Executar todos os testes
python -m pytest tests/

# Executar testes com output detalhado
python -m pytest tests/ -v

# Executar testes de um módulo específico
python -m pytest tests/test_ingest.py -v
python -m pytest tests/test_search.py -v
python -m pytest tests/test_chat.py -v

# Executar testes com cobertura (requer pytest-cov)
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

### Testes de Integração

Para testar o sistema completo:

1. Certifique-se de que o PDF contém informações relevantes
2. Execute a ingestão e verifique se não há erros:
   ```bash
   python src/ingest.py
   ```
3. Execute o chat e teste perguntas:
   ```bash
   python src/chat.py
   ```
4. Teste perguntas que devem estar no documento
5. Teste perguntas que não devem estar no documento
6. Verifique se as respostas são apropriadas

### Cenários de Teste

- Pergunta com resposta no contexto → Deve retornar resposta baseada no PDF
- Pergunta sem resposta no contexto → Deve retornar "Não tenho informações necessárias..."
- Pergunta que requer opinião → Deve retornar "Não tenho informações necessárias..."
- Pergunta sobre conhecimento geral → Deve retornar "Não tenho informações necessárias..."

## Licença

Este projeto é parte de um curso/desafio educacional.

## Referências

- [LangChain Documentation](https://python.langchain.com/)
- [pgVector Documentation](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
