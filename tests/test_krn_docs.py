"""Local BM25 retrieval tests for KRN document knowledge."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from krn_catalog_cases import CATALOG_CASES

from agent import Assistant
from krn_docs import (
    INDEX_PATH,
    citation_label,
    load_index,
    search_krn_docs,
    search_krn_index,
)
from weather import get_weather
from web_search import search_web


def _joined_hits(hits: list[dict]) -> str:
    from krn_docs import fold_text

    return fold_text(" ".join(hit.get("text", "") for hit in hits))


def test_index_exists_and_keeps_source_pages():
    assert INDEX_PATH.is_file()
    chunks = load_index()
    assert chunks
    filenames = {chunk["filename"] for chunk in chunks}
    assert len(filenames) == 9
    assert all(chunk["page"] >= 1 for chunk in chunks)
    assert all(chunk["text"].strip() for chunk in chunks)


def test_search_krn_docs_is_local_only():
    source = inspect.getsource(search_krn_docs)
    assert "playwright" not in source.lower()
    assert "search_web" not in source
    assert "httpx" not in source
    assert "ddgs" not in source


@pytest.mark.asyncio
async def test_empty_query_does_not_invent_hits():
    result = await search_krn_docs("   ")
    assert result["status"] == "invalid_query"
    assert result["results"] == []


@pytest.mark.asyncio
async def test_unknown_topic_is_not_invented():
    result = await search_krn_docs("geheime Mondbasis der KRN")
    assert result["status"] in {"no_results", "no_evidence"}
    assert result["results"] == []


@pytest.mark.asyncio
async def test_realtime_delay_has_no_document_evidence():
    result = await search_krn_docs(
        "Kannst du mir aus dem Netzplan die aktuelle Verspaetung nennen?"
    )
    assert result["status"] == "no_evidence"
    assert result["results"] == []


@pytest.mark.parametrize("case", CATALOG_CASES, ids=lambda case: case["id"])
def test_catalog_retrieval(case):
    packed = search_krn_index(case["query"], limit=8)
    if case["refusal"] and case["id"] in {"F06", "N01", "N02", "N03"}:
        assert packed["status"] == "no_evidence"
        assert packed["results"] == []
        return

    hits = packed["results"]
    assert hits, f"{case['id']} returned no hits"
    joined = _joined_hits(hits)
    hit_files = {hit["filename"] for hit in hits}
    if case["filenames"]:
        assert hit_files & set(case["filenames"]), (
            f"{case['id']} files {hit_files} miss {case['filenames']}"
        )
    if case["pages"] and case["filenames"]:
        page_ok = any(
            hit["filename"] in case["filenames"] and hit["page"] in case["pages"]
            for hit in hits
        )
        assert page_ok, f"{case['id']} missing page {case['pages']} in {hits}"
    for needle in case["must_contain"]:
        assert needle in joined, f"{case['id']} missing {needle!r} in {joined[:400]}"


def test_citation_labels_follow_question_language():
    assert citation_label("de") == "Quelle"
    assert citation_label("en") == "Source"
    assert citation_label("fr") == "Source"


def test_assistant_keeps_existing_tools_and_adds_docs():
    assistant = Assistant()
    names = {getattr(tool, "__name__", "") for tool in assistant.tools}
    assert names >= {"search_krn_docs", "search_web", "get_weather"}
    assert assistant.llm.model == "gemini-3.1-flash-live-preview"
    instructions = assistant.instructions
    assert "search_krn_docs" in instructions
    assert "zuerst search_krn_docs" in instructions
    assert "Answer immediately" not in instructions
    assert "search_web" in instructions
    assert "get_weather" in instructions
    assert "open_browser" in instructions


def test_existing_tool_modules_were_not_replaced():
    assert get_weather.__name__ == "get_weather"
    assert search_web.__name__ == "search_web"
    assert Path("src/weather.py").is_file()
    assert Path("src/web_search.py").is_file()
    assert Path("src/browser_tools.py").is_file()
