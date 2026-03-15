import os
import unicodedata
from typing import Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector


OUT_OF_CONTEXT_RESPONSE = "Não tenho informações necessárias para responder sua pergunta."

PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

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
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

GROUNDING_PROMPT_TEMPLATE = """CONTEXTO:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

RESPOSTA PROPOSTA:
{resposta}

REGRAS:
- Responda somente com SIM ou NAO.
- Responda SIM apenas se a RESPOSTA PROPOSTA estiver explicitamente sustentada pelo CONTEXTO.
- Considere válidas reformulações fiéis e traduções do CONTEXTO.
- Responda NAO se a resposta usar informação ausente, inferida, opinativa ou externa ao CONTEXTO.
"""


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"A variável de ambiente '{name}' não foi definida.")
    return value


def get_provider() -> str:
    return os.getenv("PROVIDER", "openai").strip().lower()


def get_embeddings():
    provider = get_provider()

    if provider == "openai":
        return OpenAIEmbeddings(
            model=os.getenv("OPENAI_MODEL", "text-embedding-3-small"),
            api_key=get_required_env("OPENAI_API_KEY"),
        )

    if provider == "google":
        return GoogleGenerativeAIEmbeddings(
            model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001"),
            google_api_key=get_required_env("GOOGLE_API_KEY"),
        )

    raise RuntimeError("PROVIDER inválido. Use 'openai' ou 'google'.")


def get_llm():
    provider = get_provider()

    if provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5-nano"),
            api_key=get_required_env("OPENAI_API_KEY"),
            temperature=0,
        )

    if provider == "google":
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_CHAT_MODEL", "gemini-2.5-flash-lite"),
            google_api_key=get_required_env("GOOGLE_API_KEY"),
            temperature=0,
        )

    raise RuntimeError("PROVIDER inválido. Use 'openai' ou 'google'.")


def get_vector_store() -> PGVector:
    load_dotenv()
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=get_required_env("PGVECTOR_COLLECTION"),
        connection=get_required_env("PGVECTOR_URL"),
        use_jsonb=True,
    )


def search_documents(query: str, k: int = 10) -> list[tuple[Document, float]]:
    if not query.strip():
        raise ValueError("A pergunta não pode ser vazia.")

    try:
        store = get_vector_store()
        return store.similarity_search_with_score(query, k=k)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "Falha ao consultar o PGVector. Verifique se o banco está ativo e se PGVECTOR_URL está correto."
        ) from exc


def build_context(results: list[tuple[Document, float]]) -> str:
    if not results:
        return ""

    context_parts = []

    for index, (doc, score) in enumerate(results, start=1):
        content = doc.page_content.strip()
        if not content:
            continue

        page = doc.metadata.get("page", "desconhecida")
        source = doc.metadata.get("source", "document.pdf")
        context_parts.append(
            f"[Trecho {index} | página={page} | source={source} | score={score:.4f}]\n{content}"
        )

    return "\n\n".join(context_parts)


def extract_text_from_response(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str) and item.strip():
                text_parts.append(item.strip())
                continue

            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
                    continue

            text = getattr(item, "text", None)
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

        return "\n".join(text_parts).strip()

    return str(content).strip()


def normalize_answer_text(answer_text: str) -> str:
    cleaned_text = answer_text.strip()
    normalized_text = cleaned_text.strip("\"' ").strip()

    if normalized_text == OUT_OF_CONTEXT_RESPONSE:
        return OUT_OF_CONTEXT_RESPONSE

    return cleaned_text


def normalize_for_comparison(text: str) -> str:
    return " ".join(text.lower().split())


def normalize_yes_no(text: str) -> str:
    normalized_text = unicodedata.normalize("NFKD", text)
    ascii_text = normalized_text.encode("ascii", "ignore").decode("ascii")
    return normalize_for_comparison(ascii_text)


def is_answer_grounded_in_context(
    question: str,
    answer_text: str,
    context: str,
    llm: Any,
) -> bool:
    normalized_context = normalize_for_comparison(context)
    normalized_answer = normalize_for_comparison(answer_text.strip("\"' "))

    if not normalized_context or not normalized_answer:
        return False

    if normalized_answer in normalized_context:
        return True

    grounding_prompt = GROUNDING_PROMPT_TEMPLATE.format(
        contexto=context,
        pergunta=question,
        resposta=answer_text,
    )

    try:
        grounding_response = llm.invoke(grounding_prompt)
    except Exception as exc:
        raise RuntimeError(
            "Falha ao validar se a resposta está sustentada pelo contexto recuperado."
        ) from exc

    decision = normalize_yes_no(extract_text_from_response(grounding_response))
    return decision.startswith("sim")


def answer_question(question: str) -> dict[str, Any]:
    load_dotenv()

    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("A pergunta não pode ser vazia.")

    results = search_documents(cleaned_question, k=10)
    context = build_context(results)

    if not context:
        return {
            "question": cleaned_question,
            "answer": OUT_OF_CONTEXT_RESPONSE,
            "results": results,
            "context": context,
        }

    prompt = PROMPT_TEMPLATE.format(
        contexto=context,
        pergunta=cleaned_question,
    )

    llm = get_llm()

    try:
        response = llm.invoke(prompt)
    except Exception as exc:
        raise RuntimeError(
            "Falha ao chamar o modelo de linguagem. Verifique a chave de API e o provedor configurado."
        ) from exc

    answer_text = normalize_answer_text(extract_text_from_response(response))
    if not answer_text:
        answer_text = OUT_OF_CONTEXT_RESPONSE
    elif answer_text != OUT_OF_CONTEXT_RESPONSE and not is_answer_grounded_in_context(
        cleaned_question,
        answer_text,
        context,
        llm,
    ):
        answer_text = OUT_OF_CONTEXT_RESPONSE

    return {
        "question": cleaned_question,
        "answer": answer_text,
        "results": results,
        "context": context,
    }
