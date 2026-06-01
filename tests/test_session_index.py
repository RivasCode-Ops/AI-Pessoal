import json
from pathlib import Path
from unittest.mock import patch

from ai_pessoal.semantic import load_all_index_rows, search_index
from ai_pessoal.session import ChatSession, sessions_dir
from ai_pessoal.session_index import index_session_file, message_row_id


def test_message_row_id():
    assert message_row_id("20260101-abc", 3) == "sess:20260101-abc:0003"


def test_index_session_semantic_search(tmp_path: Path):
    d = tmp_path
    sessions_dir(d).mkdir(parents=True, exist_ok=True)
    path = sessions_dir(d) / "20260101-test.jsonl"
    sess = ChatSession(session_id="20260101-test", path=path)
    sess.append("user", "como melhorar funil de vendas")
    sess.append("assistant", "teste A/B no topo do funil")

    cfg = {
        "features": {"semantic_search": True},
        "semantic": {"embed_model": "m", "min_score": 0.3},
        "ollama": {"base_url": "http://127.0.0.1:11434", "timeout_seconds": 5},
    }

    def fake_embed(_base, _model, text, timeout=60):
        if "funil" in text.lower():
            return [1.0, 0.0]
        return [0.0, 1.0]

    with patch("ai_pessoal.session_index.embed_text", side_effect=fake_embed):
        n = index_session_file(d, cfg, path, force=True)
    assert n == 2

    with patch("ai_pessoal.semantic.embed_text", side_effect=fake_embed):
        hits = search_index(d, cfg, "estratégia de funil", limit=5)

    assert any(h.source_type == "session" for h in hits)
    rows = load_all_index_rows(d, "m")
    assert message_row_id("20260101-test", 0) in rows
