import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

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


def get_embeddings(provider: str = "openai"):
		"""Retorna instância de embeddings configurada (mesma da ingestão).

		Args:
				provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")

		Returns:
				Instância de embeddings configurada
		"""
		provider = provider.lower()

		if provider == "openai":
				if not os.getenv("OPENAI_API_KEY"):
						raise ValueError("OPENAI_API_KEY não encontrada no .env!")
				from langchain_openai import OpenAIEmbeddings
				return OpenAIEmbeddings()
		elif provider == "google":
				if not os.getenv("GOOGLE_API_KEY"):
						raise ValueError("GOOGLE_API_KEY não encontrada no .env!")
				from langchain_google_genai import GoogleGenerativeAIEmbeddings
				return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
		else:
				raise ValueError(f"Provider '{provider}' não suportado! Use 'openai' ou 'google'.")


def get_vectorstore(provider: str = "openai"):
	"""Retorna instância do vectorstore conectado ao banco.

	Args:
		provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")

	Returns:
		Instância do vectorstore conectado
	"""
	# Suporta DATABASE_URL ou POSTGRES_CONNECTION_STRING
	connection_string = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")

	if not connection_string:
		raise ValueError("DATABASE_URL ou POSTGRES_CONNECTION_STRING não encontrada no .env!")

	# Configurar embeddings (mesmo da ingestão)
	embeddings = get_embeddings(provider)

	# Obter nome da coleção (opcional)
	collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME") or os.getenv("PGVECTOR_COLLECTION")

	# Conectar ao vectorstore existente
	vectorstore_params = {
		"embeddings": embeddings,
		"connection": connection_string,
		"use_jsonb": True
	}

	# Adicionar collection_name se fornecido
	if collection_name:
		vectorstore_params["collection_name"] = collection_name

	vectorstore = PGVector(**vectorstore_params)

	return vectorstore


def search_prompt(question: str, provider: str = "openai"):
	"""Busca chunks relevantes e monta prompt com contexto.

	Args:
		question: Pergunta do usuário
		provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")
	"""
	if not question:
		return None

	try:
		# 1. Obter vectorstore
		vectorstore = get_vectorstore(provider)

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


def create_rag_chain(llm):
    """Cria chain RAG completa."""
    prompt_template = PromptTemplate(
			template=PROMPT_TEMPLATE,
			input_variables=["context", "query"]
    )

    return LLMChain(llm=llm, prompt=prompt_template)
