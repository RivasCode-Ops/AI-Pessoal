from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ChatMessage:
    role: str
    content: str
    ts: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())

    def to_api(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatSession:
    session_id: str
    path: Path
    messages: list[ChatMessage] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"role": msg.role, "content": msg.content, "ts": msg.ts}, ensure_ascii=False))
            f.write("\n")

    def recent_for_api(self, max_messages: int) -> list[dict[str, str]]:
        return [m.to_api() for m in self.messages[-max_messages:]]


def sessions_dir(data_dir: Path) -> Path:
    return data_dir / "data" / "sessions"


def start_session(data_dir: Path) -> ChatSession:
    sessions_dir(data_dir).mkdir(parents=True, exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    path = sessions_dir(data_dir) / f"{session_id}.jsonl"
    path.touch()
    return ChatSession(session_id=session_id, path=path)


def load_session(path: Path) -> ChatSession:
    messages: list[ChatMessage] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row: dict[str, Any] = json.loads(line)
                messages.append(
                    ChatMessage(
                        role=str(row.get("role", "user")),
                        content=str(row.get("content", "")),
                        ts=str(row.get("ts", "")),
                    )
                )
            except json.JSONDecodeError:
                continue
    return ChatSession(session_id=path.stem, path=path, messages=messages)


def search_sessions(data_dir: Path, query: str, limit: int = 10) -> list[tuple[Path, ChatMessage]]:
    q = query.strip().lower()
    if not q:
        return []
    folder = sessions_dir(data_dir)
    if not folder.exists():
        return []

    hits: list[tuple[Path, ChatMessage]] = []
    for path in sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        session = load_session(path)
        for msg in reversed(session.messages):
            if q in msg.content.lower():
                hits.append((path, msg))
                break
        if len(hits) >= limit:
            break
    return hits
