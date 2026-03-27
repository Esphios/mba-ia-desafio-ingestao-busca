# AGENTS.md

## Visão Geral

Este repositório implementa um desafio de ingestão e busca semântica com
LangChain, PostgreSQL e pgvector. A prioridade máxima é cumprir a especificação
do desafio sem enfraquecer as regras de contexto restrito ao PDF.

## Prioridade de Decisão

Quando houver conflito entre referências, siga esta ordem:

1. especificação do desafio;
2. estrutura atual do fluxo de ingestão e busca;
3. manter mensagens e documentação claras em pt-BR;
4. boas práticas de engenharia.

## Tecnologias Principais

| Categoria | Tecnologia | Evidência | Uso |
| --- | --- | --- | --- |
| Runtime | Python | `requirements.txt`, `src/` | CLI do projeto |
| Framework LLM | LangChain | `requirements.txt`, `src/*.py` | ingestão, busca e chat |
| Vetor store | PostgreSQL + pgvector + `langchain-postgres` | `docker-compose.yml`, `src/ingest.py`, `src/search.py` | armazenamento vetorial |
| Embeddings/LLM | OpenAI e Google GenAI | `src/ingest.py`, `src/search.py`, `.env.example` | provedores suportados |
| Parsing | `PyPDFLoader`, `RecursiveCharacterTextSplitter` | `src/ingest.py` | leitura e chunking do PDF |

## Estrutura do Repositório

- `src/ingest.py`: lê `document.pdf`, divide em chunks de 1000 com overlap de 150, gera embeddings e recria a coleção.
- `src/search.py`: faz busca vetorial, monta o contexto, chama a LLM e valida se a resposta está sustentada pelo contexto.
- `src/chat.py`: expõe um loop CLI simples para perguntas e respostas.
- `docker-compose.yml`: sobe PostgreSQL com pgvector.
- `document.pdf`: arquivo de entrada obrigatório.
- `.env.example`: contrato mínimo de configuração.

## Especificação que Não Pode Ser Quebrada

- O arquivo de entrada obrigatório é `document.pdf` na raiz.
- O chunking deve permanecer em 1000 caracteres com overlap de 150.
- A busca vetorial deve usar `similarity_search_with_score(query, k=10)` ou equivalente com os mesmos limites.
- A resposta deve ser baseada apenas no contexto recuperado.
- Se a informação não estiver explicitamente no contexto, a resposta obrigatória é:

`Não tenho informações necessárias para responder sua pergunta.`

## Setup e Comandos

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python .\src\ingest.py
python .\src\chat.py
```

## Configuração e Segredos

- Variáveis centrais: `PROVIDER`, `PGVECTOR_URL`, `PGVECTOR_COLLECTION`.
- OpenAI: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_CHAT_MODEL`.
- Google: `GOOGLE_API_KEY`, `GOOGLE_EMBEDDING_MODEL`, `GOOGLE_CHAT_MODEL`.
- Nunca commite `.env`; mantenha `.env.example` alinhado.

## Comportamento Esperado

- `src/ingest.py` deve usar `PyPDFLoader` e `RecursiveCharacterTextSplitter`.
- A ingestão recria a coleção configurada antes de gravar os chunks.
- `src/search.py` deve consultar o banco com `similarity_search_with_score(query, k=10)`.
- A resposta deve usar apenas os trechos recuperados do PDF.
- Quando o PDF estiver ausente, sem texto legível, ou houver problema de conexão com o banco, a aplicação deve exibir uma mensagem de erro clara no terminal.

## Convenções e Limites

- Preserve o contrato entre `ingest.py`, `search.py` e `chat.py`; evite duplicar lógica entre os arquivos.
- Qualquer mudança no prompt deve manter a regra de não inventar fatos e a resposta exata fora de contexto.
- O suporte atual de provedores é `openai` e `google`; não remova um ao ajustar o outro.
- Não altere o desafio para facilitar testes ou avaliação.
- Mantenha mensagens e documentação em pt-BR.

## Peculiaridades do Projeto

- A ingestão recria a coleção vetorial a cada execução para evitar resíduos.
- O projeto mistura requisitos de desafio acadêmico com um fluxo CLI executável.
- O histórico recente usa Conventional Commits em parte (`feat:`, `docs:`, `chore:`), mas não de forma totalmente rígida.
