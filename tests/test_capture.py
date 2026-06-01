from pathlib import Path

from ai_pessoal.capture import parse_capture_line, save_capture, search_captures


def test_parse_and_search(tmp_path: Path):
    parsed = parse_capture_line("nota: hello")
    assert parsed == ("nota", "hello")

    parsed = parse_capture_line("decisão: usar local")
    assert parsed[0] == "decisao"

    e = save_capture(tmp_path, "fato", "Tenho 54 anos")
    assert e.path.exists()

    save_capture(
        tmp_path,
        "decisao",
        "Escolher Ollama\nMotivo: privacidade\nprojeto: Revigor",
    )
    hits = search_captures(tmp_path, "", project="Revigor")
    assert len(hits) >= 1
