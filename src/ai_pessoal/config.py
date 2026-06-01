from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "app": {"name": "AI-Pessoal", "language": "pt-BR", "data_dir": "~/.ai-pessoal"},
    "ollama": {
        "base_url": "http://127.0.0.1:11434",
        "model_default": "qwen2.5:7b",
        "model_reasoning": None,
        "timeout_seconds": 120,
    },
    "chat": {
        "max_history_messages": 20,
        "temperature": 0.7,
        "system_prompt": (
            "Você é o AI-Pessoal, um assistente pessoal prestativo, claro e respeitoso. "
            "Responda em português do Brasil. Não invente fatos sobre o usuário; "
            "use apenas o contexto fornecido. Se não souber, diga."
        ),
    },
    "modes": {"note_prefix": ".", "question_prefix": "?"},
    "privacy": {"allow_network_tools": False, "allow_shell": False},
    "features": {
        "long_term_memory": False,
        "semantic_search": False,
        "cortana_bridge": False,
        "reminders": False,
    },
    "context": {
        "active_project": None,
    },
    "semantic": {
        "embed_model": "nomic-embed-text",
        "min_score": 0.35,
        "max_results": 12,
    },
    "documents": {
        "chunk_chars": 900,
        "chunk_overlap": 120,
    },
    "cortana": {
        "enabled": False,
        "base_url": "http://127.0.0.1:8787",
        "poll_seconds": 3,
        "timeout_seconds": 600,
        "default_output_type": "summary",
    },
}


def is_semantic_enabled(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("features", {}).get("semantic_search", False))


def set_cortana_bridge(data_dir: Path, enabled: bool) -> dict[str, Any]:
    config_path = data_dir / "config.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg.setdefault("features", {})["cortana_bridge"] = enabled
    cfg.setdefault("cortana", {})["enabled"] = enabled
    config_path.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return cfg


def set_semantic_search(data_dir: Path, enabled: bool) -> dict[str, Any]:
    config_path = data_dir / "config.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    cfg.setdefault("features", {})["semantic_search"] = enabled
    config_path.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return cfg


def get_active_project(cfg: dict[str, Any]) -> str | None:
    raw = cfg.get("context", {}).get("active_project")
    if raw is None:
        return None
    name = str(raw).strip()
    return name or None


def set_active_project(data_dir: Path, name: str | None) -> dict[str, Any]:
    config_path = data_dir / "config.json"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    ctx = cfg.setdefault("context", {})
    if name is None or not str(name).strip():
        ctx["active_project"] = None
    else:
        ctx["active_project"] = str(name).strip()
    config_path.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return cfg


def resolve_project(cfg: dict[str, Any], explicit: str | None = None) -> str | None:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    return get_active_project(cfg)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def example_config_path() -> Path:
    return project_root() / "config.example.json"


def resolve_data_dir(cfg: dict[str, Any]) -> Path:
    raw = cfg.get("app", {}).get("data_dir", "~/.ai-pessoal")
    return Path(os.path.expanduser(str(raw))).resolve()


def ensure_data_layout(data_dir: Path) -> None:
    for sub in ("capture", "sessions", "memory", "links", "embeddings", "documents"):
        (data_dir / "data" / sub).mkdir(parents=True, exist_ok=True)


def load_config() -> tuple[dict[str, Any], Path]:
    data_dir = resolve_data_dir(DEFAULT_CONFIG)
    config_path = data_dir / "config.json"

    if not config_path.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        example = example_config_path()
        if example.exists():
            shutil.copy(example, config_path)
        else:
            config_path.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    data_dir = resolve_data_dir(cfg)
    ensure_data_layout(data_dir)
    return cfg, data_dir
