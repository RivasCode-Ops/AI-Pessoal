from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


def exports_dir(data_dir: Path) -> Path:
    p = data_dir / "data" / "exports"
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_acervo(data_dir: Path) -> Path:
    """Copia capturas, sessoes, links e config para pasta datada."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = exports_dir(data_dir) / stamp
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for sub in ("capture", "sessions", "links", "embeddings"):
        src = data_dir / "data" / sub
        if src.exists() and any(src.iterdir()):
            shutil.copytree(src, dest / sub)
            copied.append(sub)

    cfg_src = data_dir / "config.json"
    if cfg_src.exists():
        shutil.copy2(cfg_src, dest / "config.json")
        copied.append("config.json")

    meta = {
        "exported_at": datetime.now().astimezone().isoformat(),
        "source": str(data_dir),
        "folders": copied,
    }
    (dest / "export.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return dest
