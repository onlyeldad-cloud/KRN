"""Regression checks for complete, safe offline document preparation."""

import importlib.util
from pathlib import Path

import pytest

import krn_docs

spec = importlib.util.spec_from_file_location(
    "prepare", Path(__file__).resolve().parents[1] / "scripts/prepare_krn_docs.py"
)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def test_native_text_does_not_trigger_ocr_by_filename():
    assert not prepare.needs_ocr(prepare.JUBILAEEN, "Lesbarer deutscher Inhalt. " * 20)
    assert prepare.needs_ocr("new.pdf", "")


def test_long_pages_have_bounded_chunks_without_losing_tail():
    text = "Eine wichtige Regelung gilt. " * 200 + "ENDE_DER_SEITE"
    chunks = prepare.split_paragraphs(text)
    assert max(map(len, chunks)) <= 1800
    assert "ENDE_DER_SEITE" in chunks[-1]


@pytest.mark.parametrize(
    "query",
    [
        "Betriebs zugehörigkeit",
        "Betriebszugehorigkeit",
        "10 Jahre bei KRN",
        "zehn Jahre gearbeitet",
        "Jubiläum nach zehn Jahren",
    ],
)
def test_spoken_anniversary_variants(query):
    assert krn_docs.is_krn_internal_question(query)
    hits = krn_docs.search_krn_index(query)["results"]
    assert any(h["filename"] == prepare.JUBILAEEN and h["page"] == 3 for h in hits)


def test_inventory_does_not_hide_unindexed_documents(tmp_path, monkeypatch):
    import json

    path = tmp_path / "index.json"
    path.write_text(
        json.dumps(
            {"documents": [{"filename": "unreadable.pdf", "pages": 1}], "chunks": []}
        )
    )
    monkeypatch.setattr(krn_docs, "INDEX_PATH", path)
    assert krn_docs.load_inventory_documents()[0]["filename"] == "unreadable.pdf"


def test_anniversary_answer_keeps_paid_leave():
    query = "Was bekomme ich bei 40 Jahren Betriebszugehörigkeit?"
    answer = krn_docs.short_krn_voice_answer(query, krn_docs.search_krn_index(query))
    assert "400" in answer and "freier Tag" in answer


def test_unrelated_number_does_not_create_anniversary_entitlement():
    query = "Welche KRN Betriebsrente bekomme ich nach 10 Jahren?"
    answer = krn_docs.short_krn_voice_answer(query, krn_docs.search_krn_index(query))
    assert "100 Euro" not in answer
