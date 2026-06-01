from __future__ import annotations

import re

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ai_pessoal import __version__
from ai_pessoal.capture import capture_dir, list_captures, parse_capture_line, save_capture, search_captures
from ai_pessoal.recover import format_retrieval_markdown, retrieve_for_query
from ai_pessoal.relate import add_link, format_related_markdown, gather_related
from ai_pessoal.chat import run_chat
from ai_pessoal.config import (
    get_active_project,
    is_semantic_enabled,
    load_config,
    resolve_project,
    set_active_project,
    set_semantic_search,
)
from ai_pessoal.documents import documents_dir, index_all_documents, list_document_sources
from ai_pessoal.semantic import index_all, search_index
from ai_pessoal.memory import format_who_am_i, list_profile_entries, list_projects
from ai_pessoal.ollama_client import OllamaError, health_check, list_models
from ai_pessoal.session import ChatSession, search_sessions, start_session

console = Console()

_SEARCH_RE = re.compile(r"^buscar\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)
_PROJETO_BUSCA_RE = re.compile(r"^projeto\s*:\s*(.+)$", re.IGNORECASE)
_RELACIONADOS_RE = re.compile(r"^relacionados\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)
_RECUPERAR_RE = re.compile(r"^recuperar\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)
_PROJETO_ATIVO_RE = re.compile(r"^projeto\s+ativo\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)
_SEMANTICO_RE = re.compile(r"^semantico\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _help_text() -> str:
    return """
[bold]Captura[/] (sem IA)
  nota: / ideia: / decisão: / fato: / pref: / projeto: / aprendi:

  Decisão com estrutura:
    decisão: escolher Ollama
    Motivo: privacidade
    Risco: modelo menor

  Aprendizado:
    aprendi: vídeo converte melhor
    Fonte: campanha jun/2026

[bold]Recuperar[/] (sem IA — só o acervo)
  recuperar: marketing
  semantico: funil de vendas  (requer !indexar + Ollama embed)

[bold]PDFs[/] (pasta data/documents)
  Coloque .pdf → !indexar (inclui docs)
  !docs — listar PDFs na pasta

[bold]Semântica[/] (Ollama nomic-embed-text)
  !indexar — capturas + PDFs
  !semantico on | off

[bold]Conversa[/]
  ? pergunta
  ou texto livre (memória + trechos anexados à resposta)

[bold]Projeto ativo[/] (filtra busca, recuperar e chat)
  projeto ativo: Revigor
  !projeto Revigor | !projeto limpar | !projeto

[bold]Perfil[/]
  quem sou eu?
  !memoria
  !projetos

[bold]Relacionar[/]
  relacionados: Revigor
  relacionados: 20260601-120000-nota
  !relacionados [projeto ou id]
  !liga id_origem id_destino

  Na captura, vincule com:
    ref: 20260601-120000-nota
    projeto: Revigor

[bold]Comandos[/]
  !ajuda | !sair | !notas [n] | !hoje
  !buscar termo | buscar: termo | projeto: Nome
  !modelo | !ollama | !web
"""


def _print_banner(cfg, data_dir, model: str, ollama_ok: bool) -> None:
    status = "[green]Ollama OK[/]" if ollama_ok else "[red]Ollama offline[/]"
    n = len(list_captures(data_dir, limit=500))
    active = get_active_project(cfg)
    sem = "[green]semântica on[/]" if is_semantic_enabled(cfg) else "[dim]semântica off[/]"
    proj_line = f"\nProjeto ativo: [cyan]{active}[/]" if active else "\nProjeto ativo: [dim]nenhum[/]"
    proj_line += f" · {sem}"
    console.print(
        Panel(
            f"[bold]AI-Pessoal[/] v{__version__} — segundo cérebro local\n"
            f"Dados: [dim]{data_dir}[/]\n"
            f"Modelo: [cyan]{model}[/] · {status} · [dim]{n} capturas[/]"
            f"{proj_line}",
            border_style="blue",
        )
    )
    console.print("[dim]Captura: nota: · Conversa: ? · Perfil: quem sou eu? · !ajuda[/]\n")


def _format_capture_row(entry) -> str:
    ts = entry.created.strftime("%d/%m %H:%M")
    body = entry.body.replace("\n", " ")
    if len(body) > 70:
        body = body[:67] + "..."
    return f"[dim]{ts}[/] [cyan]{entry.type_label}[/] {body}"


def _parse_buscar_query(raw: str) -> tuple[str, str | None]:
    raw = raw.strip()
    m = _PROJETO_BUSCA_RE.match(raw)
    if m:
        return "", m.group(1).strip()
    return raw, None


def _cmd_notas(data_dir, arg: str, kind: str | None = None) -> None:
    limit = 10
    if arg.strip().isdigit():
        limit = max(1, min(50, int(arg.strip())))
    entries = list_captures(data_dir, limit=limit, kind=kind)
    if not entries:
        console.print("[yellow]Nenhuma captura.[/]")
        return
    for e in entries:
        console.print(_format_capture_row(e))


def _cmd_hoje(data_dir) -> None:
    entries = list_captures(data_dir, limit=50, today_only=True)
    if not entries:
        console.print("[yellow]Nada capturado hoje.[/]")
        return
    for e in entries:
        console.print(_format_capture_row(e))


def _cmd_buscar(cfg, data_dir, query: str) -> None:
    q, explicit = _parse_buscar_query(query)
    project = resolve_project(cfg, explicit)
    if not q and not project:
        console.print("[yellow]Uso: buscar: termo  |  projeto: Nome  |  !buscar termo[/]")
        return

    seen: set[str] = set()
    cap_hits: list = []
    sem_hits: list = []

    if is_semantic_enabled(cfg) and q:
        sem_hits = search_index(data_dir, cfg, q, limit=12, project=project)
        for s in sem_hits:
            if s.entry and s.entry.id not in seen:
                seen.add(s.entry.id)
                cap_hits.append(s.entry)

    for e in search_captures(data_dir, q, project=project):
        if e.id not in seen:
            seen.add(e.id)
            cap_hits.append(e)

    sess_hits = search_sessions(data_dir, q) if q else []

    label = project or q
    if not cap_hits and not sess_hits and not sem_hits:
        console.print(f"[yellow]Nada encontrado para «{label}».[/]")
        return

    if sem_hits:
        console.print(f"\n[bold]Semântica ({len(sem_hits)})[/]")
        for s in sem_hits:
            body = s.text.replace("\n", " ")
            if len(body) > 60:
                body = body[:57] + "..."
            label = s.label if s.source_type == "document" else s.entry.type_label
            console.print(f"[dim]{s.score:.0%}[/] [cyan]{label}[/] {body}")

    if cap_hits:
        console.print(f"\n[bold]Capturas ({len(cap_hits)})[/]")
        for e in cap_hits:
            console.print(_format_capture_row(e))

    if sess_hits:
        console.print(f"\n[bold]Conversas ({len(sess_hits)})[/]")
        for path, msg in sess_hits:
            snippet = msg.content.replace("\n", " ")
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            console.print(f"[dim]{path.name}[/] [{msg.role}] {snippet}")


def _cmd_memoria(data_dir) -> None:
    profile = list_profile_entries(data_dir)
    any_ = False
    for kind, entries in profile.items():
        if not entries:
            continue
        any_ = True
        console.print(f"\n[bold]{kind}[/]")
        for e in entries:
            console.print(_format_capture_row(e))
    if not any_:
        console.print("[yellow]Sem fatos, prefs ou projetos. Use fato:/pref:/projeto:[/]")


def _cmd_projetos(data_dir) -> None:
    names = list_projects(data_dir)
    if not names:
        console.print("[yellow]Nenhum projeto registrado (projeto: Nome).[/]")
        return
    console.print("[bold]Projetos:[/] " + ", ".join(names))


def _cmd_projeto_ativo(cfg, data_dir, arg: str) -> str:
    """Define ou limpa projeto ativo; retorna cfg atualizado."""
    raw = arg.strip()
    if not raw:
        active = get_active_project(cfg)
        if active:
            console.print(f"[cyan]Projeto ativo:[/] {active}")
        else:
            console.print("[dim]Nenhum projeto ativo. Use: projeto ativo: Nome[/]")
        return cfg
    if raw.lower() in ("limpar", "clear", "off", "nenhum", "-"):
        cfg = set_active_project(data_dir, None)
        console.print("[green]✓[/] Projeto ativo removido.")
        return cfg
    cfg = set_active_project(data_dir, raw)
    console.print(f"[green]✓[/] Projeto ativo: [cyan]{raw}[/]")
    return cfg


def _cmd_relacionados(data_dir, arg: str) -> None:
    raw = arg.strip()
    if not raw:
        recent = list_captures(data_dir, limit=1)
        if not recent:
            console.print("[yellow]Nenhuma captura para relacionar.[/]")
            return
        entries = gather_related(data_dir, entry_id=recent[0].id)
    elif (capture_dir(data_dir) / f"{raw}.md").exists():
        entries = gather_related(data_dir, entry_id=raw)
    else:
        entries = gather_related(data_dir, project=raw)
    console.print(Markdown(format_related_markdown(data_dir, entries)))
    console.print()


def _cmd_liga(data_dir, arg: str) -> None:
    parts = arg.strip().split()
    if len(parts) != 2:
        console.print("[yellow]Uso: !liga id_origem id_destino[/]")
        return
    try:
        add_link(data_dir, parts[0], parts[1])
        console.print(f"[green]✓[/] Ligação: {parts[0]} ↔ {parts[1]}")
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")


def _cmd_web() -> None:
    console.print(
        "[bold]Interface web[/]\n"
        "  pip install -e \".[web]\"\n"
        "  python -m ai_pessoal.web\n"
        "  Abra [link=http://127.0.0.1:8765]http://127.0.0.1:8765[/link]"
    )


def _is_who_am_i(text: str) -> bool:
    low = text.lower().strip().rstrip("?").strip()
    return low in (
        "quem sou eu",
        "quem sou",
        "meu perfil",
        "o que você sabe sobre mim",
        "o que voce sabe sobre mim",
    )


def _cmd_semantico(cfg, data_dir, query: str) -> None:
    q = query.strip()
    if not q:
        console.print("[yellow]Uso: semantico: conceito ou pergunta[/]")
        return
    if not is_semantic_enabled(cfg):
        console.print("[yellow]Ative com !semantico on e rode !indexar[/]")
        return
    hits = search_index(
        data_dir, cfg, q, limit=15, project=get_active_project(cfg)
    )
    if not hits:
        console.print("[yellow]Nada no índice semântico. Rode !indexar[/]")
        return
    for s in hits:
        body = s.text.replace("\n", " ")[:80]
        console.print(f"[dim]{s.score:.0%}[/] [{s.label}] {body}")


def _cmd_indexar(cfg, data_dir) -> None:
    if not is_semantic_enabled(cfg):
        console.print("[yellow]Ative com !semantico on primeiro.[/]")
        return
    model = cfg.get("semantic", {}).get("embed_model", "nomic-embed-text")
    with console.status(f"[cyan]Indexando com {model}…[/]"):
        ok, total = index_all(data_dir, cfg)
        chunks, pdfs = index_all_documents(data_dir, cfg, force=True)
    console.print(
        f"[green]✓[/] {ok}/{total} capturas · {chunks} trechos em {pdfs} PDF(s)."
    )
    console.print(f"[dim]PDFs: {documents_dir(data_dir)}[/]")


def _cmd_docs(data_dir) -> None:
    names = list_document_sources(data_dir)
    folder = documents_dir(data_dir)
    if not names:
        console.print(f"[yellow]Nenhum PDF em[/] {folder}")
        return
    console.print(f"[bold]PDFs ({len(names)}):[/]")
    for name in names:
        console.print(f"  · {name}")


def _cmd_semantico_toggle(cfg, data_dir, arg: str) -> dict:
    raw = arg.strip().lower()
    if raw in ("on", "sim", "true", "1"):
        cfg = set_semantic_search(data_dir, True)
        console.print("[green]✓[/] Busca semântica ativada. Rode !indexar")
    elif raw in ("off", "nao", "não", "false", "0"):
        cfg = set_semantic_search(data_dir, False)
        console.print("[green]✓[/] Busca semântica desativada.")
    else:
        state = "on" if is_semantic_enabled(cfg) else "off"
        console.print(f"Semântica: [cyan]{state}[/] — !semantico on | off")
    return cfg


def _cmd_recuperar(cfg, data_dir, query: str) -> None:
    q = query.strip()
    if not q:
        console.print("[yellow]Ex.: recuperar: marketing · por que decidi X[/]")
        return
    entries, intent, doc_hits = retrieve_for_query(
        data_dir,
        q,
        active_project=get_active_project(cfg),
        cfg=cfg,
    )
    console.print(Markdown(format_retrieval_markdown(entries, intent, doc_hits)))
    console.print()


def _run_chat_ui(cfg, data_dir, session, user_text: str) -> None:
    with console.status("[bold cyan]Pensando…[/]"):
        try:
            reply, sources = run_chat(cfg, data_dir, session, user_text)
        except OllamaError as e:
            console.print(f"[red]{e}[/]")
            return
    console.print()
    console.print(Markdown(reply))
    if sources:
        console.print("[dim]Baseado em:[/]")
        for s in sources[:6]:
            body = s["body"].replace("\n", " ")
            if len(body) > 55:
                body = body[:52] + "…"
            console.print(f"  [dim]·[/] [{s['type']}] {body} [dim]({s['id']})[/]")
    console.print()


def main() -> None:
    cfg, data_dir = load_config()
    ollama = cfg["ollama"]
    model = str(ollama["model_default"])
    question_prefix = str(cfg.get("modes", {}).get("question_prefix", "?"))

    ollama_ok = health_check(str(ollama["base_url"]))
    _print_banner(cfg, data_dir, model, ollama_ok)
    session = start_session(data_dir)

    while True:
        try:
            line = console.input("[bold green]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Até logo.[/]")
            break

        if not line:
            continue

        low = line.lower()
        if low in ("sair", "exit", "quit") or low == "!sair":
            console.print("[dim]Até logo.[/]")
            break

        if low in ("!ajuda", "ajuda", "help"):
            console.print(_help_text())
            continue

        if low == "!web":
            _cmd_web()
            continue

        if low == "!memoria":
            _cmd_memoria(data_dir)
            continue

        if low == "!projetos":
            _cmd_projetos(data_dir)
            continue

        if _is_who_am_i(line):
            console.print(Markdown(format_who_am_i(data_dir)))
            console.print()
            continue

        if low == "!ollama":
            ok = health_check(str(ollama["base_url"]))
            if ok:
                models = list_models(str(ollama["base_url"]))
                console.print("[green]Ollama conectado.[/]")
                if models:
                    console.print("Modelos: " + ", ".join(models[:12]))
            else:
                console.print("[red]Ollama offline.[/]")
            continue

        if low == "!modelo":
            console.print(f"Modelo: [cyan]{model}[/]")
            continue

        if low.startswith("!notas"):
            _cmd_notas(data_dir, line[6:])
            continue

        if low.startswith("!decisoes"):
            _cmd_notas(data_dir, line[9:], kind="decisao")
            continue

        if low.startswith("!aprendizados"):
            _cmd_notas(data_dir, line[13:], kind="aprendi")
            continue

        if low == "!hoje":
            _cmd_hoje(data_dir)
            continue

        if low.startswith("!projeto"):
            cfg = _cmd_projeto_ativo(cfg, data_dir, line[8:])
            continue

        m_ativo = _PROJETO_ATIVO_RE.match(line)
        if m_ativo:
            cfg = _cmd_projeto_ativo(cfg, data_dir, m_ativo.group(1))
            continue

        if low.startswith("!buscar"):
            _cmd_buscar(cfg, data_dir, line[7:])
            continue

        if low.startswith("!relacionados"):
            _cmd_relacionados(data_dir, line[13:])
            continue

        if low.startswith("!liga"):
            _cmd_liga(data_dir, line[5:])
            continue

        m_rel = _RELACIONADOS_RE.match(line)
        if m_rel:
            _cmd_relacionados(data_dir, m_rel.group(1))
            continue

        m_rec = _RECUPERAR_RE.match(line)
        if m_rec:
            _cmd_recuperar(cfg, data_dir, m_rec.group(1))
            continue

        if low.startswith("!recuperar"):
            _cmd_recuperar(cfg, data_dir, line[10:])
            continue

        if low.startswith("!indexar"):
            _cmd_indexar(cfg, data_dir)
            continue

        if low == "!docs":
            _cmd_docs(data_dir)
            continue

        if low.startswith("!semantico"):
            cfg = _cmd_semantico_toggle(cfg, data_dir, line[9:])
            continue

        m_sem = _SEMANTICO_RE.match(line)
        if m_sem:
            _cmd_semantico(cfg, data_dir, m_sem.group(1))
            continue

        m_search = _SEARCH_RE.match(line)
        if m_search:
            _cmd_buscar(cfg, data_dir, m_search.group(1))
            continue

        m_proj = _PROJETO_BUSCA_RE.match(line)
        if m_proj:
            _cmd_buscar(cfg, data_dir, line)
            continue

        parsed = parse_capture_line(line)
        if parsed:
            kind, body = parsed
            if not body:
                console.print("[yellow]Escreva algo após o prefixo.[/]")
                continue
            entry = save_capture(
                data_dir,
                kind,
                body,
                active_project=get_active_project(cfg),
                cfg=cfg,
            )
            console.print(f"[green]✓[/] {entry.type_label} → [dim]{entry.path.name}[/]")
            continue

        if line.startswith(question_prefix):
            user_text = line[len(question_prefix) :].strip()
            if not user_text:
                console.print("[yellow]Escreva a pergunta após ?[/]")
                continue
            _run_chat_ui(cfg, data_dir, session, user_text)
            continue

        _run_chat_ui(cfg, data_dir, session, line)


if __name__ == "__main__":
    main()
