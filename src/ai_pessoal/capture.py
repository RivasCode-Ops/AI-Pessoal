from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

# Semana 1: nota, ideia, decisão. Semana 3+: demais tipos já aceitos na captura.
CAPTURE_TYPES = frozenset(
    {"nota", "ideia", "decisao", "fato", "pref", "projeto", "aprendi"}
)

PREFIX_ALIASES: dict[str, str] = {
    "nota": "nota",
    "ideia": "ideia",
    "decisão": "decisao",
    "decisao": "decisao",
    "fato": "fato",
    "pref": "pref",
    "preferência": "pref",
    "preferencia": "pref",
    "projeto": "projeto",
    "aprendi": "aprendi",
}

_PREFIX_RE = re.compile(
    r"^(" + "|".join(re.escape(k) for k in PREFIX_ALIASES) + r")\s*:\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class CaptureEntry:
    id: str
    type: str
    body: str
    created: datetime
    path: Path

    @property
    def type_label(self) -> str:
        labels = {
            "nota": "nota",
            "ideia": "ideia",
            "decisao": "decisão",
            "fato": "fato",
            "pref": "pref",
            "projeto": "projeto",
            "aprendi": "aprendi",
        }
        return labels.get(self.type, self.type)


def parse_capture_line(line: str) -> tuple[str, str] | None:
    m = _PREFIX_RE.match(line.strip())
    if not m:
        return None
    raw_type, body = m.group(1), m.group(2).strip()
    key = raw_type.lower()
    if key not in PREFIX_ALIASES:
        return None
    return PREFIX_ALIASES[key], body


def capture_dir(data_dir: Path) -> Path:
    return data_dir / "data" / "capture"


def save_capture(data_dir: Path, kind: str, body: str) -> CaptureEntry:
    if kind not in CAPTURE_TYPES:
        raise ValueError(f"Tipo inválido: {kind}")

    now = datetime.now().astimezone()
    entry_id = now.strftime("%Y%m%d-%H%M%S") + f"-{kind}"
    dest = capture_dir(data_dir) / f"{entry_id}.md"
    content = (
        f"---\n"
        f"type: {kind}\n"
        f"created: {now.isoformat()}\n"
        f"---\n\n"
        f"{body.strip()}\n"
    )
    dest.write_text(content, encoding="utf-8")
    return CaptureEntry(id=entry_id, type=kind, body=body.strip(), created=now, path=dest)


def _read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, parts[2].strip()


def load_capture(path: Path) -> CaptureEntry:
    meta, body = _read_frontmatter(path)
    created_raw = meta.get("created", "")
    try:
        created = datetime.fromisoformat(created_raw)
    except ValueError:
        created = datetime.fromtimestamp(path.stat().st_mtime)
    kind = meta.get("type", "nota")
    return CaptureEntry(
        id=path.stem,
        type=kind,
        body=body,
        created=created,
        path=path,
    )


def list_captures(
    data_dir: Path,
    *,
    limit: int = 20,
    kind: str | None = None,
    today_only: bool = False,
) -> list[CaptureEntry]:
    folder = capture_dir(data_dir)
    if not folder.exists():
        return []

    entries: list[CaptureEntry] = []
    for path in sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            entry = load_capture(path)
        except OSError:
            continue
        if kind and entry.type != kind:
            continue
        if today_only and entry.created.date() != date.today():
            continue
        entries.append(entry)
        if len(entries) >= limit:
            break
    return entries


def search_captures(data_dir: Path, query: str, limit: int = 15) -> list[CaptureEntry]:
    q = query.strip().lower()
    if not q:
        return []
    hits: list[CaptureEntry] = []
    folder = capture_dir(data_dir)
    if not folder.exists():
        return hits

    for path in sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            entry = load_capture(path)
        except OSError:
            continue
        hay = f"{entry.type} {entry.body}".lower()
        if q in hay or q in entry.id.lower():
            hits.append(entry)
        if len(hits) >= limit:
            break
    return hits
