# Configuração e Deployment

## Visão Geral

Este documento descreve como configurar e executar o sistema de ingestão e busca semântica.

## Pré-requisitos

### Software Necessário

- **Python 3.9+**: Linguagem de programação
- **Docker**: Versão 20.10+
- **Docker Compose**: Versão 2.0+
- **Git**: Para clonar o repositório (opcional)

### Contas Necessárias

- **OpenAI API Key**: Para embeddings e LLM (alternativa: Google Gemini)
- Acesso à internet para baixar dependências e modelos

## Estrutura do Projeto

```
.
├── docker-compose.yml       # Configuração do PostgreSQL
├── requirements.txt         # Dependências Python
├── .env.example            # Template de variáveis de ambiente
├── .env                    # Variáveis de ambiente (criar)
├── document.pdf            # PDF para ingestão
├── src/
│   ├── ingest.py          # Script de ingestão
│   ├── search.py          # Módulo de busca
│   └── chat.py            # CLI de chat
└── docs/
    └── *.md               # Documentação
```

## Configuração Inicial

### 1. Clone/Download do Projeto

```bash
# Se usando Git
git clone <repository-url>
cd search-ingestion

# Ou baixe e extraia o projeto
```

### 2. Criar Ambiente Virtual Python

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env com suas credenciais
nano .env  # ou use seu editor preferido
```

**Arquivo `.env` deve conter:**

```env
# OpenAI (para embeddings e LLM)
OPENAI_API_KEY=sk-...

# OU Google Gemini (alternativa)
GOOGLE_API_KEY=...

# Caminho do PDF (opcional, padrão: document.pdf)
PDF_PATH=document.pdf

# Configurações do Banco de Dados
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/rag
```

### 5. Criar Arquivo `.env.example` (se não existir)

```bash
# .env.example
OPENAI_API_KEY=your_openai_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
PDF_PATH=document.pdf
POSTGRES_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/rag
```

## Execução do Sistema

### Passo 1: Iniciar PostgreSQL

```bash
# Subir banco de dados e criar extensão pgVector
docker compose up -d

# Verificar se está rodando
docker compose ps

# Ver logs (opcional)
docker compose logs -f postgres
```

**O que acontece:**
- Postgres inicia na porta 5432
- Extensão pgVector é criada automaticamente
- Banco de dados `rag` é criado
- Volume persistente é criado para dados

### Passo 2: Ingerir PDF

```bash
# Executar ingestão
python src/ingest.py
```

**O que acontece:**
- PDF é carregado
- Texto é dividido em chunks
- Embeddings são gerados
- Dados são salvos no PostgreSQL

**Saída esperada:**
```
Carregando PDF...
Dividindo em chunks...
Gerando embeddings...
Salvando no banco de dados...
Ingestão concluída! X chunks processados.
```

### Passo 3: Executar Chat

```bash
# Iniciar interface de chat
python src/chat.py
```

**Interface:**
```
Faça sua pergunta (digite 'sair' para encerrar):
> Qual o faturamento da empresa?
RESPOSTA: O faturamento foi de 10 milhões de reais.

> Quantos clientes temos?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

> sair
Encerrando chat...
```

## Configuração do Docker Compose

### Estrutura do `docker-compose.yml`

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    container_name: postgres_rag
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: rag
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d rag"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  bootstrap_vector_ext:
    image: pgvector/pgvector:pg17
    depends_on:
      postgres:
        condition: service_healthy
    entrypoint: ["/bin/sh", "-c"]
    command: >
      PGPASSWORD=postgres
      psql "postgresql://postgres@postgres:5432/rag" -v ON_ERROR_STOP=1
      -c "CREATE EXTENSION IF NOT EXISTS vector;"
    restart: "no"

volumes:
  postgres_data:
```

### Explicação dos Serviços

1. **postgres**: Serviço principal do PostgreSQL
   - Usa imagem oficial com pgVector
   - Porta 5432 exposta
   - Healthcheck para garantir disponibilidade
   - Volume persistente para dados

2. **bootstrap_vector_ext**: Serviço de inicialização
   - Cria extensão pgVector automaticamente
   - Executa apenas uma vez
   - Aguarda postgres estar saudável

## Verificação e Troubleshooting

### Verificar PostgreSQL

```bash
# Verificar se está rodando
docker compose ps

# Verificar logs
docker compose logs postgres

# Conectar ao banco (opcional)
docker compose exec postgres psql -U postgres -d rag

# Dentro do psql, verificar extensão:
# \dx
# Deve mostrar: vector
```

### Verificar Dados Ingeridos

```bash
# Conectar ao banco
docker compose exec postgres psql -U postgres -d rag

# Verificar tabela
SELECT COUNT(*) FROM langchain_pg_embedding;

# Ver alguns chunks
SELECT LEFT(document, 100) as preview FROM langchain_pg_embedding LIMIT 5;
```

### Problemas Comuns

#### 1. PostgreSQL não inicia

```bash
# Verificar se porta 5432 está livre
lsof -i :5432

# Parar outros containers PostgreSQL
docker stop $(docker ps -q --filter ancestor=postgres)

# Limpar volumes (cuidado: apaga dados)
docker compose down -v
```

#### 2. Erro de conexão no ingest.py

- Verificar se PostgreSQL está rodando: `docker compose ps`
- Verificar string de conexão no `.env`
- Verificar credenciais (usuário, senha, banco)

#### 3. Erro de API Key

- Verificar se `.env` está configurado corretamente
- Verificar se API key é válida
- Verificar se tem créditos na conta OpenAI/Gemini

#### 4. PDF não encontrado

- Verificar se `document.pdf` existe na raiz do projeto
- Verificar caminho em `PDF_PATH` no `.env`
- Usar caminho absoluto se necessário

## Desenvolvimento

### Modo de Desenvolvimento

```bash
# Instalar dependências de desenvolvimento (se houver)
pip install -r requirements-dev.txt

# Executar testes (se houver)
pytest

# Linting
flake8 src/
black src/
```

### Estrutura de Código

```
src/
├── ingest.py          # Lógica de ingestão
├── search.py          # Lógica de busca e prompt
└── chat.py            # Interface CLI
```

## Produção (Considerações Futuras)

### Segurança

- **Nunca commitar `.env`**: Já está no `.gitignore`
- **Usar secrets management**: AWS Secrets Manager, HashiCorp Vault
- **HTTPS**: Para APIs (não aplicável ao CLI atual)
- **Autenticação**: Para APIs futuras

### Escalabilidade

- **Múltiplos workers**: Para processar múltiplos PDFs
- **Queue system**: Para ingestões assíncronas
- **Cache**: Para embeddings e respostas frequentes
- **Load balancer**: Para APIs (se migrar de CLI)

### Monitoramento

- **Logs**: Centralizar logs (ELK, CloudWatch)
- **Métricas**: Prometheus, Grafana
- **Alertas**: Para falhas e performance
- **Tracing**: Para debugging distribuído

### Backup

- **Backup do PostgreSQL**: Regular e automático
- **Backup de volumes**: Para disaster recovery
- **Versionamento**: Schema do banco versionado

## Comandos Úteis

```bash
# Parar serviços
docker compose down

# Parar e remover volumes (cuidado: apaga dados)
docker compose down -v

# Ver logs em tempo real
docker compose logs -f

# Reiniciar serviços
docker compose restart

# Rebuild containers
docker compose up -d --build

# Limpar tudo
docker compose down -v
docker system prune -a
```

## Ambiente de Produção vs Desenvolvimento

### Desenvolvimento (Atual)

- Docker Compose local
- Credenciais em `.env`
- Logs no console
- Sem autenticação
- Sem monitoramento

### Produção (Recomendado)

- Kubernetes ou ECS
- Secrets management
- Logs centralizados
- Autenticação/autorização
- Monitoramento completo
- CI/CD pipeline
- Backup automático

## Próximos Passos

1. Implementar testes automatizados
2. Adicionar validação de entrada
3. Melhorar tratamento de erros
4. Adicionar logging estruturado
5. Criar API REST (opcional)
6. Implementar autenticação (se API)
7. Adicionar monitoramento
8. Configurar CI/CD

