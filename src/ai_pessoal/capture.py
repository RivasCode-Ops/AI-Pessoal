from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

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


def _parse_meta_from_body(kind: str, body: str) -> tuple[str, dict[str, str]]:
    """Extrai projeto: / Motivo: / Risco: / Fonte: do corpo quando presentes."""
    extra: dict[str, str] = {}
    lines = body.strip().splitlines()
    kept: list[str] = []
    for line in lines:
        low = line.strip().lower()
        if low.startswith("projeto:") and "projeto" not in extra:
            extra["projeto"] = line.split(":", 1)[1].strip()
            continue
        if kind == "decisao":
            if low.startswith("motivo:"):
                extra["motivo"] = line.split(":", 1)[1].strip()
                continue
            if low.startswith("risco:"):
                extra["risco"] = line.split(":", 1)[1].strip()
                continue
        if kind == "aprendi" and low.startswith("fonte:"):
            extra["fonte"] = line.split(":", 1)[1].strip()
            continue
        if low.startswith("ref:") or low.startswith("liga:") or low.startswith("relaciona:"):
            key = low.split(":", 1)[0]
            extra[key] = line.split(":", 1)[1].strip()
            continue
        kept.append(line)
    clean = "\n".join(kept).strip() or body.strip()
    return clean, extra


def save_capture(
    data_dir: Path,
    kind: str,
    body: str,
    *,
    active_project: str | None = None,
    cfg: dict[str, Any] | None = None,
) -> CaptureEntry:
    if kind not in CAPTURE_TYPES:
        raise ValueError(f"Tipo inválido: {kind}")

    clean_body, extra = _parse_meta_from_body(kind, body)
    if active_project and kind != "projeto" and "projeto" not in extra:
        extra["projeto"] = active_project
    now = datetime.now().astimezone()
    entry_id = now.strftime("%Y%m%d-%H%M%S") + f"-{kind}"
    folder = capture_dir(data_dir)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{entry_id}.md"

    fm_lines = [f"type: {kind}", f"created: {now.isoformat()}"]
    for key, val in extra.items():
        fm_lines.append(f"{key}: {val}")
    frontmatter = "---\n" + "\n".join(fm_lines) + "\n---\n\n"
    dest.write_text(frontmatter + clean_body + "\n", encoding="utf-8")
    entry = CaptureEntry(id=entry_id, type=kind, body=clean_body, created=now, path=dest)
    _apply_links_from_meta(data_dir, entry_id, extra)
    if cfg is not None:
        from ai_pessoal.semantic import try_index_after_save

        try_index_after_save(data_dir, cfg, entry)
    return entry


def _apply_links_from_meta(data_dir: Path, entry_id: str, extra: dict[str, str]) -> None:
    from ai_pessoal.relate import add_link

    for key in ("ref", "liga", "relaciona"):
        target = extra.get(key, "").strip()
        if target:
            try:
                add_link(data_dir, entry_id, target, relation=key)
            except FileNotFoundError:
                pass


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


def _entry_search_blob(entry: CaptureEntry, meta: dict[str, str]) -> str:
    parts = [entry.type, entry.body, entry.id]
    parts.extend(meta.values())
    return " ".join(parts).lower()


def search_captures(
    data_dir: Path,
    query: str,
    limit: int = 15,
    *,
    project: str | None = None,
    kind: str | None = None,
) -> list[CaptureEntry]:
    q = query.strip().lower()
    proj = (project or "").strip().lower()
    hits: list[CaptureEntry] = []
    folder = capture_dir(data_dir)
    if not folder.exists():
        return hits
    if not q and not proj:
        return hits

    for path in sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            meta, _ = _read_frontmatter(path)
            entry = load_capture(path)
        except OSError:
            continue
        if kind and entry.type != kind:
            continue
        blob = _entry_search_blob(entry, meta)
        if proj and proj not in blob:
            if entry.type != "projeto" or proj not in entry.body.lower():
                continue
        if q and q not in blob:
            continue
        hits.append(entry)
        if len(hits) >= limit:
            break
    return hits
