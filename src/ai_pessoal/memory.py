from __future__ import annotations

from pathlib import Path

from ai_pessoal.capture import CaptureEntry, list_captures
from ai_pessoal.recover import format_context_block, retrieve_for_query

PROFILE_TYPES = ("fato", "pref", "projeto")
CONTEXT_TYPES = ("fato", "pref", "projeto", "decisao", "aprendi", "nota", "ideia")


def _format_entry_line(entry: CaptureEntry) -> str:
    return f"- [{entry.type_label}] {entry.body.replace(chr(10), ' ')}"


def list_profile_entries(data_dir: Path, limit_per_type: int = 10) -> dict[str, list[CaptureEntry]]:
    out: dict[str, list[CaptureEntry]] = {}
    for kind in PROFILE_TYPES:
        out[kind] = list_captures(data_dir, limit=limit_per_type, kind=kind)
    return out


def format_who_am_i(data_dir: Path) -> str:
    """Perfil só a partir do registrado — sem inventar."""
    profile = list_profile_entries(data_dir)
    lines = ["# O que está registrado sobre você\n"]
    empty = True
    for kind in PROFILE_TYPES:
        entries = profile[kind]
        if not entries:
            continue
        empty = False
        label = {"fato": "Fatos", "pref": "Preferências", "projeto": "Projetos"}[kind]
        lines.append(f"## {label}\n")
        for e in entries:
            lines.append(_format_entry_line(e))
        lines.append("")
    if empty:
        return (
            "Ainda não há fatos, preferências ou projetos registrados.\n"
            "Use: `fato: ...`, `pref: ...`, `projeto: Nome`"
        )
    lines.append(
        "_Fonte: capturas em ~/.ai-pessoal/data/capture — "
        "a IA na conversa usa este acervo quando relevante._"
    )
    return "\n".join(lines)


def build_memory_context(data_dir: Path, *, max_items: int = 15) -> str:
    """Bloco fixo de memória de perfil para o system prompt."""
    parts: list[str] = []
    count = 0
    for kind in ("fato", "pref", "projeto"):
        for entry in list_captures(data_dir, limit=5, kind=kind):
            parts.append(_format_entry_line(entry))
            count += 1
            if count >= max_items:
                break
        if count >= max_items:
            break
    if not parts:
        return ""
    return "Memória registrada do usuário:\n" + "\n".join(parts)


def build_relevant_context(data_dir: Path, query: str, *, max_items: int = 8) -> str:
    """Trechos recuperados (intenção + busca + conexões) para a pergunta."""
    hits, intent = retrieve_for_query(data_dir, query, limit=max_items)
    return format_context_block(hits, intent)


def list_projects(data_dir: Path) -> list[str]:
    names: list[str] = []
    for entry in list_captures(data_dir, limit=100, kind="projeto"):
        name = entry.body.strip().split("\n")[0].strip()
        if name and name not in names:
            names.append(name)
    return names
