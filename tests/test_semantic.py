import json
from pathlib import Path
from unittest.mock import patch

from ai_pessoal.capture import save_capture
from ai_pessoal.semantic import _cosine, _load_index_rows, _write_index_rows, semantic_search


def test_cosine_similarity():
    assert _cosine([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert _cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_semantic_search_from_index(tmp_path: Path):
    d = tmp_path
    e1 = save_capture(d, "aprendi", "funil de vendas com vídeo curto")
    e2 = save_capture(d, "nota", "reunião de alinhamento interno")

    cfg = {
        "features": {"semantic_search": True},
        "semantic": {"embed_model": "test-model", "min_score": 0.3},
        "ollama": {"base_url": "http://127.0.0.1:11434", "timeout_seconds": 5},
    }
    rows = {
        e1.id: {
            "id": e1.id,
            "model": "test-model",
            "mtime": e1.path.stat().st_mtime,
            "vector": [1.0, 0.0],
            "projeto": "",
        },
        e2.id: {
            "id": e2.id,
            "model": "test-model",
            "mtime": e2.path.stat().st_mtime,
            "vector": [0.0, 1.0],
            "projeto": "",
        },
    }
    _write_index_rows(d, rows)

    def fake_embed(_base, _model, text, timeout=60):
        if "vendas" in text.lower():
            return [0.95, 0.05]
        return [0.1, 0.9]

    with patch("ai_pessoal.semantic.embed_text", side_effect=fake_embed):
        hits = semantic_search(d, cfg, "estratégia de vendas", limit=5)

    assert len(hits) >= 1
    assert hits[0].entry.id == e1.id
    assert hits[0].score > 0.5


def test_index_rows_roundtrip(tmp_path: Path):
    d = tmp_path
    data = {"a": {"id": "a", "model": "m", "vector": [1, 2]}}
    _write_index_rows(d, data)
    loaded = _load_index_rows(d, "m")
    assert "a" in loaded
