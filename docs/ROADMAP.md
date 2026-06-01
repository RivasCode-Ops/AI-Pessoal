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

## v1.1 (restante)

- Projetos como filtro global (projeto ativo em config)
- Refinar ranking de relevância

## v2

- PDFs + RAG
- Busca semântica
- “o que estudei sobre X?” (notas + docs + conversas)
- API HTTP local (opcional)

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
