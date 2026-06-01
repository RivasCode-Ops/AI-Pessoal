import json
from pathlib import Path
from unittest.mock import patch

from ai_pessoal.cortana_bridge import (
    build_aprendi_body,
    import_existing_search,
    start_search,
    wait_for_search,
)


def _cfg():
    return {
        "features": {"cortana_bridge": True},
        "cortana": {"base_url": "http://127.0.0.1:8787", "poll_seconds": 0.01, "timeout_seconds": 5},
    }


def test_build_aprendi_body():
    detail = {
        "search": {"id": "abc-123", "demand": "ERPs varejo", "status": "completed"},
        "report": {
            "content": "Resumo: opção A é mais barata.",
            "sources_json": json.dumps([{"title": "Site", "url": "https://exemplo.com"}]),
        },
    }
    body = build_aprendi_body(detail)
    assert "Resumo" in body
    assert "Cortana pesquisa abc-123" in body
    assert "exemplo.com" in body


def test_import_existing_search(tmp_path: Path):
    detail = {
        "search": {"id": "full-uuid", "status": "completed"},
        "report": {"content": "Achado importante.", "sources_json": "[]"},
    }

    def fake_request(cfg, path, **kwargs):
        if path.endswith("/full-uuid"):
            return detail
        return {}

    with patch("ai_pessoal.cortana_bridge._request", side_effect=fake_request):
        entry = import_existing_search(tmp_path, _cfg(), "full-uuid")

    assert entry.type == "aprendi"
    assert "Achado" in entry.body


def test_start_search_returns_id():
    with patch(
        "ai_pessoal.cortana_bridge._request",
        return_value={"id": "new-search-id"},
    ):
        sid = start_search(_cfg(), "teste demanda")
    assert sid == "new-search-id"


def test_wait_for_completed():
    calls = {"n": 0}

    def fake_progress(cfg, search_id):
        calls["n"] += 1
        if calls["n"] >= 2:
            return {"status": "completed", "percent": 100}
        return {"status": "running", "percent": 50}

    with patch("ai_pessoal.cortana_bridge.get_progress", side_effect=fake_progress):
        wait_for_search(_cfg(), "x")
