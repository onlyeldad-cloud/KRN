import asyncio
from unittest.mock import AsyncMock

import pytest
from livekit.agents import AgentSession, inference

from agent import Assistant
from browser_tools import BrowserTools


class _FakePage:
    url = "https://docs.livekit.io/"

    async def goto(self, url, **kwargs):
        self.url = url

    async def bring_to_front(self):
        return None

    async def title(self):
        return "LiveKit Documentation"


@pytest.mark.asyncio
@pytest.mark.live
async def test_official_livekit_docs_open_browser():
    browser = BrowserTools()
    browser._start = AsyncMock(return_value=_FakePage())
    async with (
        inference.LLM(model="google/gemma-4-31b-it") as judge,
        AgentSession() as session,
    ):
        async with asyncio.timeout(90):
            greeting = await session.start(Assistant(browser=browser), capture_run=True)
            await greeting
            result = await session.run(
                user_input="Suche die offizielle LiveKit-Dokumentation."
            )
            result.expect.contains_function_call(name="open_browser")
            await (
                result.expect[-1]
                .is_message(role="assistant")
                .judge(
                    judge,
                    intent=(
                        "Speaks German. Indicates the official LiveKit documentation "
                        "was opened or shown. Does not claim it only searched snippets."
                    ),
                )
            )
