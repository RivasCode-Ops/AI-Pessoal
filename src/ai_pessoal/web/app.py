from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ai_pessoal.capture import list_captures, parse_capture_line, save_capture, search_captures
from ai_pessoal.chat import run_chat
from ai_pessoal.config import load_config
from ai_pessoal.memory import format_who_am_i
from ai_pessoal.relate import format_related_markdown, gather_related
from ai_pessoal.ollama_client import OllamaError, health_check
from ai_pessoal.session import start_session

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="AI-Pessoal", version="0.3.0")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CaptureIn(BaseModel):
    text: str = Field(..., min_length=1)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


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
    _, data_dir = load_config()
    entry = save_capture(data_dir, kind, text)
    return {"ok": True, "id": entry.id, "type": entry.type_label}


@app.get("/api/search")
def api_search(q: str = "", project: str = ""):
    _, data_dir = load_config()
    hits = search_captures(data_dir, q, project=project or None, limit=25)
    return [
        {"id": e.id, "type": e.type_label, "body": e.body, "created": e.created.isoformat()}
        for e in hits
    ]


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


@app.post("/api/chat")
def api_chat(body: ChatIn):
    cfg, data_dir = load_config()
    session = start_session(data_dir)
    try:
        reply = run_chat(cfg, data_dir, session, body.message.strip())
    except OllamaError as e:
        raise HTTPException(503, str(e)) from e
    return {"reply": reply, "session_id": session.session_id}


def main() -> None:
    import uvicorn

    uvicorn.run("ai_pessoal.web.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
