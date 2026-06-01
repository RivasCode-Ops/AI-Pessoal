from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_pessoal.capture import list_captures, parse_capture_line, save_capture, search_captures
from ai_pessoal.chat import run_chat
from ai_pessoal.config import (
    get_active_project,
    is_semantic_enabled,
    load_config,
    resolve_project,
    set_active_project,
)
from ai_pessoal.documents import index_all_documents, list_document_sources
from ai_pessoal.semantic import index_all, search_index
from ai_pessoal.memory import format_who_am_i
from ai_pessoal.recover import format_retrieval_markdown, retrieve_for_query
from ai_pessoal.relate import format_related_markdown, gather_related
from ai_pessoal.ollama_client import OllamaError, health_check
from ai_pessoal.session import start_session

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="AI-Pessoal", version="0.7.0")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CaptureIn(BaseModel):
    text: str = Field(..., min_length=1)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class ActiveProjectIn(BaseModel):
    name: str | None = None


@app.get("/", response_class=HTMLResponse)
def index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(500, "index.html não encontrado")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/api/health")
def api_health():
    cfg, data_dir = load_config()
    base = str(cfg["ollama"]["base_url"])
    return {
        "ok": True,
        "ollama": health_check(base),
        "data_dir": str(data_dir),
        "model": cfg["ollama"]["model_default"],
        "active_project": get_active_project(cfg),
        "semantic_search": is_semantic_enabled(cfg),
        "embed_model": cfg.get("semantic", {}).get("embed_model", "nomic-embed-text"),
    }


@app.get("/api/captures")
def api_captures(limit: int = 30):
    _, data_dir = load_config()
    items = list_captures(data_dir, limit=min(limit, 100))
    return [
        {
            "id": e.id,
            "type": e.type,
            "type_label": e.type_label,
            "body": e.body,
            "created": e.created.isoformat(),
        }
        for e in items
    ]


@app.post("/api/capture")
def api_capture(body: CaptureIn):
    parsed = parse_capture_line(body.text)
    if not parsed:
        raise HTTPException(
            400,
            "Use prefixo: nota:, ideia:, decisão:, fato:, pref:, projeto:, aprendi:",
        )
    kind, text = parsed
    cfg, data_dir = load_config()
    entry = save_capture(
        data_dir,
        kind,
        text,
        active_project=get_active_project(cfg),
        cfg=cfg,
    )
    return {"ok": True, "id": entry.id, "type": entry.type_label}


@app.get("/api/search")
def api_search(q: str = "", project: str = ""):
    cfg, data_dir = load_config()
    proj = resolve_project(cfg, project or None)
    seen: set[str] = set()
    out: list[dict] = []
    if is_semantic_enabled(cfg) and q:
        for s in search_index(data_dir, cfg, q, limit=15, project=proj):
            if s.entry:
                seen.add(s.entry.id)
                out.append(
                    {
                        "id": s.entry.id,
                        "type": s.entry.type_label,
                        "body": s.entry.body,
                        "created": s.entry.created.isoformat(),
                        "score": round(s.score, 3),
                        "semantic": True,
                    }
                )
            elif s.source_type == "document":
                out.append(
                    {
                        "id": s.hit_id,
                        "type": s.label,
                        "body": s.text,
                        "created": "",
                        "score": round(s.score, 3),
                        "semantic": True,
                        "document": s.document,
                    }
                )
    for e in search_captures(data_dir, q, project=proj, limit=25):
        if e.id in seen:
            continue
        seen.add(e.id)
        out.append(
            {
                "id": e.id,
                "type": e.type_label,
                "body": e.body,
                "created": e.created.isoformat(),
                "semantic": False,
            }
        )
    return out


@app.get("/api/profile")
def api_profile():
    _, data_dir = load_config()
    return {"markdown": format_who_am_i(data_dir)}


@app.get("/api/related")
def api_related(
    id: str = "",
    project: str = "",
    q: str = "",
    limit: int = 20,
):
    _, data_dir = load_config()
    entries = gather_related(
        data_dir,
        entry_id=id or None,
        project=project or None,
        query=q or None,
        limit=min(limit, 50),
    )
    return {
        "markdown": format_related_markdown(data_dir, entries),
        "items": [
            {
                "id": e.id,
                "type": e.type_label,
                "body": e.body,
                "created": e.created.isoformat(),
            }
            for e in entries
        ],
    }


@app.get("/api/active-project")
def api_get_active_project():
    cfg, _ = load_config()
    return {"name": get_active_project(cfg)}


@app.put("/api/active-project")
def api_set_active_project(body: ActiveProjectIn):
    _, data_dir = load_config()
    name = body.name
    if name is not None and str(name).strip().lower() in ("", "limpar", "clear", "off"):
        name = None
    cfg = set_active_project(data_dir, name)
    return {"name": get_active_project(cfg)}


@app.get("/api/recover")
def api_recover(q: str = "", limit: int = 15):
    cfg, data_dir = load_config()
    entries, intent, doc_hits = retrieve_for_query(
        data_dir,
        q,
        limit=min(limit, 50),
        active_project=get_active_project(cfg),
        cfg=cfg,
    )
    return {
        "markdown": format_retrieval_markdown(entries, intent, doc_hits),
        "items": [
            {
                "id": e.id,
                "type": e.type_label,
                "body": e.body,
                "created": e.created.isoformat(),
            }
            for e in entries
        ],
    }


@app.post("/api/semantic/index")
def api_semantic_index():
    cfg, data_dir = load_config()
    if not is_semantic_enabled(cfg):
        raise HTTPException(400, "semantic_search desativado em config.json")
    ok, total = index_all(data_dir, cfg)
    chunks, pdfs = index_all_documents(data_dir, cfg, force=True)
    return {
        "indexed": ok,
        "total": total,
        "doc_chunks": chunks,
        "pdfs": pdfs,
        "pdf_files": list_document_sources(data_dir),
    }


@app.get("/api/semantic/search")
def api_semantic_search(q: str = "", limit: int = 15):
    cfg, data_dir = load_config()
    if not is_semantic_enabled(cfg):
        raise HTTPException(400, "semantic_search desativado")
    hits = search_index(
        data_dir,
        cfg,
        q,
        limit=min(limit, 30),
        project=get_active_project(cfg),
    )
    return [
        {
            "id": s.hit_id,
            "type": s.label,
            "body": s.text,
            "score": round(s.score, 3),
            "source": s.source_type,
            "document": s.document,
        }
        for s in hits
    ]


@app.post("/api/chat")
def api_chat(body: ChatIn):
    cfg, data_dir = load_config()
    session = start_session(data_dir)
    try:
        reply, sources = run_chat(cfg, data_dir, session, body.message.strip())
    except OllamaError as e:
        raise HTTPException(503, str(e)) from e
    return {"reply": reply, "session_id": session.session_id, "sources": sources}


def main() -> None:
    import uvicorn

    uvicorn.run("ai_pessoal.web.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
