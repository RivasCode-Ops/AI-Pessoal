from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_pessoal.capture import (
    CaptureEntry,
    _read_frontmatter,
    capture_dir,
    list_captures,
    load_capture,
)
from ai_pessoal.config import is_semantic_enabled
from ai_pessoal.ollama_client import OllamaError, embed_text


@dataclass
class ScoredHit:
    hit_id: str
    score: float
    source_type: str  # capture | document
    label: str
    text: str
    entry: CaptureEntry | None = None
    document: str | None = None


# Compatibilidade com código que usa ScoredEntry
@dataclass
class ScoredEntry:
    entry: CaptureEntry
    score: float


def embed_model(cfg: dict[str, Any]) -> str:
    return str(cfg.get("semantic", {}).get("embed_model", "nomic-embed-text"))


def min_score(cfg: dict[str, Any]) -> float:
    return float(cfg.get("semantic", {}).get("min_score", 0.35))


def chunk_settings(cfg: dict[str, Any]) -> tuple[int, int]:
    doc = cfg.get("documents", {})
    size = int(doc.get("chunk_chars", cfg.get("semantic", {}).get("chunk_chars", 900)))
    overlap = int(doc.get("chunk_overlap", cfg.get("semantic", {}).get("chunk_overlap", 120)))
    return max(200, size), max(0, overlap)


def index_path(data_dir: Path) -> Path:
    p = data_dir / "data" / "embeddings" / "vectors.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def entry_embed_text(entry: CaptureEntry) -> str:
    meta, _ = _read_frontmatter(entry.path)
    parts = [entry.type_label, entry.body]
    for key in ("projeto", "motivo", "risco", "fonte"):
        val = meta.get(key, "").strip()
        if val:
            parts.append(f"{key}: {val}")
    return "\n".join(parts).strip()


def _entry_project(entry: CaptureEntry) -> str:
    meta, _ = _read_frontmatter(entry.path)
    p = meta.get("projeto", "").strip()
    if p:
        return p
    if entry.type == "projeto":
        return entry.body.strip().split("\n")[0].strip()
    return ""


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_cosine = cosine_similarity


def load_all_index_rows(data_dir: Path, model: str) -> dict[str, dict[str, Any]]:
    path = index_path(data_dir)
    if not path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("model", "")) != model:
            continue
        row_id = str(row.get("id", ""))
        if row_id:
            rows[row_id] = row
    return rows


def save_index_rows(data_dir: Path, rows: dict[str, dict[str, Any]]) -> None:
    path = index_path(data_dir)
    lines = [json.dumps(rows[k], ensure_ascii=False) for k in sorted(rows)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


_load_index_rows = load_all_index_rows
_write_index_rows = save_index_rows


def index_entry(
    data_dir: Path,
    cfg: dict[str, Any],
    entry: CaptureEntry,
    *,
    force: bool = False,
) -> bool:
    if not is_semantic_enabled(cfg):
        return False
    model = embed_model(cfg)
    base = str(cfg["ollama"]["base_url"])
    timeout = float(cfg["ollama"].get("timeout_seconds", 120))
    mtime = entry.path.stat().st_mtime
    rows = load_all_index_rows(data_dir, model)
    prev = rows.get(entry.id)
    if not force and prev and float(prev.get("mtime", 0)) == mtime:
        return False

    text = entry_embed_text(entry)
    if not text:
        return False
    try:
        vector = embed_text(base, model, text, timeout=timeout)
    except OllamaError:
        return False

    rows[entry.id] = {
        "id": entry.id,
        "kind": "capture",
        "model": model,
        "mtime": mtime,
        "vector": vector,
        "projeto": _entry_project(entry),
    }
    save_index_rows(data_dir, rows)
    return True


def index_all(data_dir: Path, cfg: dict[str, Any]) -> tuple[int, int]:
    entries = list_captures(data_dir, limit=10_000)
    ok = 0
    for entry in entries:
        if index_entry(data_dir, cfg, entry, force=True):
            ok += 1
    return ok, len(entries)


def search_index(
    data_dir: Path,
    cfg: dict[str, Any],
    query: str,
    *,
    limit: int = 10,
    project: str | None = None,
    kind: str | None = None,
) -> list[ScoredHit]:
    if not is_semantic_enabled(cfg):
        return []
    q = query.strip()
    if not q:
        return []

    model = embed_model(cfg)
    base = str(cfg["ollama"]["base_url"])
    timeout = float(cfg["ollama"].get("timeout_seconds", 120))
    threshold = min_score(cfg)

    try:
        qvec = embed_text(base, model, q, timeout=timeout)
    except OllamaError:
        return []

    rows = load_all_index_rows(data_dir, model)
    if not rows:
        return []

    proj = (project or "").strip().lower()
    scored: list[ScoredHit] = []

    for row_id, row in rows.items():
        vec = row.get("vector")
        if not isinstance(vec, list):
            continue
        score = cosine_similarity(qvec, [float(x) for x in vec])
        if score < threshold:
            continue

        row_kind = str(row.get("kind", "capture"))
        if row_kind == "document":
            source = str(row.get("source", "documento"))
            text = str(row.get("text", ""))
            chunk_i = int(row.get("chunk_index", 0))
            scored.append(
                ScoredHit(
                    hit_id=row_id,
                    score=score,
                    source_type="document",
                    label=f"PDF {source} §{chunk_i + 1}",
                    text=text,
                    document=source,
                )
            )
            continue

        path = capture_dir(data_dir) / f"{row_id}.md"
        if not path.exists():
            continue
        try:
            entry = load_capture(path)
        except OSError:
            continue
        if kind and entry.type != kind:
            continue
        if proj:
            ep = _entry_project(entry).lower()
            blob = entry_embed_text(entry).lower()
            if proj not in ep.lower() and proj not in blob:
                if entry.type != "projeto" or proj not in entry.body.lower():
                    continue
        scored.append(
            ScoredHit(
                hit_id=row_id,
                score=score,
                source_type="capture",
                label=entry.type_label,
                text=entry.body,
                entry=entry,
            )
        )

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:limit]


def semantic_search(
    data_dir: Path,
    cfg: dict[str, Any],
    query: str,
    *,
    limit: int = 10,
    project: str | None = None,
    kind: str | None = None,
) -> list[ScoredEntry]:
    """Compat: retorna só capturas."""
    hits = search_index(data_dir, cfg, query, limit=limit, project=project, kind=kind)
    out: list[ScoredEntry] = []
    for h in hits:
        if h.entry is not None:
            out.append(ScoredEntry(entry=h.entry, score=h.score))
    return out


def format_hits_for_context(hits: list[ScoredHit], *, max_chars: int = 400) -> str:
    if not hits:
        return ""
    lines = ["Trechos semânticos (capturas + PDFs):"]
    for h in hits:
        body = h.text.replace("\n", " ")
        if len(body) > max_chars:
            body = body[: max_chars - 3] + "..."
        if h.source_type == "document":
            lines.append(f"- [{h.label}] {body}")
        else:
            lines.append(f"- [{h.label}] {body} (id: {h.hit_id})")
    return "\n".join(lines)


def try_index_after_save(data_dir: Path, cfg: dict[str, Any], entry: CaptureEntry) -> None:
    try:
        index_entry(data_dir, cfg, entry)
    except OSError:
        pass
