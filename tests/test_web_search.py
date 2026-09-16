from unittest.mock import patch

import pytest

from web_search import search_web


@pytest.mark.asyncio
async def test_results_keep_sources():
    rows = [{"title": "Example", "link": "https://example.com", "snippet": "Details"}]
    with patch("web_search.DuckDuckGoSearchAPIWrapper.results", return_value=rows):
        result = await search_web("LiveKit")
    assert result["status"] == "ok"
    assert result["results"] == rows


@pytest.mark.asyncio
async def test_empty_query_does_not_search():
    with patch("web_search.DuckDuckGoSearchAPIWrapper.results") as search:
        result = await search_web("   ")
    search.assert_not_called()
    assert result["status"] == "invalid_query"


@pytest.mark.asyncio
async def test_search_failure_is_explicit_and_does_not_leak_details():
    with patch(
        "web_search.DuckDuckGoSearchAPIWrapper.results",
        side_effect=RuntimeError("private internal details"),
    ):
        result = await search_web("LiveKit")
    assert result["status"] == "unavailable"
    assert "private internal details" not in str(result)


@pytest.mark.asyncio
async def test_no_results_is_not_success():
    with patch("web_search.DuckDuckGoSearchAPIWrapper.results", return_value=[]):
        result = await search_web("unknown")
    assert result["status"] == "no_results"
