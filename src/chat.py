try:
    from .search import answer_question
except ImportError:
    from search import answer_question


def main():
    print("Chat de busca semântica iniciado.")
    print("Digite sua pergunta ou 'sair' para encerrar.\n")

    while True:
        try:
            question = input("Faça sua pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando chat.")
            break

        if not question:
            print("Digite uma pergunta válida.\n")
            continue

        if question.lower() in {"sair", "exit", "quit"}:
            print("Encerrando chat.")
            break

        try:
            result = answer_question(question)

            print()
            print(f"PERGUNTA: {result['question']}")
            print(f"RESPOSTA: {result['answer']}")
            print("-" * 60)
            print()

        except Exception as exc:
            print(f"Erro ao processar a pergunta: {exc}\n")


if __name__ == "__main__":
    main()
