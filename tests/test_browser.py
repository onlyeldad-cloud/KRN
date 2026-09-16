from unittest.mock import AsyncMock

import pytest
from livekit.agents.llm import ToolError

from browser_tools import BrowserTools, validate_public_url


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
async def test_browser_denial_prevents_fill_and_approval_allows_it():
    browser = BrowserTools()
    try:
        page = await browser._start()
        await page.set_content(
            '<label>Name<input aria-label="Name"></label><button>Weiter</button>'
        )
        controls = await browser.inspect_browser()
        assert "Weiter" in controls["controls"]
        with pytest.raises(ToolError):
            await browser.type_browser("Name", "KRN")
        assert await page.get_by_label("Name").input_value() == ""
        browser._approve = AsyncMock()
        await browser.type_browser("Name", "KRN")
        assert await page.get_by_label("Name").input_value() == "KRN"
        browser._approve.assert_awaited_once_with("In Name eingeben: KRN")
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_approval_must_cover_entire_text():
    browser = BrowserTools()
    with pytest.raises(ToolError):
        await browser.type_browser("Name", "a" * 1001)
    assert browser.page is None
