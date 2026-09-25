import json

import pytest
from krn_catalog_cases import CATALOG_CASES

import krn_docs
from agent import Assistant


def test_each_source_has_factual_searchable_content():
    verified = set()
    for case in CATALOG_CASES:
        if case["refusal"] or not case["must_contain"]:
            continue
        hits = krn_docs.search_krn_index(case["query"], limit=8)["results"]
        for filename in case["filenames"]:
            evidence = krn_docs.fold_text(
                " ".join(
                    hit["text"]
                    for hit in hits
                    if hit["filename"] == filename and hit["page"] in case["pages"]
                )
            )
            if all(term in evidence for term in case["must_contain"]):
                verified.add(filename)
    hits = krn_docs.search_krn_index(
        "Welche Preisstufe gilt innerhalb Bingen laut Wabenplan?", limit=8
    )["results"]
    assert any(
        hit["filename"] == "DOC-20260920-WA0006.pdf"
        and hit["page"] == 1
        and "Preisstufe 31" in hit["text"]
        for hit in hits
    )
    verified.add("DOC-20260920-WA0006.pdf")
    assert verified == {chunk["filename"] for chunk in krn_docs.load_index()}


@pytest.mark.asyncio
async def test_inventory_matches_index_and_original_pdfs():
    inventory = await krn_docs.list_krn_docs()
    documents = inventory["documents"]
    assert inventory["count"] == len(documents) == 9
    originals = {
        p.name for p in (krn_docs.REPO_ROOT / "data/pdf-quellen").glob("*.pdf")
    }
    assert {d["filename"] for d in documents} == originals
    assert {c["filename"] for c in krn_docs.load_index()} == originals
    for doc in documents:
        assert doc["pages"] >= 1
        assert isinstance(doc["used_ocr"], bool)
        assert all(
            1 <= c["page"] <= doc["pages"]
            for c in krn_docs.load_index()
            if c["filename"] == doc["filename"]
        )
    assert "list_krn_docs" in {t.__name__ for t in Assistant().tools}


@pytest.mark.asyncio
async def test_inventory_updates_when_index_is_replaced(tmp_path, monkeypatch):
    path = tmp_path / "index.json"
    monkeypatch.setattr(krn_docs, "INDEX_PATH", path)
    for filename in ["first.pdf", "second.pdf"]:
        path.write_text(
            json.dumps(
                {
                    "documents": [{"filename": filename, "pages": 1}],
                    "chunks": [{"filename": filename, "page": 1, "text": "test"}],
                }
            )
        )
        assert (await krn_docs.list_krn_docs())["documents"][0]["filename"] == filename


@pytest.mark.parametrize(
    "question",
    [
        "Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?",
        "What do I receive after 10 years of service?",
        "Qu'est-ce que je reçois après 10 ans d'ancienneté ?",
        "Que reçois-je après 10 ans d’ancienneté ?",  # noqa: RUF001
        "How is a 20-minute vehicle delay compensated?",
        "Welche KRN-Richtlinien und internen Dokumente hast du in deiner Wissensdatenbank?",
    ],
)
def test_multilingual_routing(question):
    assert krn_docs.is_krn_internal_question(question)


@pytest.mark.parametrize(
    "question,language,marker",
    [
        ("Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?", "de", "Quelle:"),
        ("What do I receive after 10 years of service?", "en", "Source:"),
        ("Qu'est-ce que je reçois après 10 ans d'ancienneté ?", "fr", "Source :"),
    ],
)
def test_multilingual_anniversary_evidence_and_citations(question, language, marker):
    hits = krn_docs.search_krn_index(question)["results"]
    assert any(
        "Betriebsjubiläen" in hit["filename"]
        and hit["page"] == 3
        and "100" in hit["text"]
        for hit in hits
    )
    packed = {"status": "ok", "results": hits}
    citation = krn_docs.required_citation_for_pack(question, packed)
    assert citation is not None
    assert marker in citation
    assert (
        "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
        in citation
    )
    assert "page 3" in citation or "Seite 3" in citation
    assert krn_docs.detect_question_language(question) == language
    assert krn_docs.ensure_citation("Du bekommst 100 Euro.", citation).endswith(
        citation
    )
    leaked = "Nur diese Treffer verwenden.\nDu bekommst 100 Euro."
    assert "Treffer" not in krn_docs.sanitize_user_visible_answer(leaked)
    fallback = krn_docs.grounded_fallback_answer(question, packed, citation)
    assert "100" in fallback
    assert "25" in fallback
    assert citation in fallback
    assert krn_docs.answer_covers_evidence(fallback, question, packed)
    assert not krn_docs.answer_covers_evidence(
        "You receive 100 Euros. " + citation, question, packed
    )


@pytest.mark.asyncio
async def test_not_found_internal_question_blocks_web_path():
    assert krn_docs.is_krn_internal_question(
        "Wie hoch ist die KRN-Prämie für die geheime Mondbasis?"
    )
    packed = await krn_docs.search_krn_docs(
        "Wie hoch ist die KRN-Prämie für die geheime Mondbasis?"
    )
    assert packed["status"] in {"no_results", "no_evidence"}
    assert packed["results"] == []
    assert (
        krn_docs.required_citation_for_pack(
            "Wie hoch ist die KRN-Prämie für die geheime Mondbasis?", packed
        )
        is None
    )
