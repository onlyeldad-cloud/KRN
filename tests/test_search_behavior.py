import asyncio
from unittest.mock import patch

import pytest
from livekit.agents import AgentSession, inference

from agent import Assistant


@pytest.mark.asyncio
async def test_gemini_calls_search_and_uses_result():
    # Deterministic search evidence, but a real Gemini session and tool call.
    rows = [
        {
            "title": "KRN Testveranstaltung",
            "link": "https://example.com/krn-test",
            "snippet": "Die KRN Testveranstaltung beginnt um 16:30 Uhr.",
        }
    ]
    with patch("web_search.DuckDuckGoSearchAPIWrapper.results", return_value=rows):
        async with (
            inference.LLM(model="google/gemma-4-31b-it") as judge,
            AgentSession() as session,
        ):
            async with asyncio.timeout(90):
                greeting = await session.start(Assistant(), capture_run=True)
                await greeting
                result = await session.run(
                    user_input="Suche bitte im Internet, wann die KRN Testveranstaltung beginnt."
                )
                result.expect.contains_function_call(name="search_web")
                await (
                    result.expect[-1]
                    .is_message(role="assistant")
                    .judge(
                        judge,
                        intent="Answers in German that the event begins at 16:30, based on the search result.",
                    )
                )
