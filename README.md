# AI-Pessoal

**Segundo cérebro local:** registra pensamentos, preserva decisões e aprendizados, recupera o que você já viveu/registrou — para pensar melhor.

Não é Todoist, agenda, WhatsApp-bot nem ferramenta de código.

## Documentação

- **[CONSTITUICAO.md](./CONSTITUICAO.md)** — Guardião do Produto: 6 perguntas, princípios, o que fazer quando… (ler antes de pedir features)
- **[ESPECIFICACAO.md](./ESPECIFICACAO.md)** — dor norte, teste de escopo, memória em 5 tipos, MVP 30 dias
- **[docs/ROADMAP.md](./docs/ROADMAP.md)** — semanas 1–4 e v2 (RAG/PDFs)
- **[docs/CORTANA.md](./docs/CORTANA.md)** — guia de trabalho quando for sessão no projeto Cortana (irmão: pesquisa web + fontes)

## Princípios

1. **Dor única** — lembrar, recuperar e conectar conhecimento pessoal.
2. **Captura sem IA** — `nota:`, `decisão:`, `aprendi:`, `projeto:` …
3. **Projetos como contexto** — Revigor, Master Chip, consultoria, etc.
4. **Canais e lembretes depois** — ou nunca, se diluírem o foco.

## Instalação (Windows)

```powershell
cd "d:\PROJETOS\Assistente Pessoal"
.\install.ps1
.\.venv\Scripts\Activate.ps1
python -m ai_pessoal
```

Requisitos: **Python 3.11+**, **Ollama** rodando (`ollama serve`) e um modelo baixado (ex.: `ollama pull qwen2.5:7b`).

Dados do usuário: `%USERPROFILE%\.ai-pessoal\` (config + capturas + sessões).

## Uso rápido

| Entrada | Efeito |
|---------|--------|
| `nota: reunião com cliente` | Grava sem IA |
| `decisão: usar Ollama. Motivo: privacidade.` | Grava decisão |
| `? como priorizo projetos?` | Conversa com Ollama |
| `buscar: marketing` | Busca em capturas e conversas |
| `!hoje` | Lista capturas de hoje |
| `!sair` | Encerra |

## Estado

**v0.1.0** — MVP semana 1 + busca textual (semana 2): TUI, captura tipada, chat Ollama, histórico JSONL, `buscar:`.
