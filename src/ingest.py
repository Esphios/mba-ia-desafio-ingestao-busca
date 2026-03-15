import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"A variável de ambiente '{name}' não foi definida.")
    return value


def get_embeddings():
    provider = os.getenv("PROVIDER", "openai").strip().lower()

    if provider == "openai":
        api_key = get_required_env("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        return OpenAIEmbeddings(
            model=model,
            api_key=api_key,
        )

    if provider == "google":
        api_key = get_required_env("GOOGLE_API_KEY")
        model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key,
        )

    raise RuntimeError("PROVIDER inválido. Use 'openai' ou 'google'.")


def main():
    load_dotenv()

    pgvector_url = get_required_env("PGVECTOR_URL")
    collection_name = get_required_env("PGVECTOR_COLLECTION")

    project_root = Path(__file__).resolve().parent.parent
    pdf_path = project_root / "document.pdf"

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado em: {pdf_path}")

    print(f"[INFO] Lendo PDF: {pdf_path}")
    try:
        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()
    except Exception as exc:
        raise RuntimeError(f"Falha ao ler o PDF '{pdf_path.name}'.") from exc

    print(f"[INFO] Páginas carregadas: {len(docs)}")

    docs_with_text = [doc for doc in docs if doc.page_content and doc.page_content.strip()]
    if not docs_with_text:
        raise RuntimeError("O PDF não possui texto legível para ingestão.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    splits = splitter.split_documents(docs_with_text)
    splits = [doc for doc in splits if doc.page_content and doc.page_content.strip()]

    if not splits:
        raise RuntimeError("Nenhum chunk com texto foi gerado a partir do PDF.")

    print(f"[INFO] Chunks gerados: {len(splits)}")

    enriched_docs = []
    ids = []

    for index, doc in enumerate(splits):
        clean_metadata = {
            key: value
            for key, value in doc.metadata.items()
            if value not in ("", None)
        }

        enriched_docs.append(
            Document(
                page_content=doc.page_content.strip(),
                metadata=clean_metadata,
            )
        )
        ids.append(f"doc-{index}")

    embeddings = get_embeddings()

    try:
        store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=pgvector_url,
            pre_delete_collection=True,
            use_jsonb=True,
        )

        print("[INFO] Gravando documentos no PGVector...")
        store.add_documents(documents=enriched_docs, ids=ids)
    except Exception as exc:
        raise RuntimeError(
            "Falha ao gravar documentos no PGVector. Verifique o banco, o pgvector e as variáveis PGVECTOR_URL e PGVECTOR_COLLECTION."
        ) from exc

    print("[OK] Ingestão concluída com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERRO] {exc}")
        raise SystemExit(1) from exc
