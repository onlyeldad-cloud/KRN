"""Real Gemini text-input checks; these do NOT test microphone or RoomIO transport."""

from __future__ import annotations

import asyncio
import os

import pytest
from livekit.agents import AgentSession, room_io
from livekit.agents.llm.realtime import RealtimeError

from agent import Assistant, krn_text_input
from krn_docs import list_krn_docs


def _assistant_text(session: AgentSession) -> str:
    return " ".join(
        item.text_content or ""
        for item in session.history.items
        if getattr(item, "role", None) == "assistant"
    )


@pytest.mark.skipif(
    not os.getenv("KRN_LIVE_TESTS"),
    reason="Set KRN_LIVE_TESTS=1 for paid Gemini Live checks",
)
@pytest.mark.parametrize(
    "question,label",
    [
        ("Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?", "Quelle:"),
        ("What do I receive after 10 years of service?", "Source:"),
        ("Que reçois-je après 10 ans d'ancienneté ?", "Source :"),
        ("Welche Dokumente hast du? Liste alle Original-Dateinamen auf.", "inventory"),
        ("Wie hoch ist die KRN-Prämie für die geheime Mondbasis?", "refusal"),
    ],
)
@pytest.mark.live
async def test_live_text_callback(question, label):
    """Exercise production typed-chat callback (retrieve → session.say)."""
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            async with asyncio.timeout(120), AgentSession() as session:
                await session.start(Assistant())
                await krn_text_input(session, room_io.TextInputEvent(text=question))
                await asyncio.sleep(1.0)
                response = _assistant_text(session)
                assert response, "expected a grounded assistant reply via session.say"
                if label == "inventory":
                    for doc in (await list_krn_docs())["documents"]:
                        assert doc["filename"] in response
                elif label == "refusal":
                    assert any(
                        word in response.lower() for word in ("nicht", "keine", "not")
                    )
                    assert "€" not in response and "Euro" not in response
                else:
                    assert label in response
                    assert (
                        "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
                        in response
                    )
                    assert ("Seite 3" if label == "Quelle:" else "page 3") in response
                    assert "100" in response and "25" in response
                    assert "pension" not in response.lower()
                    assert "KRN_EVIDENCE" not in response
                    assert "required_citation" not in response.lower()
            return
        except (TimeoutError, RealtimeError) as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


@pytest.mark.skipif(
    not os.getenv("KRN_LIVE_TESTS"),
    reason="Set KRN_LIVE_TESTS=1 for paid Gemini Live checks",
)
@pytest.mark.live
async def test_live_sequential_stability_text():
    """Sequential typed turns: greeting/weather stay on Gemini; docs use say."""
    questions = [
        ("Hallo, wie geht es dir?", "chat"),
        ("Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?", "doc"),
        ("Welche internen KRN-Dokumente hast du?", "inv"),
        ("Danke.", "chat"),
    ]
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            async with asyncio.timeout(180), AgentSession() as session:
                await session.start(Assistant())
                for text, kind in questions:
                    before = _assistant_text(session)
                    await krn_text_input(session, room_io.TextInputEvent(text=text))
                    await asyncio.sleep(1.0)
                    after = _assistant_text(session)
                    assert after != before or kind == "chat"
                    if kind == "doc":
                        assert "100" in after and "Betriebsjubiläen" in after
                        assert "KRN_EVIDENCE" not in after
                    if kind == "inv":
                        for doc in (await list_krn_docs())["documents"]:
                            assert doc["filename"] in after
            return
        except (TimeoutError, RealtimeError) as exc:
            last_error = exc
    assert last_error is not None
    raise last_error
