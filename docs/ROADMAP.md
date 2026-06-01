# Roadmap AI-Pessoal (segundo cérebro)

Cada item deve passar no teste: **ajuda a registrar, relacionar ou recuperar conhecimento?**

## Semana 1 ⭐

- Conversa Ollama
- Captura: `nota:`, `ideia:`, `decisão:` (sem IA)
- Histórico de sessão (JSONL)
- Listar capturas recentes

## Semana 2 ⭐

- `buscar:` textual (notas + histórico + capturas)

## Semana 3 ⭐

- Memória: `fato:`, `pref:`, `projeto:`
- Injeção de memória no chat
- `quem sou eu?` a partir do registrado

## Semana 4 ⭐

- `decisão:` com motivo/risco
- `aprendi:` com fonte
- Consultas por projeto (Revigor, Master Chip, etc.)
- “por que decidi…”, “o que aprendi sobre…”

## Relacionar ✅ (v0.3.0)

- Links explícitos (`!liga`, `ref:` / `liga:` na captura)
- `relacionados: projeto|id`
- Mesmo `projeto:` no frontmatter
- Contexto de conversa inclui conexões

## Recuperar ✅ (v0.4.0)

- Intenção: `por que decidi…`, `o que aprendi…`, `o que anotei…`
- `recuperar:` / `!recuperar` (sem IA)
- Motivo / Risco / Fonte no contexto do chat
- Fontes citadas após resposta (CLI + web)

## Projeto ativo ✅ (v0.5.0)

- `projeto ativo: Nome` / `!projeto` / web header
- Filtra busca, recuperar, chat e capturas novas

## Compreender — semântica ✅ (v0.6.0)

- Embeddings Ollama (`nomic-embed-text`)
- Índice local `vectors.jsonl`
- `semantico:` · `!indexar` · merge em busca/chat/recuperar

## v2 (restante)

- PDFs + RAG em documentos
- “o que estudei sobre X?” com PDFs + conversas

## v3+ (só com coração sólido)

- Canais (Telegram/WhatsApp) — integração, não identidade
- Voz
- MCP pontual (com consentimento)

## Não é roadmap (commodity / dispersão)

- Lembretes
- To-do
- Resumo do dia (antes da memória forte)
- Agenda nativa
- CRM
- Código / winget / dispositivos
