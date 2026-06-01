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
.\run.ps1          # terminal
.\run-web.ps1      # navegador em http://127.0.0.1:8765
```

Requisitos: **Python 3.11+**, **Ollama** rodando (`ollama serve`) e um modelo baixado (ex.: `ollama pull qwen2.5:7b`).

Dados do usuário: `%USERPROFILE%\.ai-pessoal\` (config + capturas + sessões).

Interface web (opcional): `pip install -e ".[web]"` ou use `run-web.ps1`.

## Uso rápido

| Entrada | Efeito |
|---------|--------|
| `nota: reunião com cliente` | Grava sem IA |
| `decisão: usar Ollama. Motivo: privacidade.` | Grava decisão |
| `? como priorizo projetos?` | Conversa com Ollama |
| `buscar: marketing` | Busca em capturas e conversas |
| `!hoje` | Lista capturas de hoje |
| `quem sou eu?` | Perfil só do registrado |
| `!memoria` / `!projetos` | Fatos, prefs, projetos |
| `projeto: Revigor` | Busca por projeto |
| `projeto ativo: Revigor` | Filtra tudo; capturas herdam projeto |
| `recuperar: termo` | Acervo sem IA (ou `!recuperar`) |
| `?por que decidi X` | Conversa com decisões no contexto |
| `relacionados: Revigor` | Conexões (projeto + links + ref:) |
| `!liga id1 id2` | Liga duas capturas |
| `ref: id` na captura | Vincula à entrada existente |
| `!sair` | Encerra |

## Estado

**v0.7.0** — **PDFs + RAG**: coloque `.pdf` em `~/.ai-pessoal/data/documents/`, rode `!indexar`. Busca e chat incluem trechos dos PDFs.

```powershell
pip install "ai-pessoal[pdf]"
```

**v0.6.0** — **Busca semântica** (Ollama local): `semantico:`, `!indexar`, índice em `data/embeddings/`. Ative em `config.json` → `features.semantic_search`.

```powershell
ollama pull nomic-embed-text
# config: "semantic_search": true
.\run.ps1
!semantico on
!indexar
semantico: funil de conversão
```

**v0.5.0** — Projeto ativo filtra busca, recuperar e chat.

**v0.4.0** — Recuperar: intenção, `recuperar:`, fontes no chat.

**v0.3.0** — Relacionar: links, `relacionados:`, grafo por projeto.
