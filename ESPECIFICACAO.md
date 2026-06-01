# AI-Pessoal — Especificação do produto

**Versão:** 2.0  
**Status:** Visão com escopo protegido (segundo cérebro, não agregador)  
**Princípio:** Excelente em **lembrar, recuperar e conectar conhecimento pessoal**. Tudo que não fortalece isso entra depois — ou nunca.

---

## 0. Pergunta norte

> **Qual dor o AI-Pessoal resolve?**

**Resposta:** Lembrar, recuperar e conectar conhecimento pessoal.

**Teste de escopo:** toda função nova deve responder “sim” a:

> Isso ajuda a **registrar**, **relacionar** ou **recuperar** pensamento/conhecimento/experiência passada?

Se não, é **fora do core** (integração opcional futura ou nunca).

---

## 1. Definição final

> **Um segundo cérebro local** que registra pensamentos, organiza conhecimento, preserva decisões e recupera experiências passadas para ajudar o usuário a **pensar melhor**.

**É:**

- conversa local (Ollama);
- captura rápida sem IA;
- memória estruturada;
- busca e recuperação;
- contexto por **projetos**;
- decisões e aprendizados preservados.

**Não é (nem será o coração):**

- organizador de tarefas;
- CRM;
- agenda / lembretes;
- chatbot WhatsApp/Telegram;
- assistente doméstico;
- secretária de desenvolvimento;
- mini Notion + mini ChatGPT + mini Todoist.

---

## 2. Risco que esta spec evita

Projeto começa como segundo cérebro e vira agregador medíocre. **Proteção agressiva de escopo:** rotina, canais e produtividade existem em abundância fora; o diferencial é **inteligência sobre o que você já registrou**.

---

## 3. O que não é (fora de escopo)

| Excluído | Motivo |
|----------|--------|
| Código, AST, winget, dispositivos | Fora desde v1.0 |
| **Lembretes** | Não aumenta inteligência; Agenda/Alexa/etc. já resolvem |
| **To-do / listas de tarefas** | Commodity; não é diferencial |
| **Resumo do dia** | Consequência da memória, não fundação — só após memória forte |
| **Telegram / WhatsApp (v1–v1.x)** | Canal ≠ inteligência; custo e dispersão altos |
| **Voz (v1–v1.x)** | Idem; depois do coração |
| Executável com LLM embutido | Ollama separado |
| OpenClaw/Nanobot no repo principal | Integrar só se necessário, sem mudar identidade |

**Rebaixado para “talvez nunca”:** proatividade tipo “te aviso às 14h”, CRM, agenda nativa.

---

## 4. Modelo de memória (cinco categorias)

Toda captura estruturada usa um tipo. Arquivos abertos (Markdown + JSON).

| Tipo | Prefixo / comando | Exemplo |
|------|-------------------|---------|
| **Fato** | `fato:` ou memória explícita | Tenho 54 anos. |
| **Preferência** | `pref:` | Prefiro português. |
| **Decisão** | `decisão:` | Trocar emprego. Motivo… Risco… |
| **Projeto** | `projeto:` | Revigor, Master Chip, Nhô Café… |
| **Aprendizado** | `aprendi:` | Cliente responde melhor a vídeo. Fonte: campanha junho. |

**Nota livre** (sem tipo): `nota:` — texto geral, indexado para busca.

**Ideia** (opcional): `ideia:` — meio-termo entre nota e aprendizado; pode fundir com `nota:` se quiser menos verbos.

Consultas típicas:

- `buscar: marketing`
- `o que eu anotei sobre marketing?` (conversa + recuperação)
- `por que decidi sair da empresa?`
- `o que aprendi sobre vendas?`
- `quem sou eu?` / perfil sintetizado do registrado

---

## 5. Captura rápida (sem IA)

Gravação imediata — **zero tokens**, zero latência.

```text
nota:   reunião com cliente X
ideia:  testar vídeo curto no funil
decisão: escolher Ollama local. Motivo: privacidade.
aprendi: Facebook converteu melhor que Instagram. Fonte: jun/2026.
projeto: Revigor
fato:   trabalho com consultoria no shopping
pref:   respostas diretas, sem enrolação
```

Cada entrada: timestamp + tipo + corpo (+ metadados opcionais: `projeto:Revigor` no frontmatter).

---

## 6. MVP (≈ 30 dias)

### Semana 1 — Conversa + registro + histórico

- Chat via Ollama (“pergunte qualquer coisa”)
- Captura `nota:`, `ideia:`, `decisão:` (mínimo); histórico JSONL de sessão
- Listar o que foi gravado hoje / por tipo

### Semana 2 — Busca textual

- `buscar: termo` em notas + histórico + capturas tipadas
- Resultados com data e tipo

### Semana 3 — Memória estruturada

- Persistir **fato**, **pref**, **projeto** (e esquecer/corrigir)
- Injetar memória relevante no prompt da conversa
- `quem sou eu?` → síntese a partir do registrado (não inventar)

### Semana 4 — Decisões + projetos

- Template **decisão** (motivo, risco, data)
- Template **aprendizado** (fonte)
- Filtro por `projeto:` (Revigor, Master Chip, etc.)
- Perguntas: “por que decidi…”, “o que aprendi sobre…”

**Fora do MVP:** lembretes, todo, Telegram, WhatsApp, RAG, semântica, voz, resumo do dia.

---

## 7. v1.1 (logo após MVP)

Prioridade **máxima** (não v1.2 distante):

- Sistema de **decisões** completo (registrar + recuperar + link a projeto)
- Sistema de **aprendizados**
- **Projetos** como eixo de contexto (filtro, tags, perguntas por projeto)
- Anexar trechos recuperados à conversa atual

---

## 8. v2 — Onde o conhecimento multiplica

Só depois do núcleo excelente:

- Indexar **PDFs e textos** locais
- **RAG** + **busca semântica**
- Perguntas do tipo: `o que já estudei sobre Empretec?` usando notas + PDFs + conversas

Isso vale mais que lembrete de remédio — alinhado à dor principal.

**Opcional em v2:** API HTTP local (outros frontends consomem o mesmo cérebro).

---

## 9. v3+ — Canais e extras (só se o coração estiver sólido)

- Telegram / WhatsApp como **canal**, não como produto
- Voz STT/TTS
- MCP (calendário, web) **com consentimento** — nunca substituir memória própria

**Regra:** canal não entra se desviar 2+ semanas do segundo cérebro.

---

## 10. Modelo de interação

| Ação | Como | IA? |
|------|------|-----|
| Capturar | `tipo: texto` | Não |
| Buscar | `buscar: termo` | Não |
| Conversar | linha normal ou `?` | Sim (Ollama + contexto recuperado) |
| Perfil | `quem sou eu?` | Sim (só sobre dados registrados) |
| Ajuda | `!ajuda` | Não |

Evitar modos ambíguos (`.`, `!nota` duplicado). **Prefixos de tipo** são a UI principal.

---

## 11. Arquitetura

```
Captura (tipos) ──► Armazenamento (MD + JSON por tipo/projeto)
                           │
Busca textual ─────────────┼──► Recuperação ──► Prompt ──► Ollama
                           │
v2: índice semântico + RAG ◘
```

Orquestrador fino em Python; Ollama externo; dados em `%USERPROFILE%\.ai-pessoal\`.

---

## 12. Estrutura de dados

```
.ai-pessoal/
├── config.json
├── data/
│   ├── capture/          # entradas por tipo (ou notes/ tipadas)
│   ├── projects/         # índice por projeto (opcional)
│   ├── memory/
│   │   ├── facts.json
│   │   ├── preferences.json
│   │   ├── decisions/
│   │   └── learnings/
│   ├── sessions/         # *.jsonl
│   └── index/            # v2: embeddings
```

---

## 13. Critérios de sucesso

1. Você **captura** em segundos sem abrir outro app.
2. Semanas depois, **acha** decisão, aprendizado ou nota por projeto/tema.
3. Na conversa, o assistente **usa** o que você registrou — não inventa biografia.
4. Não sente necessidade de Todoist/Notion **dentro** deste app para o core.
5. v2 com PDFs muda a vida em estudo/consultoria — não v1 com WhatsApp.

---

## 14. Histórico de decisões

| Data | Decisão |
|------|---------|
| 2026-06 | Produto = AI-Pessoal; fim da secretária de dev |
| 2026-06 | Dor norte = lembrar, recuperar, conectar conhecimento |
| 2026-06 | Escopo agressivo: cortar lembretes, todo, canais no início |
| 2026-06 | Memória em 5 categorias; projetos como eixo; v2 = RAG/PDFs |

---

*Documento vivo — qualquer feature passa pelo teste da seção 0.*
