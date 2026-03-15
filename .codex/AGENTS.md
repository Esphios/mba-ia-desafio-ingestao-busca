# AGENTS.md

## Regra máxima deste repositório

Este projeto possui uma especificação formal de desafio, e ela deve sempre ter prioridade máxima.

Ao analisar, modificar ou refatorar este repositório, siga esta ordem de prioridade:

1. Cumprir a especificação do desafio
2. Preservar a estrutura obrigatória do projeto
3. Manter o projeto claro, simples e adequado para desenvolvedores pt-BR
4. Aplicar boas práticas de engenharia sem violar os itens acima

Se houver conflito entre uma melhoria arquitetural genérica e a especificação do desafio, siga a especificação do desafio.

---

## Especificação obrigatória do projeto

O software deve ser capaz de:

1. Ler um arquivo PDF
2. Dividir o conteúdo em chunks de 1000 caracteres com overlap de 150
3. Gerar embeddings para cada chunk
4. Armazenar os vetores em PostgreSQL com pgVector
5. Permitir perguntas via linha de comando
6. Vetorizar a pergunta do usuário
7. Buscar os 10 resultados mais relevantes no banco vetorial
8. Montar o prompt com os resultados recuperados
9. Chamar a LLM
10. Responder apenas com base no conteúdo do PDF

### Regra crítica de resposta

Se a informação não estiver explicitamente no contexto recuperado, a resposta deve ser exatamente:

`Não tenho informações necessárias para responder sua pergunta.`

Essa regra é obrigatória.
Não enfraqueça essa regra.
Não permita respostas inventadas.
Não permita uso de conhecimento externo.
Não permita opiniões, extrapolações ou interpretações além do texto disponível.

---

## Prompt funcional obrigatório da aplicação

A lógica da aplicação deve respeitar este comportamento de prompt:

```text
CONTEXTO: {resultados concatenados do banco de dados}
REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda: "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.
EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
PERGUNTA DO USUÁRIO: {pergunta do usuário}
RESPONDA A "PERGUNTA DO USUÁRIO"
```
