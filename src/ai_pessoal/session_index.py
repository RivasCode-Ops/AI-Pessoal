from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_pessoal.config import is_semantic_enabled
from ai_pessoal.ollama_client import OllamaError, embed_text
from ai_pessoal.semantic import embed_model, load_all_index_rows, save_index_rows
from ai_pessoal.session import load_session, sessions_dir


def message_row_id(session_id: str, index: int) -> str:
    return f"sess:{session_id}:{index:04d}"


def _message_embed_text(session_id: str, role: str, content: str) -> str:
    return f"Conversa {session_id}\n{role}: {content}"


def index_session_file(
    data_dir: Path,
    cfg: dict[str, Any],
    path: Path,
    *,
    force: bool = False,
) -> int:
    if not is_semantic_enabled(cfg):
        return 0

    model = embed_model(cfg)
    base = str(cfg["ollama"]["base_url"])
    timeout = float(cfg["ollama"].get("timeout_seconds", 120))
    mtime = path.stat().st_mtime
    session = load_session(path)
    if not session.messages:
        return 0

    rows = load_all_index_rows(data_dir, model)
    prefix = f"sess:{session.session_id}:"

    if not force:
        sample_key = f"{prefix}0000"
        if sample_key in rows:
            row = rows[sample_key]
            if (
                row.get("kind") == "session"
                and row.get("source") == path.name
                and float(row.get("mtime", 0)) == mtime
                and int(row.get("message_count", 0)) == len(session.messages)
            ):
                return 0

    for key in list(rows):
        if key.startswith(prefix):
            del rows[key]

    indexed = 0
    for i, msg in enumerate(session.messages):
        text = _message_embed_text(session.session_id, msg.role, msg.content)
        if not text.strip():
            continue
        try:
            vector = embed_text(base, model, text, timeout=timeout)
        except OllamaError:
            break
        rid = message_row_id(session.session_id, i)
        rows[rid] = {
            "id": rid,
            "kind": "session",
            "source": path.name,
            "session_id": session.session_id,
            "role": msg.role,
            "text": msg.content,
            "message_index": i,
            "message_count": len(session.messages),
            "model": model,
            "mtime": mtime,
            "vector": vector,
        }
        indexed += 1

    save_index_rows(data_dir, rows)
    return indexed


def index_session_tail(
    data_dir: Path,
    cfg: dict[str, Any],
    path: Path,
    *,
    tail: int = 4,
) -> int:
    """Indexa só as últimas mensagens (rápido após cada turno de chat)."""
    if not is_semantic_enabled(cfg):
        return 0
    if not cfg.get("semantic", {}).get("auto_index_on_chat", True):
        return 0

    model = embed_model(cfg)
    base = str(cfg["ollama"]["base_url"])
    timeout = float(cfg["ollama"].get("timeout_seconds", 120))
    session = load_session(path)
    if not session.messages:
        return 0

    rows = load_all_index_rows(data_dir, model)
    mtime = path.stat().st_mtime
    start = max(0, len(session.messages) - tail)
    indexed = 0

    for i in range(start, len(session.messages)):
        msg = session.messages[i]
        text = _message_embed_text(session.session_id, msg.role, msg.content)
        if not text.strip():
            continue
        rid = message_row_id(session.session_id, i)
        prev = rows.get(rid)
        if prev and prev.get("text") == msg.content and float(prev.get("mtime", 0)) == mtime:
            continue
        try:
            vector = embed_text(base, model, text, timeout=timeout)
        except OllamaError:
            break
        rows[rid] = {
            "id": rid,
            "kind": "session",
            "source": path.name,
            "session_id": session.session_id,
            "role": msg.role,
            "text": msg.content,
            "message_index": i,
            "message_count": len(session.messages),
            "model": model,
            "mtime": mtime,
            "vector": vector,
        }
        indexed += 1

    if indexed:
        save_index_rows(data_dir, rows)
    return indexed


def try_index_after_chat(data_dir: Path, cfg: dict[str, Any], session_path: Path) -> None:
    try:
        index_session_tail(data_dir, cfg, session_path)
    except OSError:
        pass


def index_all_sessions(data_dir: Path, cfg: dict[str, Any], *, force: bool = True) -> tuple[int, int]:
    folder = sessions_dir(data_dir)
    if not folder.exists():
        return 0, 0
    files = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    total_msgs = 0
    for path in files:
        total_msgs += index_session_file(data_dir, cfg, path, force=force)
    return total_msgs, len(files)
