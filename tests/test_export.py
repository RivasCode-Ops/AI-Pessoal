from ai_pessoal.capture import save_capture
from ai_pessoal.export_acervo import export_acervo


def test_export_creates_folder(tmp_path):
    save_capture(tmp_path, "nota", "teste export")
    dest = export_acervo(tmp_path)
    assert dest.exists()
    assert (dest / "capture").exists()
    assert (dest / "export.json").exists()
