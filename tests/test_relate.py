from pathlib import Path

from ai_pessoal.capture import save_capture
from ai_pessoal.relate import add_link, gather_related


def test_links_and_project(tmp_path: Path):
    d = tmp_path
    a = save_capture(d, "projeto", "Revigor")
    b = save_capture(
        d,
        "aprendi",
        "Vídeo converte melhor\nprojeto: Revigor\nFonte: teste",
    )
    c = save_capture(d, "nota", "Reunião cliente")
    add_link(d, c.id, b.id)

    by_proj = gather_related(d, project="Revigor")
    ids = {e.id for e in by_proj}
    assert a.id in ids
    assert b.id in ids

    by_link = gather_related(d, entry_id=c.id)
    assert b.id in {e.id for e in by_link}
