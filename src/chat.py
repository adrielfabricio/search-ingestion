import os
from dotenv import load_dotenv
from search import get_vectorstore, create_rag_chain

load_dotenv()


def get_llm(provider: str = "openai"):
	"""Retorna instância do LLM configurado.

	Args:
		provider: Provedor de IA a ser usado. Opções: "openai" ou "google" (padrão: "openai")

	Returns:
		Instância do LLM configurado
	"""
	provider = provider.lower()

	if provider == "openai":
		if not os.getenv("OPENAI_API_KEY"):
			raise ValueError("OPENAI_API_KEY não encontrada no .env!")
		print("🔑 Usando OpenAI LLM")
		from langchain_openai import ChatOpenAI
		return ChatOpenAI(
			model="gpt-5-nano",
			temperature=0.0,
			max_tokens=500
		)
	elif provider == "google":
		if not os.getenv("GOOGLE_API_KEY"):
			raise ValueError("GOOGLE_API_KEY não encontrada no .env!")
		print("🔑 Usando Google Gemini LLM")
		from langchain_google_genai import ChatGoogleGenerativeAI
		return ChatGoogleGenerativeAI(
			model="gemini-2.5-flash-lite",
			temperature=0.0,
			max_output_tokens=500
		)
	else:
		raise ValueError(f"Provider '{provider}' não suportado! Use 'openai' ou 'google'.")


def main():
	"""Função principal do chat CLI."""
	print("🤖 Chat de Busca Semântica")
	print("=" * 50)
	print("Digite 'sair' para encerrar\n")

	try:
		# Inicializar LLM
		llm = get_llm()
		print("✅ LLM inicializado com sucesso!\n")

		# Criar chain RAG
		chain = create_rag_chain(llm)
		vectorstore = get_vectorstore()
		print("✅ Vectorstore conectado com sucesso!\n")

	except Exception as e:
		print(f"❌ Erro ao inicializar: {e}")
		return

	while True:
		try:
			# Receber pergunta do usuário
			query = input("Faça sua pergunta: ").strip()

			# Verificar se quer sair
			if query.lower() in ['sair', 'exit', 'quit']:
				print("\n👋 Encerrando chat...")
				break

			# Verificar se pergunta não está vazia
			if not query:
				print("⚠️  Por favor, digite uma pergunta válida.\n")
				continue

			# Buscar contexto
			print("\n🔍 Buscando informações...")
			try:
				results = vectorstore.similarity_search_with_score(query, k=10)
				context = "\n\n".join([doc.page_content for doc, _ in results])
			except Exception as e:
				print(f"❌ Erro ao buscar informações: {e}\n")
				continue

			# Executar chain RAG
			print("💭 Gerando resposta...\n")
			try:
				response = chain.invoke({"context": context, "query": query})
				response_text = response["text"]
			except Exception as e:
				print(f"❌ Erro ao gerar resposta: {e}\n")
				continue

			# Exibir resposta formatada
			print("PERGUNTA:", query)
			print("RESPOSTA:", response_text)
			print("\n" + "-" * 50 + "\n")

		except KeyboardInterrupt:
			print("\n\n👋 Encerrando chat...")
			break
		except Exception as e:
			print(f"\n❌ Erro: {e}\n")
			continue


if __name__ == "__main__":
	main()
