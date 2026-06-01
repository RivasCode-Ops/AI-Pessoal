from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from ai_pessoal.config import is_semantic_enabled
from ai_pessoal.semantic import (
    chunk_settings,
    embed_model,
    load_all_index_rows,
    save_index_rows,
)
from ai_pessoal.ollama_client import OllamaError, embed_text


def documents_dir(data_dir: Path) -> Path:
    p = data_dir / "data" / "documents"
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_pdfs(data_dir: Path) -> list[Path]:
    folder = documents_dir(data_dir)
    return sorted(folder.glob("*.pdf"), key=lambda p: p.name.lower())


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError(
            "Instale suporte PDF: pip install 'ai-pessoal[pdf]' ou pip install pypdf"
        ) from e

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def chunk_text(text: str, *, size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [c for c in chunks if c]


def chunk_id(pdf_name: str, index: int) -> str:
    stem = Path(pdf_name).stem
    safe = re.sub(r"[^\w\-]+", "_", stem)[:40]
    return f"doc:{safe}:{index:04d}"


def _pdf_mtime(path: Path) -> float:
    return path.stat().st_mtime


def _pdf_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def index_document(data_dir: Path, cfg: dict[str, Any], pdf_path: Path, *, force: bool = False) -> int:
    """Indexa um PDF em chunks. Retorna quantidade de chunks indexados."""
    if not is_semantic_enabled(cfg):
        return 0

    model = embed_model(cfg)
    base = str(cfg["ollama"]["base_url"])
    timeout = float(cfg["ollama"].get("timeout_seconds", 120))
    size, overlap = chunk_settings(cfg)

    try:
        full_text = extract_pdf_text(pdf_path)
    except (ImportError, OSError, ValueError):
        return 0
    chunks = chunk_text(full_text, size=size, overlap=overlap)
    if not chunks:
        return 0

    mtime = _pdf_mtime(pdf_path)
    file_hash = _pdf_hash(pdf_path)
    rows = load_all_index_rows(data_dir, model)
    if not force:
        for row in rows.values():
            if row.get("kind") == "document" and row.get("source") == pdf_path.name:
                if (
                    float(row.get("mtime", 0)) == mtime
                    and row.get("file_hash") == file_hash
                ):
                    return 0
                break

    for key in list(rows):
        row = rows[key]
        if row.get("kind") == "document" and row.get("source") == pdf_path.name:
            del rows[key]

    indexed = 0
    for i, chunk in enumerate(chunks):
        cid = chunk_id(pdf_path.name, i)
        embed_input = f"Documento: {pdf_path.name}\n{chunk}"
        try:
            vector = embed_text(base, model, embed_input, timeout=timeout)
        except OllamaError:
            break
        rows[cid] = {
            "id": cid,
            "kind": "document",
            "source": pdf_path.name,
            "chunk_index": i,
            "text": chunk,
            "model": model,
            "mtime": mtime,
            "file_hash": file_hash,
            "vector": vector,
        }
        indexed += 1

    save_index_rows(data_dir, rows)
    return indexed


def index_all_documents(data_dir: Path, cfg: dict[str, Any], *, force: bool = True) -> tuple[int, int]:
    pdfs = list_pdfs(data_dir)
    total_chunks = 0
    for pdf in pdfs:
        total_chunks += index_document(data_dir, cfg, pdf, force=force)
    return total_chunks, len(pdfs)


def list_document_sources(data_dir: Path) -> list[str]:
    return [p.name for p in list_pdfs(data_dir)]
