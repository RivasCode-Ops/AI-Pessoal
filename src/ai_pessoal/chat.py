from __future__ import annotations

from pathlib import Path
from typing import Any  # noqa: TC003 — used in compose_system_prompt

from ai_pessoal.config import get_active_project
from ai_pessoal.memory import build_memory_context
from ai_pessoal.recover import RetrievalIntent, format_context_block, retrieve_for_query
from ai_pessoal.capture import CaptureEntry
from ai_pessoal.ollama_client import OllamaError, chat, health_check
from ai_pessoal.session import ChatSession


def compose_system_prompt(
    base: str,
    data_dir: Path,
    user_query: str,
    *,
    entries: list[CaptureEntry] | None = None,
    intent: RetrievalIntent | None = None,
    active_project: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> str:
    blocks = [base.strip()]
    mem = build_memory_context(data_dir)
    if mem:
        blocks.append(mem)
    if entries is None:
        entries, intent = retrieve_for_query(
            data_dir,
            user_query,
            limit=8,
            active_project=active_project,
            cfg=cfg,
        )
    rel = format_context_block(entries, intent)
    if rel:
        blocks.append(rel)
    if active_project:
        blocks.append(f"Filtro: projeto ativo «{active_project}».")
    blocks.append(
        "Regras: use apenas o contexto acima sobre o usuário. "
        "Se não houver dado, diga que não está registrado. Não invente biografia."
    )
    return "\n\n".join(blocks)


def run_chat(
    cfg: dict[str, Any],
    data_dir: Path,
    session: ChatSession,
    user_text: str,
) -> tuple[str, list[dict[str, str]]]:
    ollama = cfg["ollama"]
    chat_cfg = cfg["chat"]
    base = str(ollama["base_url"])
    model = str(ollama["model_default"])
    timeout = float(ollama.get("timeout_seconds", 120))
    temp = float(chat_cfg.get("temperature", 0.7))
    max_hist = int(chat_cfg.get("max_history_messages", 20))
    base_system = str(chat_cfg.get("system_prompt", ""))

    if not health_check(base):
        raise OllamaError(
            "Ollama não está acessível. Inicie com 'ollama serve' ou ajuste config.json."
        )

    active = get_active_project(cfg)
    entries, intent = retrieve_for_query(
        data_dir, user_text, limit=8, active_project=active, cfg=cfg
    )
    system = compose_system_prompt(
        base_system,
        data_dir,
        user_text,
        entries=entries,
        intent=intent,
        active_project=active,
        cfg=cfg,
    )
    session.append("user", user_text)
    messages = [{"role": "system", "content": system}]
    messages.extend(session.recent_for_api(max_hist))

    reply = chat(base, model, messages, temperature=temp, timeout=timeout)
    session.append("assistant", reply)
    source_items = [
        {"id": e.id, "type": e.type_label, "body": e.body[:200]}
        for e in entries
    ]
    return reply, source_items
