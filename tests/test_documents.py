from ai_pessoal.documents import chunk_text, chunk_id


def test_chunk_text_overlap():
    text = "a" * 1000
    parts = chunk_text(text, size=400, overlap=50)
    assert len(parts) >= 2
    assert all(len(p) <= 400 for p in parts)


def test_chunk_id_stable():
    assert chunk_id("Relatório 2026.pdf", 3) == chunk_id("Relatório 2026.pdf", 3)
