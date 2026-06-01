from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ai_pessoal.capture import CaptureEntry, _read_frontmatter, search_captures
from ai_pessoal.relate import gather_related

_PROJECT_TAIL_RE = re.compile(r"\s+no\s+projeto\s+(.+)$", re.IGNORECASE)

_INTENT_PATTERNS: list[tuple[re.Pattern[str], str | None, int]] = [
    (
        re.compile(
            r"(?:por\s*que|porque)\s+(?:eu\s+)?decidi(?:\s+sobre)?\s+(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        "decisao",
        1,
    ),
    (
        re.compile(
            r"(?:minhas?\s+)?decis[oõ]es(?:\s+sobre)?\s+(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        "decisao",
        1,
    ),
    (
        re.compile(
            r"o\s+que\s+(?:eu\s+)?aprendi(?:\s+sobre)?\s+(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        "aprendi",
        1,
    ),
    (
        re.compile(
            r"aprendizados?(?:\s+sobre)?\s+(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        "aprendi",
        1,
    ),
    (
        re.compile(
            r"o\s+que\s+(?:eu\s+)?anotei(?:\s+sobre)?\s+(.+)",
            re.IGNORECASE | re.DOTALL,
        ),
        None,
        1,
    ),
]


@dataclass(frozen=True)
class RetrievalIntent:
    topic: str
    kind: str | None
    project: str | None
    label: str


def parse_retrieval_intent(query: str) -> RetrievalIntent | None:
    text = query.strip()
    if not text:
        return None

    rec = re.match(r"^recuperar\s*:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
    if rec:
        inner = rec.group(1).strip().rstrip("?").strip()
        nested = parse_retrieval_intent(inner)
        if nested:
            return nested
        return RetrievalIntent(topic=inner, kind=None, project=None, label="entradas")

    for pattern, kind, group in _INTENT_PATTERNS:
        m = pattern.match(text)
        if not m:
            continue
        topic = m.group(group).strip().rstrip("?").strip()
        project = None
        pm = _PROJECT_TAIL_RE.search(topic)
        if pm:
            project = pm.group(1).strip()
            topic = _PROJECT_TAIL_RE.sub("", topic).strip()
        if not topic:
            continue
        labels = {
            "decisao": "decisões",
            "aprendi": "aprendizados",
            None: "notas",
        }
        return RetrievalIntent(
            topic=topic,
            kind=kind,
            project=project,
            label=labels.get(kind, "entradas"),
        )
    return None


def retrieve_for_query(
    data_dir: Path,
    query: str,
    *,
    limit: int = 12,
) -> tuple[list[CaptureEntry], RetrievalIntent | None]:
    intent = parse_retrieval_intent(query)
    topic = intent.topic if intent else query.strip()
    kind = intent.kind if intent else None
    project = intent.project if intent else None

    if not topic and not project:
        return [], intent

    seen: set[str] = set()
    ordered: list[CaptureEntry] = []

    def add(entry: CaptureEntry | None) -> None:
        if entry is None or entry.id in seen:
            return
        seen.add(entry.id)
        ordered.append(entry)

    if project:
        for e in gather_related(data_dir, project=project, limit=limit):
            add(e)

    for e in search_captures(
        data_dir,
        topic,
        limit=limit,
        kind=kind,
        project=project,
    ):
        add(e)

    if kind and topic:
        for e in gather_related(data_dir, query=topic, limit=limit):
            if e.type == kind:
                add(e)
    elif topic:
        for e in gather_related(data_dir, query=topic, limit=limit):
            add(e)

    return ordered[:limit], intent


def _entry_meta(entry: CaptureEntry) -> dict[str, str]:
    meta, _ = _read_frontmatter(entry.path)
    return meta


def format_entry_detail(entry: CaptureEntry) -> str:
    meta = _entry_meta(entry)
    lines = [f"**{entry.type_label}** — {entry.body}"]
    for key, label in (
        ("motivo", "Motivo"),
        ("risco", "Risco"),
        ("fonte", "Fonte"),
        ("projeto", "Projeto"),
    ):
        val = meta.get(key, "").strip()
        if val:
            lines.append(f"  - {label}: {val}")
    return "\n".join(lines)


def format_retrieval_markdown(
    entries: list[CaptureEntry],
    intent: RetrievalIntent | None,
) -> str:
    if not entries:
        if intent:
            return (
                f"Nenhum registro de **{intent.label}** sobre “{intent.topic}”"
                + (f" no projeto **{intent.project}**." if intent.project else ".")
            )
        return "Nada encontrado no acervo para essa consulta."

    title = "# Recuperado do seu acervo\n"
    if intent:
        proj = f" · projeto **{intent.project}**" if intent.project else ""
        title += f"_Consulta: {intent.label} sobre “{intent.topic}”{proj}_\n\n"

    blocks = []
    for e in entries:
        ts = e.created.strftime("%d/%m/%Y %H:%M")
        blocks.append(f"### {e.id} · {ts}\n\n{format_entry_detail(e)}")
    return title + "\n\n".join(blocks)


def format_context_block(entries: list[CaptureEntry], intent: RetrievalIntent | None) -> str:
    if not entries:
        return ""
    header = "Trechos recuperados do acervo"
    if intent:
        header += f" ({intent.label} sobre “{intent.topic}”)"
    lines = [header + ":"]
    for e in entries:
        detail = format_entry_detail(e).replace("\n", " ")
        lines.append(f"- {detail} (id: {e.id})")
    return "\n".join(lines)
