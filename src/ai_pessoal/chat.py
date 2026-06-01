from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_pessoal.memory import build_memory_context, build_relevant_context
from ai_pessoal.ollama_client import OllamaError, chat, health_check
from ai_pessoal.session import ChatSession


def compose_system_prompt(base: str, data_dir: Path, user_query: str) -> str:
    blocks = [base.strip()]
    mem = build_memory_context(data_dir)
    if mem:
        blocks.append(mem)
    rel = build_relevant_context(data_dir, user_query)
    if rel:
        blocks.append(rel)
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
) -> str:
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

    system = compose_system_prompt(base_system, data_dir, user_text)
    session.append("user", user_text)
    messages = [{"role": "system", "content": system}]
    messages.extend(session.recent_for_api(max_hist))

    reply = chat(base, model, messages, temperature=temp, timeout=timeout)
    session.append("assistant", reply)
    return reply
