from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ai_pessoal.capture import (
    CaptureEntry,
    _read_frontmatter,
    capture_dir,
    load_capture,
    search_captures,
)


@dataclass
class Link:
    source: str
    target: str
    relation: str
    created: str


def links_path(data_dir: Path) -> Path:
    p = data_dir / "data" / "links" / "links.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def add_link(
    data_dir: Path,
    source_id: str,
    target_id: str,
    relation: str = "relaciona",
) -> None:
    if source_id == target_id:
        return
    if not (capture_dir(data_dir) / f"{source_id}.md").exists():
        raise FileNotFoundError(f"Captura não encontrada: {source_id}")
    if not (capture_dir(data_dir) / f"{target_id}.md").exists():
        raise FileNotFoundError(f"Captura não encontrada: {target_id}")

    row = {
        "source": source_id,
        "target": target_id,
        "relation": relation,
        "created": datetime.now().astimezone().isoformat(),
    }
    with links_path(data_dir).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_links(data_dir: Path) -> list[Link]:
    path = links_path(data_dir)
    if not path.exists():
        return []
    out: list[Link] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            out.append(
                Link(
                    source=str(row["source"]),
                    target=str(row["target"]),
                    relation=str(row.get("relation", "relaciona")),
                    created=str(row.get("created", "")),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return out


def neighbors(data_dir: Path, entry_id: str) -> set[str]:
    linked: set[str] = set()
    for link in load_links(data_dir):
        if link.source == entry_id:
            linked.add(link.target)
        if link.target == entry_id:
            linked.add(link.source)
    return linked


def _meta_projeto(data_dir: Path, entry: CaptureEntry) -> str | None:
    meta, _ = _read_meta(entry.path)
    p = meta.get("projeto", "").strip()
    if p:
        return p
    if entry.type == "projeto":
        return entry.body.strip().split("\n")[0].strip() or None
    return None


def _read_meta(path: Path) -> tuple[dict[str, str], str]:
    return _read_frontmatter(path)


def by_project(data_dir: Path, project: str, *, limit: int = 25) -> list[CaptureEntry]:
    proj = project.strip().lower()
    if not proj:
        return []
    hits: list[CaptureEntry] = []
    folder = capture_dir(data_dir)
    if not folder.exists():
        return hits
    for path in sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            entry = load_capture(path)
            meta, _ = _read_meta(path)
        except OSError:
            continue
        blob = f"{entry.body} {meta.get('projeto', '')} {entry.type}".lower()
        if entry.type == "projeto" and proj in entry.body.lower():
            hits.append(entry)
        elif proj in blob:
            hits.append(entry)
        if len(hits) >= limit:
            break
    return hits


def gather_related(
    data_dir: Path,
    *,
    entry_id: str | None = None,
    project: str | None = None,
    query: str | None = None,
    limit: int = 20,
) -> list[CaptureEntry]:
    """Relacionar: links explícitos + mesmo projeto + busca textual opcional."""
    seen: set[str] = set()
    ordered: list[CaptureEntry] = []

    def add(entry: CaptureEntry | None) -> None:
        if entry is None or entry.id in seen:
            return
        seen.add(entry.id)
        ordered.append(entry)

    if entry_id:
        base = _load_id(data_dir, entry_id)
        if base:
            proj = _meta_projeto(data_dir, base)
            for nid in neighbors(data_dir, entry_id):
                add(_load_id(data_dir, nid))
            add(base)
            if proj:
                for e in by_project(data_dir, proj, limit=limit):
                    add(e)

    if project:
        for e in by_project(data_dir, project, limit=limit):
            add(e)

    if query:
        for e in search_captures(data_dir, query, limit=limit):
            add(e)

    return ordered[:limit]


def _load_id(data_dir: Path, entry_id: str) -> CaptureEntry | None:
    path = capture_dir(data_dir) / f"{entry_id}.md"
    if not path.exists():
        return None
    return load_capture(path)


def format_related_markdown(data_dir: Path, entries: list[CaptureEntry]) -> str:
    if not entries:
        return "Nenhuma entrada relacionada encontrada."
    lines = ["# Relacionados\n"]
    for e in entries:
        ts = e.created.strftime("%d/%m/%Y %H:%M")
        proj = _meta_projeto(data_dir, e)
        extra = f" · projeto:{proj}" if proj else ""
        body = e.body.replace("\n", " ")[:120]
        lines.append(f"- **{e.id}** [{e.type_label}] {ts}{extra}\n  {body}")
    return "\n".join(lines)
