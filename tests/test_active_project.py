import json
from pathlib import Path

from ai_pessoal.capture import save_capture, search_captures
from ai_pessoal.config import get_active_project, set_active_project
from ai_pessoal.recover import retrieve_for_query


def test_active_project_filters_search(tmp_path: Path):
    d = tmp_path
    cfg_path = d / "config.json"
    cfg_path.write_text(
        json.dumps({"app": {"data_dir": str(d)}, "context": {"active_project": None}}),
        encoding="utf-8",
    )
    save_capture(d, "nota", "reunião geral")
    save_capture(d, "nota", "cliente X\nprojeto: Revigor")

    cfg = set_active_project(d, "Revigor")
    hits = search_captures(d, "cliente", project=get_active_project(cfg))
    assert len(hits) == 1
    assert "cliente" in hits[0].body.lower()


def test_capture_inherits_active_project(tmp_path: Path):
    d = tmp_path
    (d / "config.json").write_text("{}", encoding="utf-8")
    set_active_project(d, "Master Chip")
    entry = save_capture(d, "aprendi", "teste A/B", active_project="Master Chip")
    text = entry.path.read_text(encoding="utf-8")
    assert "projeto: Master Chip" in text


def test_retrieve_uses_active_project(tmp_path: Path):
    d = tmp_path
    (d / "config.json").write_text("{}", encoding="utf-8")
    save_capture(d, "decisao", "usar Ollama\nMotivo: privacidade\nprojeto: Revigor")
    save_capture(d, "fato", "comprei carro novo")

    entries, _, _docs = retrieve_for_query(d, "ollama", active_project="Revigor", limit=10)
    bodies = " ".join(e.body.lower() for e in entries)
    assert "ollama" in bodies
    assert "carro" not in bodies
