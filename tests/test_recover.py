from pathlib import Path

from ai_pessoal.capture import save_capture
from ai_pessoal.recover import parse_retrieval_intent, retrieve_for_query


def test_parse_decision_intent():
    intent = parse_retrieval_intent("por que decidi sair da empresa?")
    assert intent is not None
    assert intent.kind == "decisao"
    assert "sair" in intent.topic.lower()


def test_retrieve_decision_with_motivo(tmp_path: Path):
    save_capture(
        tmp_path,
        "decisao",
        "sair da empresa X\nMotivo: cultura tóxica\nRisco: período sem renda",
    )
    entries, intent, _docs = retrieve_for_query(tmp_path, "por que decidi sair da empresa")
    assert intent is not None
    assert len(entries) >= 1
    assert "empresa" in entries[0].body.lower()
