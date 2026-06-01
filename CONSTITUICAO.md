# Constituição do AI-Pessoal — Guardião do Produto

**Status:** vigente  
**Função:** mecanismo de defesa contra scope creep e perda de identidade  
**Complementa:** [ESPECIFICACAO.md](./ESPECIFICACAO.md) (o *o quê* e *quando*) — este documento define *como decidir*

> O AI-Pessoal não precisa de mais features. Precisa de **clareza**, **disciplina** e **longevidade**.

---

## 1. Papel do Guardião

Quem projeta, codifica ou sugere mudanças neste repositório atua como **Guardião do Produto**:

| Papel | O que faz |
|-------|-----------|
| **Filtro** | Não gera ideias por hype; avalia pedidos contra critérios |
| **Memória institucional** | Preserva o *porquê* das decisões |
| **Anti-entropia** | Resiste ao crescimento desordenado |
| **Jardineiro** | Cultiva o essencial (captura, recuperação, decisões) |
| **Tradutor** | Converte necessidade real em decisão arquitetural mínima |
| **Arquivista** | Garante que dados e formatos sobrevivam ao código |

**Critério máximo de valor:** *Isso ainda será útil daqui a 5 anos?*

---

## 2. Identidade (imutável no coração)

### É

Um **segundo cérebro local** que:

- registra pensamentos (`nota:`, `ideia:`, …);
- preserva decisões e aprendizados;
- recupera o que você já viveu/registrou;
- ajuda a **pensar melhor** — não a executar a vida inteira.

### Não é (nem será o coração)

| Excluído | Motivo |
|----------|--------|
| Agenda / lembretes | Commodity; não aumenta inteligência sobre *seu* acervo |
| CRM / ERP / tickets | Outro produto |
| To-do / produtividade genérica | Todoist, Notion, etc. |
| Clone ChatGPT na nuvem | Local e *seus* dados |
| Assistente de desenvolvimento | Você já tem ferramentas de código |
| Hub de integrações | Dispersão |
| Central de notificações | Proatividade ≠ segundo cérebro |
| Automação geral do PC | Fora de escopo |
| Mini Notion + mini ChatGPT + mini Todoist | O risco que esta constituição evita |

**Produtos irmãos (repos separados):** [Cortana](https://github.com/RivasCode-Ops/Cortana) (pesquisa web + fontes), [workbench](https://github.com/RivasCode-Ops/workbench) (método de entrega). Não fundir identidades.

---

## 3. Seis perguntas obrigatórias (antes de qualquer feature)

Toda proposta deve responder **sim** em pelo menos uma pergunta central (1–4). A pergunta 5 e 6 são **travas de qualidade**.

| # | Pergunta | Se não… |
|---|----------|---------|
| 1 | Isso ajuda a **lembrar** melhor? | Fora do core (ou desejo documentado para revisão semestral) |
| 2 | Isso ajuda a **recuperar** melhor? | Idem — inclui performance de busca, não só “memória nova” |
| 3 | Isso ajuda a **conectar** conhecimento? | Idem — fase “Relacionar”; não antes de Organizar/Recuperar sólidos |
| 4 | Isso fortalece a **inteligência pessoal** do usuário? | Deve ser específico: “usa o que ele registrou”, não “parece inteligente” |
| 5 | Isso mantém **simplicidade**, **privacidade** e **velocidade**? | Simplificar ou recusar |
| 6 | Isso melhora **confiabilidade**, **durabilidade** ou **manutenibilidade**? | Bugfix e formato de dados sim; feature vazia não |

**Regra:** feature que só passa na 6 (ex.: refatorar) é válida; feature que não passa em nenhuma → **não implementar**.

---

## 4. Princípios arquiteturais

| # | Princípio | Compromisso |
|---|-----------|-------------|
| 1 | **Simplicidade** | Menos código legível > mais código “poderoso” |
| 2 | **Dados abertos** | Markdown + JSONL; legíveis sem o app |
| 3 | **Privacidade local** | Núcleo sem nuvem obrigatória |
| 4 | **Evolução gradual** | Camadas (seção 5); não pular fases |
| 5 | **Baixa dependência externa** | Ollama como motor; evitar SDKs desnecessários |
| 6 | **Facilidade de manutenção** | Testes onde o comportamento importa; código plano |
| 7 | **Persistência do conhecimento** | O acervo sobrevive a versões do app |
| 8 | **Clareza operacional** | Prefixos e `!comandos` previsíveis |
| 9 | **Escalabilidade conceitual** | Seis categorias de memória escalam sem virar ERP |
| 10 | **Longevidade** | Preferir formatos e shell básicos; documentar migração de LLM |

---

## 5. Filosofia de crescimento (camadas obrigatórias)

Ordem **não negociável**:

```text
Capturar → Organizar → Recuperar → Relacionar → Compreender
```

| Fase | Significado | Estado v0.1.0 |
|------|-------------|---------------|
| **Capturar** | Gravar sem fricção (`nota:`, `decisão:`, …) | ✅ |
| **Organizar** | Tipos, pastas, consistência | ⚠️ Parcial |
| **Recuperar** | Busca textual; depois semântica | ⚠️ Parcial |
| **Relacionar** | Ligações entre notas/decisões/projetos | ❌ |
| **Compreender** | Linha do tempo, sínteses sobre evolução | ❌ |

**Regra do Guardião:** não avançar para **Relacionar** antes de **Organizar** e **Recuperar** estarem sólidos.

### Memória (seis categorias)

| Categoria | Prefixo | Papel |
|-----------|---------|--------|
| Fatos | `fato:` | Verdades objetivas |
| Preferências | `pref:` | Gostos e hábitos |
| Projetos | `projeto:` | Contexto (Revigor, Master Chip, …) |
| Decisões | `decisão:` | Escolha + motivo (+ risco) |
| Aprendizados | `aprendi:` | Lição + fonte |
| Notas | `nota:` / `ideia:` | Informação livre |

Evoluções permitidas **sem violar princípios:** tags leves (Organizar), links entre entradas (Relacionar), timelines (Compreender).

---

## 6. Teste dos 5 anos

Antes de implementar, pergunte:

> *Se eu parar de manter este código hoje, o que o usuário gravou ainda funciona daqui a 5 anos?*

| Dependência | Veredito |
|-------------|----------|
| APIs externas obrigatórias | ❌ |
| Serviços cloud obrigatórios | ❌ |
| Versão exata sem fallback | ⚠️ documentar |
| Formatos proprietários | ❌ |
| Dependências obscuras | ⚠️ evitar |

**Deve continuar válido:** arquivos em `~/.ai-pessoal/`, Markdown, JSONL, leitura manual.

---

## 7. O que fazer quando…

| Situação | Ação do Guardião |
|----------|------------------|
| Surge tecnologia hype | Esperar 6 meses; reavaliar com as 6 perguntas |
| Pedido fora do escopo | Registrar em “desejos” (issue/doc); não implementar; revisar a cada 6 meses |
| Bug crítico vs feature nova | **Bug primeiro** — estabilidade > novidade |
| Dúvida entre duas soluções | Mais simples, mais legível, menos dependências |
| Pedido de integrar Cortana/WhatsApp no core | Ponte ou export; outro repo ou fase tardia |
| “Só mais um comando” | Passa nas 6 perguntas ou não entra |
| Busca lenta mas correta | Pergunta 2 e 6 — válido melhorar performance |
| Fadiga com prefixos (futuro) | UX: perguntar “nota ou conversa?” — sem abandonar tipos |

---

## 8. Métrica de saúde do sistema

O produto está saudável quando:

- [ ] Uso real ≥ 3× por semana (captura ou busca)
- [ ] Recuperar algo antigo em **< 10 s** (`buscar:` ou listagem)
- [ ] Nenhuma quebra crítica nos últimos 30 dias
- [ ] `~/.ai-pessoal/` abre e edita em qualquer editor de texto
- [ ] Pedidos de feature fora do escopo são **adiados**, não aceitos por default
- [ ] Identidade “segundo cérebro” reconhecível em demo de 2 minutos

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| Obsolescência do Ollama | Abstrair cliente LLM; documentar troca para API compatível |
| Crescimento de `~/.ai-pessoal/` | Futuro: `!arquivar` sessões antigas (não prioridade MVP) |
| Fadiga de prefixos | Modo ambíguo com confirmação (v1.1+) |
| Dependência de Python | Aceita no curto prazo; executável só se necessário (v2+) |
| Scope creep por agentes IA | Este arquivo + regra Cursor: ler antes de sugerir código |

---

## 10. Uso deste documento

1. **Você** — dúvida de escopo → seção 3 ou 7  
2. **Cursor / agentes** — ler `CONSTITUICAO.md` + `ESPECIFICACAO.md` antes de implementar  
3. **PRs** — mudança de comportamento deve citar qual pergunta (1–6) atende  
4. **Onboarding** — identidade em 5 minutos: seções 2 e 5  

---

## 11. Emendas

| Data | Emenda |
|------|--------|
| 2026-06 | Constituição inicial (Guardião do Produto + pergunta 6 + teste 5 anos + saúde) |

*Emendas futuras: adicionar linha aqui; não apagar princípios sem revisão explícita.*

---

**Veredicto:** esta constituição está **aprovada** como lei do projeto. Código e [ROADMAP](./docs/ROADMAP.md) devem obedecê-la; detalhes de entrega ficam na [ESPECIFICACAO.md](./ESPECIFICACAO.md).
