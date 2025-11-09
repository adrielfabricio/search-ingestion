# Prompt Engineering - Sistema de Busca Semântica

## Visão Geral

Este documento descreve a estratégia de prompt engineering utilizada no sistema RAG (Retrieval Augmented Generation) para garantir respostas precisas baseadas apenas no contexto fornecido.

## Template de Prompt

### Estrutura Completa

```markdown
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
```

## Componentes do Prompt

### 1. Seção CONTEXTO

**Propósito**: Fornecer informações relevantes do documento PDF

**Conteúdo**: 
- Os 10 chunks mais relevantes retornados pela busca vetorial
- Ordenados por relevância (score)
- Separados por quebras de linha

**Formato**:
```
CONTEXTO:
[Chunk 1 - Texto completo do primeiro chunk]
[Chunk 2 - Texto completo do segundo chunk]
...
[Chunk 10 - Texto completo do décimo chunk]
```

### 2. Seção REGRAS

**Propósito**: Direcionar o comportamento do LLM

**Regras Críticas**:
1. **Resposta baseada apenas no contexto**: Previne alucinações
2. **Resposta padrão para informações ausentes**: Garante consistência
3. **Proibição de conhecimento externo**: Mantém fidelidade ao documento
4. **Proibição de opiniões**: Mantém objetividade

### 3. Seção EXEMPLOS (Few-Shot Learning)

**Propósito**: Demonstrar o comportamento esperado

**Técnica**: Few-shot learning com exemplos negativos

**Exemplos Incluídos**:
- Pergunta sobre conhecimento geral (capital da França)
- Pergunta sobre dados não presentes (clientes em 2024)
- Pergunta solicitando opinião (bom ou ruim)

**Efeito**: 
- Ensina o modelo a reconhecer perguntas fora do contexto
- Estabelece padrão de resposta para casos sem informação

### 4. Seção PERGUNTA DO USUÁRIO

**Propósito**: Inserir a pergunta real do usuário

**Formato**: 
```
PERGUNTA DO USUÁRIO:
{query}
```

## Princípios de Design

### 1. Clareza e Explicitude

- Instruções diretas e sem ambiguidade
- Linguagem imperativa ("Responda somente", "Nunca invente")
- Evita interpretações múltiplas

### 2. Exemplos Negativos

- Mostra o que NÃO fazer
- Demonstra comportamento correto em situações de falha
- Mais eficaz que apenas regras abstratas

### 3. Estrutura Hierárquica

- Contexto primeiro (informação)
- Regras depois (comportamento)
- Exemplos em seguida (demonstração)
- Pergunta por último (ação)

### 4. Resposta Padronizada

- Texto fixo para respostas sem informação
- Facilita detecção de casos sem resposta
- Melhora experiência do usuário

## Implementação no Código

### Função de Montagem do Prompt

```python
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

def format_prompt(context: str, query: str) -> str:
    return PROMPT_TEMPLATE.format(context=context, query=query)
```

### Integração com LangChain

```python
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "query"]
)
```

## Cenários de Uso

### Cenário 1: Pergunta com Resposta no Contexto

**Pergunta**: "Qual o faturamento da Empresa SuperTechIABrazil?"

**Contexto**: "O faturamento em 2023 foi de 10 milhões de reais."

**Resposta Esperada**: "O faturamento foi de 10 milhões de reais."

### Cenário 2: Pergunta sem Resposta no Contexto

**Pergunta**: "Quantos clientes temos em 2024?"

**Contexto**: [Não contém informação sobre clientes em 2024]

**Resposta Esperada**: "Não tenho informações necessárias para responder sua pergunta."

### Cenário 3: Pergunta que Requer Opinião

**Pergunta**: "Você acha isso bom ou ruim?"

**Resposta Esperada**: "Não tenho informações necessárias para responder sua pergunta."

### Cenário 4: Pergunta com Conhecimento Externo

**Pergunta**: "Qual é a capital da França?"

**Resposta Esperada**: "Não tenho informações necessárias para responder sua pergunta."

## Configurações do LLM

### Parâmetros Recomendados

**OpenAI:**
- `temperature`: 0.0 (determinístico, focado)
- `max_tokens`: 500 (respostas concisas)
- `model`: `gpt-4` ou `gpt-3.5-turbo`

**Google Gemini:**
- `temperature`: 0.0
- `max_output_tokens`: 500
- `model`: `gemini-pro`

### Justificativa

- **Temperature 0.0**: Garante respostas determinísticas e focadas
- **Max tokens 500**: Evita respostas muito longas
- **Modelos maiores**: Melhor compreensão de instruções complexas

## Melhorias Futuras

### 1. Prompt Dinâmico

- Ajustar prompt baseado no tipo de pergunta
- Adicionar instruções específicas por domínio

### 2. Contexto Mais Rico

- Incluir metadados (página, fonte)
- Formatação melhorada do contexto

### 3. Validação de Resposta

- Detectar quando resposta não está no contexto
- Re-ranking automático de respostas

### 4. Multi-turn Conversation

- Manter histórico de conversa
- Referências a perguntas anteriores

## Troubleshooting

### Problema: LLM inventa informações

**Solução**: 
- Reforçar regras no prompt
- Adicionar mais exemplos negativos
- Reduzir temperature

### Problema: Respostas muito longas

**Solução**:
- Adicionar instrução "Seja conciso"
- Reduzir max_tokens
- Limitar tamanho do contexto

### Problema: LLM não segue exemplos

**Solução**:
- Verificar se exemplos estão bem formatados
- Aumentar número de exemplos
- Usar modelo mais capaz

## Métricas de Avaliação

### Métricas Qualitativas

- Precisão: Resposta está correta?
- Relevância: Resposta responde à pergunta?
- Fidelidade: Resposta está no contexto?

### Métricas Quantitativas

- Taxa de "Não tenho informações" (deve ser alta quando apropriado)
- Tempo de resposta
- Custo por requisição

## Referências

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [LangChain Prompt Templates](https://python.langchain.com/docs/modules/model_io/prompts/)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

