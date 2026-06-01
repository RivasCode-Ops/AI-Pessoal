from __future__ import annotations

import re

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ai_pessoal import __version__
from ai_pessoal.capture import capture_dir, list_captures, parse_capture_line, save_capture, search_captures
from ai_pessoal.relate import add_link, format_related_markdown, gather_related
from ai_pessoal.chat import run_chat
from ai_pessoal.config import load_config
from ai_pessoal.memory import format_who_am_i, list_profile_entries, list_projects
from ai_pessoal.ollama_client import OllamaError, health_check, list_models
from ai_pessoal.session import ChatSession, search_sessions, start_session

console = Console()

_SEARCH_RE = re.compile(r"^buscar\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)
_PROJETO_BUSCA_RE = re.compile(r"^projeto\s*:\s*(.+)$", re.IGNORECASE)
_RELACIONADOS_RE = re.compile(r"^relacionados\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)


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

[bold]Conversa[/]
  ? pergunta
  ou texto livre (usa memória + trechos relevantes)

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


def _print_banner(data_dir, model: str, ollama_ok: bool) -> None:
    status = "[green]Ollama OK[/]" if ollama_ok else "[red]Ollama offline[/]"
    n = len(list_captures(data_dir, limit=500))
    console.print(
        Panel(
            f"[bold]AI-Pessoal[/] v{__version__} — segundo cérebro local\n"
            f"Dados: [dim]{data_dir}[/]\n"
            f"Modelo: [cyan]{model}[/] · {status} · [dim]{n} capturas[/]",
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


def _cmd_buscar(data_dir, query: str) -> None:
    q, project = _parse_buscar_query(query)
    if not q and not project:
        console.print("[yellow]Uso: buscar: termo  |  projeto: Nome  |  !buscar termo[/]")
        return

    cap_hits = search_captures(data_dir, q, project=project)
    sess_hits = search_sessions(data_dir, q) if q else []

    label = project or q
    if not cap_hits and not sess_hits:
        console.print(f"[yellow]Nada encontrado para «{label}».[/]")
        return

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


def _run_chat_ui(cfg, data_dir, session, user_text: str) -> None:
    with console.status("[bold cyan]Pensando…[/]"):
        try:
            reply = run_chat(cfg, data_dir, session, user_text)
        except OllamaError as e:
            console.print(f"[red]{e}[/]")
            return
    console.print()
    console.print(Markdown(reply))
    console.print()


def main() -> None:
    cfg, data_dir = load_config()
    ollama = cfg["ollama"]
    model = str(ollama["model_default"])
    question_prefix = str(cfg.get("modes", {}).get("question_prefix", "?"))

    ollama_ok = health_check(str(ollama["base_url"]))
    _print_banner(data_dir, model, ollama_ok)
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

        if low.startswith("!buscar"):
            _cmd_buscar(data_dir, line[7:])
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

        m_search = _SEARCH_RE.match(line)
        if m_search:
            _cmd_buscar(data_dir, m_search.group(1))
            continue

        m_proj = _PROJETO_BUSCA_RE.match(line)
        if m_proj:
            _cmd_buscar(data_dir, line)
            continue

        parsed = parse_capture_line(line)
        if parsed:
            kind, body = parsed
            if not body:
                console.print("[yellow]Escreva algo após o prefixo.[/]")
                continue
            entry = save_capture(data_dir, kind, body)
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
