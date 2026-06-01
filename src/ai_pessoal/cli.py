from __future__ import annotations

import re
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from ai_pessoal import __version__
from ai_pessoal.capture import list_captures, parse_capture_line, save_capture, search_captures
from ai_pessoal.config import load_config
from ai_pessoal.ollama_client import OllamaError, chat, health_check, list_models
from ai_pessoal.session import ChatSession, search_sessions, start_session

console = Console()

_SEARCH_RE = re.compile(r"^buscar\s*:\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _help_text() -> str:
    return """
[bold]Captura[/] (sem IA, grava na hora)
  nota: texto
  ideia: texto
  decisão: texto
  fato: / pref: / projeto: / aprendi:  (memória — semana 3+)

[bold]Conversa[/]
  ? sua pergunta
  ou qualquer linha que não seja captura/comando

[bold]Comandos[/]
  !ajuda          esta ajuda
  !sair           encerrar
  !notas [n]      últimas capturas (padrão 10)
  !hoje           capturas de hoje
  !buscar termo   busca textual (ou buscar: termo)
  !modelo         modelo Ollama atual
  !ollama         testar conexão Ollama
"""


def _print_banner(data_dir, model: str, ollama_ok: bool) -> None:
    status = "[green]Ollama OK[/]" if ollama_ok else "[red]Ollama offline[/]"
    console.print(
        Panel(
            f"[bold]AI-Pessoal[/] v{__version__} — segundo cérebro local\n"
            f"Dados: [dim]{data_dir}[/]\n"
            f"Modelo: [cyan]{model}[/] · {status}",
            border_style="blue",
        )
    )
    console.print("[dim]Captura: nota: / ideia: / decisão:  ·  Conversa: ?texto  ·  !ajuda[/]\n")


def _format_capture_row(entry) -> str:
    ts = entry.created.strftime("%d/%m %H:%M")
    body = entry.body.replace("\n", " ")
    if len(body) > 70:
        body = body[:67] + "..."
    return f"[dim]{ts}[/] [cyan]{entry.type_label}[/] {body}"


def _cmd_notas(data_dir, arg: str) -> None:
    limit = 10
    if arg.strip().isdigit():
        limit = max(1, min(50, int(arg.strip())))
    entries = list_captures(data_dir, limit=limit)
    if not entries:
        console.print("[yellow]Nenhuma captura ainda.[/]")
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
    q = query.strip()
    if not q:
        console.print("[yellow]Uso: buscar: termo  ou  !buscar termo[/]")
        return

    cap_hits = search_captures(data_dir, q)
    sess_hits = search_sessions(data_dir, q)

    if not cap_hits and not sess_hits:
        console.print(f"[yellow]Nada encontrado para «{q}».[/]")
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


def _run_chat(
    cfg: dict,
    session: ChatSession,
    user_text: str,
) -> None:
    ollama = cfg["ollama"]
    chat_cfg = cfg["chat"]
    base = str(ollama["base_url"])
    model = str(ollama["model_default"])
    timeout = float(ollama.get("timeout_seconds", 120))
    temp = float(chat_cfg.get("temperature", 0.7))
    max_hist = int(chat_cfg.get("max_history_messages", 20))
    system = str(chat_cfg.get("system_prompt", ""))

    if not health_check(base):
        console.print(
            "[red]Ollama não está acessível.[/] Inicie com [bold]ollama serve[/] "
            "ou ajuste [dim]config.json[/]."
        )
        return

    session.append("user", user_text)
    messages = [{"role": "system", "content": system}]
    messages.extend(session.recent_for_api(max_hist))

    with console.status("[bold cyan]Pensando…[/]"):
        try:
            reply = chat(base, model, messages, temperature=temp, timeout=timeout)
        except OllamaError as e:
            console.print(f"[red]{e}[/]")
            return

    session.append("assistant", reply)
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
            console.print(f"Modelo configurado: [cyan]{model}[/]")
            continue

        if low.startswith("!notas"):
            _cmd_notas(data_dir, line[6:])
            continue

        if low == "!hoje":
            _cmd_hoje(data_dir)
            continue

        if low.startswith("!buscar"):
            _cmd_buscar(data_dir, line[7:])
            continue

        m_search = _SEARCH_RE.match(line)
        if m_search:
            _cmd_buscar(data_dir, m_search.group(1))
            continue

        parsed = parse_capture_line(line)
        if parsed:
            kind, body = parsed
            if not body:
                console.print("[yellow]Escreva algo após o prefixo.[/]")
                continue
            entry = save_capture(data_dir, kind, body)
            console.print(
                f"[green]✓[/] {entry.type_label} gravada "
                f"[dim]({entry.path.name})[/]"
            )
            continue

        if line.startswith(question_prefix):
            user_text = line[len(question_prefix) :].strip()
            if not user_text:
                console.print("[yellow]Escreva a pergunta após ?[/]")
                continue
            _run_chat(cfg, session, user_text)
            continue

        _run_chat(cfg, session, line)


if __name__ == "__main__":
    main()
