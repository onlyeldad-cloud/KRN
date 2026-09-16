from unittest.mock import MagicMock

import pytest
from livekit.agents.llm import ToolError

from browser_tools import BrowserTools, validate_public_url


def test_job_session_browser_is_headed():
    assert BrowserTools()._headless() is True
    assert BrowserTools(MagicMock())._headless() is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///C:/Windows/win.ini",
        "http://127.0.0.1",
        "http://localhost",
        "http://[::1]",
        "https://user:pass@example.com",
    ],
)
async def test_browser_rejects_local_and_credential_urls(url):
    with pytest.raises(ValueError):
        await validate_public_url(url)


@pytest.mark.asyncio
async def test_clicks_and_typing_run_without_app_prompt(monkeypatch):
    monkeypatch.delenv("KRN_BROWSER_REQUIRE_APPROVAL", raising=False)
    await BrowserTools()._approve("Klicken: KRN: Home (link)")


@pytest.mark.asyncio
async def test_optional_approval_blocks_without_frontend(monkeypatch):
    monkeypatch.setenv("KRN_BROWSER_REQUIRE_APPROVAL", "1")
    with pytest.raises(ToolError):
        await BrowserTools()._approve("Klicken: KRN: Home (link)")


@pytest.mark.asyncio
async def test_approval_must_cover_entire_text():
    browser = BrowserTools()
    with pytest.raises(ToolError):
        await browser.type_browser("Name", "a" * 1001)
    assert browser.page is None
