# Guia de trabalho — Cortana

Documento para abrir **antes de cada sessão** no projeto Cortana.  
Mantém escopo, evita misturar com **AI-Pessoal** e aponta para o repo certo.

**Repo canônico (V1 atual):** [github.com/RivasCode-Ops/Cortana](https://github.com/RivasCode-Ops/Cortana)  
**Caminho local habitual (README do repo):** `c:\_PROJETOS\Cortana` (ajuste se o clone estiver em outro lugar)

---

## 0. Pergunta norte (Cortana)

> **Qual dor o Cortana resolve?**

**Resposta:** Transformar uma **demanda em linguagem natural** em **resposta estruturada com fontes**, usando busca web (SearXNG) + extração de páginas + síntese com IA — tudo **local**, com histórico auditável.

**Teste de escopo** — toda feature nova deve responder “sim” a:

> Isso melhora **buscar**, **extrair**, **sintetizar** ou **apresentar fontes** para uma demanda externa?

Se for só “lembrar o que **eu** escrevi”, “decisão minha”, “nota pessoal” → é **AI-Pessoal**, não Cortana.

---

## 1. O que é / o que não é

### É

- App de **pesquisa inteligente** (Perplexity-like, local-first).
- Pipeline: classificar demanda → subconsultas → SearXNG → rank URLs → extrair texto → síntese LLM.
- Histórico em **SQLite** (`apps/api/data/cortana.db`).
- UI **React** + API **Express** + TypeScript.
- Saídas tipadas: resumo, comparação, shortlist, briefing, relatório, direcionamentos.
- Ollama ou qualquer endpoint **OpenAI-compatible**.

### Não é

- Segundo cérebro (`nota:`, `decisão:`, `aprendi:`) → **AI-Pessoal**
- CRM, todo, agenda, WhatsApp-bot
- Secretária de dev / análise AST de código
- Substituto do **workbench** (método de entrega)
- **COmniWS** (estação desktop ampla) — produto irmão, não o mesmo núcleo

---

## 2. Linhagens do nome “Cortana” (não confundir)

| Versão | Onde | Stack | Status |
|--------|------|-------|--------|
| **Cortana V1 (canônica)** | `RivasCode-Ops/Cortana` | React + Express + SQLite + SearXNG | **Ativa** — este guia |
| **Cortana legado (prompts)** | `d:\PROJETOS\00_RECURSOS\prompts\PROMPTS-raiz\cortana\` | Python, GitHub API, `prompt_sources/` | Referência / prompts antigos; **não** é o repo principal |

Ao codar ou fazer PR: trabalhar no repo **TypeScript**. Só mexer no Python legado se for portar prompt ou regra de negócio explícita.

---

## 3. Relação com AI-Pessoal (ecossistema)

```text
┌─────────────────┐         ┌─────────────────┐
│   AI-Pessoal    │         │     Cortana     │
│  (seu acervo)   │         │  (mundo externo) │
│  notas, decisões│         │  web + fontes   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │    v2+: exportar aprendi:  │
         └───────────┬───────────────┘
                     ▼
              "Pesquisei X" + links
              gravado no segundo cérebro
```

| Ação | Onde |
|------|------|
| “Por que decidi sair da empresa?” | AI-Pessoal |
| “Compare fornecedores de X no mercado” | Cortana |
| Salvar conclusão da pesquisa com fonte | AI-Pessoal (`aprendi:` + link) — integração futura |
| Método de como construir / revisar | [workbench](https://github.com/RivasCode-Ops/workbench) |

**Regra:** não fundir repositórios. Integração = API ou export manual, depois do MVP de cada um.

---

## 4. Arquitetura (resumo)

Ver detalhe em `docs/ARCHITECTURE.md` no repo Cortana.

```text
Usuário (React :5173)
    ▼
API Express (:8787) ──► SQLite (cortana.db)
    ├── Orchestrator
    │     ├── classificar demanda
    │     ├── subconsultas (LLM ou heurística)
    │     ├── SearXNG JSON
    │     ├── rank + fetch + extração (cheerio / Readability)
    │     └── síntese (LLM)
    ├── SearXNG (:8080)
    └── LLM (Ollama / OpenAI-compatible)
```

**Tabelas principais:** `searches`, `search_queries`, `search_results`, `source_extracts`, `final_reports`, `app_settings`.

---

## 5. Pré-requisitos e subir ambiente

| Item | Versão / nota |
|------|----------------|
| Node.js | 20+ |
| Docker | Opcional mas recomendado (SearXNG) |
| Ollama | Opcional; configurável na UI |
| RAM | 8 GB mínimo; 16 GB confortável para modo “profundo” |

### Comandos (sessão típica)

```powershell
cd c:\_PROJETOS\Cortana   # ou seu clone
npm install

# SearXNG (busca web)
docker compose up -d
# URL padrão: http://127.0.0.1:8080

# Dev
npm run dev
# API: http://127.0.0.1:8787
# Web: http://127.0.0.1:5173
```

### Configuração na UI

1. Abrir **Configurações**
2. URL do SearXNG
3. Endpoint + chave + modelo de IA
4. **Testar IA** e (quando existir) **Testar SearXNG**
5. Salvar

### Produção local

```powershell
npm run build
npm start
# Tudo em http://127.0.0.1:8787
```

---

## 6. Fluxo V1 (o que o usuário vê)

1. Demanda em linguagem natural no dashboard  
2. Classificação + subconsultas  
3. Busca SearXNG  
4. Seleção e extração de páginas  
5. Síntese **somente** com conteúdo extraído (não inventar sem fonte)  
6. Relatório + histórico local  

**Princípio:** busca antes de síntese — nunca “chute” sem fonte.

---

## 7. Estado do produto (referência rápida)

Fonte: `docs/ROADMAP.md` no repo (atualizar após cada release).

| Área | Status |
|------|--------|
| Pipeline busca → extração → síntese | ✅ |
| SearXNG + SQLite + histórico | ✅ |
| Busca por imagem (categorias SearXNG) | ✅ |
| Readability + export MD | ✅ V1.2 |
| CI / testes automatizados | ❌ → V1.3 |
| Modos rápido / balanceado / profundo | 📋 V1.3 |
| Integração AI-Pessoal | 📋 V2+ |

**Maturidade (estimativa do roadmap):** ~6,5/10 uso pessoal · ~4,5/10 produto comercial.

---

## 8. Próximo sprint sugerido (V1.3)

Prioridade do próprio roadmap do repo:

1. Smoke test API + **GitHub Actions**  
2. **Modos de pesquisa** (rápido / balanceado / profundo)  
3. Classificação de demanda via LLM (fallback regex)  
4. Cancelar pesquisa em andamento  
5. Histórico com filtro + paginação  
6. `.env.example` + troubleshooting no README  

Ordem: **CI + modos** antes de integrações grandes (ex. ARBILOCAL no V2).

---

## 9. O que NÃO fazer neste repo (anti-creep)

- [ ] Captura `nota:` / `decisão:` / memória pessoal estruturada  
- [ ] Lembretes, todo, agenda  
- [ ] Bot Telegram/WhatsApp como core  
- [ ] Duplicar orchestrator do AI-Pessoal  
- [ ] Portar o monólito Python legado inteiro sem plano  

Se surgir demanda assim → issue no **AI-Pessoal** ou nota em `aprendi:` após exportar relatório do Cortana.

---

## 10. Checklist — início de sessão

Copiar mentalmente ou marcar:

- [ ] Estou no repo **RivasCode-Ops/Cortana** (não na pasta `prompts/.../cortana` legada)
- [ ] Li `docs/ROADMAP.md` — sei qual item estou atacando (#5–#12 V1.3, etc.)
- [ ] SearXNG responde em `:8080` (se a tarefa envolve busca)
- [ ] IA testada em Configurações (se a tarefa envolve síntese)
- [ ] Feature passa no **teste de escopo** (seção 0)
- [ ] Não estou implementando segundo cérebro aqui

---

## 11. Checklist — fim de sessão

- [ ] `npm run build` ok (se mexeu em api ou web)
- [ ] Atualizar `docs/ROADMAP.md` (status do item)
- [ ] Se usou workbench: `HANDOFF.md` / commit message com # do item
- [ ] Se descobriu algo para o cérebro pessoal: anotar em AI-Pessoal (`aprendi:`) — não commitar no Cortana

---

## 12. Documentos no repo Cortana

| Arquivo | Uso |
|---------|-----|
| `README.md` | Instalação e fluxo V1 |
| `docs/ARCHITECTURE.md` | Diagrama e tabelas SQLite |
| `docs/ROADMAP.md` | Prioridades e esforço S/M/L |
| `docs/GITHUB-REFERENCES.md` | Benchmark de repos |
| `docs/WORKBENCH-NOTES.md` | Alinhamento com método workbench |
| `docs/IMAGE-SEARCH.md` | Busca por imagem / V2 upload |
| `DEV-SETUP.md` | Setup de desenvolvimento |

---

## 13. workbench (como construir Cortana)

Etapa referência: **20-ENTREGA-DE-PRODUTO** em [RivasCode-Ops/workbench](https://github.com/RivasCode-Ops/workbench).

Regras herdadas:

1. Não implementar sem entender o fluxo ponta a ponta  
2. Fundação funcional antes de polish  
3. Busca antes de síntese  
4. Local-first (SQLite, SearXNG local)  

---

## 14. Integração futura com AI-Pessoal (V2 ecossistema)

**Não implementar até AI-Pessoal MVP estável.**

Esboço:

```text
Cortana finaliza relatório
    → POST opcional ou export MD
    → AI-Pessoal importa como:

aprendi: [resumo]. Fonte: Cortana search #123 + URLs
projeto: Revigor
```

Endpoint candidato: `GET /searches/:id/export` (já existe export MD na UI — reutilizar).

---

## 15. Demandas de exemplo (testar regressão)

| Demanda | Tipo esperado |
|---------|----------------|
| “Resumo sobre tendências de café especial no Brasil” | `summary` / `briefing` |
| “Compare três ERPs para pequeno varejo” | `comparison` |
| “Fornecedores de embalagem biodegradável SP” | `shortlist` + heurística comercial |
| “O que preciso definir antes de contratar consultoria?” | `directions` |

Registrar falhas (SearXNG down, timeout LLM, extração vazia) para melhorar mensagens em PT.

---

## 16. Histórico deste guia

| Data | Nota |
|------|------|
| 2026-06 | Criado em `Assistente Pessoal/docs/` para sessões Cortana; alinhado a ROADMAP V1.3 do repo |

---

*Ao começar a codar, abra este arquivo + `Cortana/docs/ROADMAP.md` no mesmo workspace.*
