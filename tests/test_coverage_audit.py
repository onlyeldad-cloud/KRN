"""Independent structural checks, including all source pages and offline provenance."""

import hashlib
import json
from pathlib import Path

import pymupdf
import pytest

from krn_docs import INDEX_PATH, fold_text, is_krn_internal_question, search_krn_index

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = json.loads(INDEX_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("doc", PAYLOAD["documents"], ids=lambda d: d["filename"])
def test_source_pages_and_review_provenance(doc):
    source = ROOT / "data/pdf-quellen" / doc["filename"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == doc["source_sha256"]
    with pymupdf.open(source) as pdf:
        assert len(pdf) == doc["pages"]
    chunks = [c for c in PAYLOAD["chunks"] if c["filename"] == doc["filename"]]
    assert {c["page"] for c in chunks} == set(range(1, doc["pages"] + 1))
    assert doc["processing_status"] == "processed"
    for chunk in chunks:
        if chunk.get("kind") == "answer_fact":
            assert chunk["source_sha256"] == doc["source_sha256"]
            assert all(1 <= p <= doc["pages"] for p in chunk["pages"])
    for page in doc["page_details"]:
        assert page["indexed"] and page["quality"] not in {
            "needs_review",
            "partial_verified_facts",
        }


def test_native_map_missing_labels_are_restored():
    results = search_krn_index("Wabenplan Hochstätten Undenheim Algenrodt", limit=8)[
        "results"
    ]
    text = fold_text(
        " ".join(
            r["text"] for r in results if r["filename"] == "DOC-20260920-WA0006.pdf"
        )
    )
    assert "hochst" in text and "undenheim" in text


@pytest.mark.parametrize(
    "text",
    [
        "Hallo, wie geht es dir?",
        "Danke!",
        "Erzähl mir einen Witz.",
        "Wie ist das Wetter heute in Berlin?",
    ],
)
def test_normal_conversation_does_not_route_to_docs(text):
    assert not is_krn_internal_question(text)


def test_repeated_searches_reuse_loaded_index(monkeypatch):
    import krn_docs

    krn_docs._load_search_bundle.cache_clear()
    original = Path.read_text
    reads = []

    def counted(path, *args, **kwargs):
        if path == INDEX_PATH:
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted)
    for _ in range(20):
        search_krn_index("Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?")
    assert len(reads) == 1
