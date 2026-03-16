# Ingestão e Busca Semântica com LangChain e PostgreSQL/pgVector

## Objetivo

Este projeto implementa o fluxo exigido pelo desafio de ingestão e busca semântica:

1. Ler `document.pdf`
2. Dividir o texto em chunks de 1000 caracteres com overlap de 150
3. Gerar embeddings
4. Armazenar os vetores em PostgreSQL com pgVector
5. Receber perguntas via CLI
6. Vetorizar a pergunta e buscar os 10 trechos mais relevantes com `similarity_search_with_score(query, k=10)`
7. Montar o prompt com o contexto recuperado
8. Chamar a LLM
9. Responder somente com base no PDF

## Tecnologias

- Python
- LangChain
- PostgreSQL
- pgVector
- Docker Compose

## Estrutura

```text
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── src/
│   ├── ingest.py
│   ├── search.py
│   └── chat.py
├── document.pdf
└── README.md
```

## Como executar

### 1. Criar ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie `.env.example` para `.env`.

Configurações suportadas:

- `PROVIDER=openai` usa `text-embedding-3-small` e `gpt-5-nano`
- `PROVIDER=google` usa `models/embedding-001` e `gemini-2.5-flash-lite`
- `PGVECTOR_URL` aponta para o PostgreSQL com pgVector
- `PGVECTOR_COLLECTION` define a coleção usada pelo PGVector

### 3. Garantir o PDF na raiz do projeto

O arquivo obrigatório deve estar em `document.pdf`.

## Execução

### 1. Subir o banco

```powershell
docker compose up -d
```

### 2. Rodar a ingestão

```powershell
python .\src\ingest.py
```

A ingestão recria a coleção configurada antes de gravar os chunks, evitando que sobras de execuções anteriores contaminem a busca.

### 3. Rodar o chat

```powershell
python .\src\chat.py
```

## Comportamento esperado

- `src/ingest.py` usa `PyPDFLoader` e `RecursiveCharacterTextSplitter`
- os chunks são gerados com `chunk_size=1000` e `chunk_overlap=150`
- `src/search.py` consulta o banco com `similarity_search_with_score(query, k=10)`
- a resposta usa apenas os trechos recuperados do PDF

Se a informação não estiver explicitamente no contexto recuperado, a resposta obrigatória é:

```text
Não tenho informações necessárias para responder sua pergunta.
```

### Exemplo

### Em contexto

```text
Faca sua pergunta: O que é o GPT-5?

PERGUNTA: O que é o GPT-5?
RESPOSTA: O GPT-5 é um sistema unificado da OpenAI que combina dois tipos de modelos:
- modelos rápidos de alto throughput (gpt-5-main e gpt-5-main-mini), para respostas rápidas;
- modelos de raciocínio mais profundo (gpt-5-thinking e gpt-5-thinking-mini), para problemas que exigem mais reflexão.
```

### Fora de contexto

```text
Faça sua pergunta: Qual é a capital da França?

PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

Quando o PDF estiver ausente, sem texto legível, ou quando houver problema de conexão com o banco, a aplicação exibe uma mensagem de erro clara no terminal.
