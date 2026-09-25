"""Conversation stability for KRN voice routing (no mic / RoomIO transport)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from livekit.agents.voice.speech_handle import SpeechHandle

from agent import (
    Assistant,
    attach_krn_live_router,
    deliver_krn_answer,
    krn_text_input,
)
from krn_docs import (
    RETRIEVAL_UNAVAILABLE_DE,
    is_krn_internal_question,
    short_krn_voice_answer,
)

ANNIVERSARY = "Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?"
ANNIVERSARY_EN = "What do I receive after 10 years of service?"
INVENTORY = "Welche internen KRN-Dokumente hast du?"
UNSUPPORTED = "Wie hoch ist die KRN-Prämie für die geheime Mondbasis?"
OTHER_DOC = "Was mache ich bei einem defekten EC-Gerät?"


def _done_handle() -> SpeechHandle:
    handle = SpeechHandle.create()
    handle._mark_done()
    return handle


def _session() -> MagicMock:
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.generate_reply = MagicMock()
    session._krn_turn_id = 0
    spoken: list[str] = []

    def capture_say(text, **_kwargs):
        spoken.append(text)
        return _done_handle()

    session.say = MagicMock(side_effect=capture_say)
    session._spoken = spoken  # type: ignore[attr-defined]
    return session


@pytest.mark.asyncio
async def test_sequential_conversation_no_duplicates_or_leaks():
    session = _session()
    turns = [
        ("Hallo, wie geht es dir?", False),
        (ANNIVERSARY, True),
        (INVENTORY, True),
        ("Wie ist das Wetter heute?", False),
        (ANNIVERSARY_EN, True),
        ("Danke.", False),
        (OTHER_DOC, True),
        (UNSUPPORTED, True),
    ]
    for text, is_doc in turns:
        assert is_krn_internal_question(text) is is_doc
        await krn_text_input(session, MagicMock(text=text))

    spoken = session._spoken
    # Document turns use session.say; chat/weather use generate_reply.
    assert len(spoken) == 5
    assert session.generate_reply.call_count == 3
    assert all("KRN_EVIDENCE" not in text for text in spoken)
    assert all("required_citation" not in text.lower() for text in spoken)
    assert all("END_EVIDENCE" not in text for text in spoken)
    assert "100" in spoken[0] and "25" in spoken[0] and "Betriebsjubiläen" in spoken[0]
    assert spoken[0].index("100") < spoken[0].index("25")
    assert spoken[0].count("[Quelle:") == 1
    assert any("Betriebsjubiläen" in text or ".pdf" in text for text in spoken[1:3])
    assert "EC" in spoken[3] or "Leitstelle" in spoken[3] or "bar" in spoken[3].lower()
    assert "nicht" in spoken[4].lower()
    assert "years of service" in spoken[2].lower() or "100" in spoken[2]
    assert "Source:" in spoken[2]


@pytest.mark.asyncio
async def test_fast_second_question_cancels_stale_answer():
    session = _session()
    # Simulate turn 1 still finishing while turn 2 is current.
    session._krn_turn_id = 2
    packed = await deliver_krn_answer(
        session,
        ANNIVERSARY,
        interrupt=True,
        turn_id=1,
        expected_turn_id=1,
    )
    assert packed["status"] == "stale"
    assert session._spoken == []


@pytest.mark.asyncio
async def test_router_final_only_one_say_per_document_turn():
    session = _session()
    handlers: dict[str, object] = {}

    def on(event, cb=None):
        if cb is None:

            def deco(fn):
                handlers[event] = fn
                return fn

            return deco
        handlers[event] = cb
        return cb

    session.on = on
    attach_krn_live_router(session)
    handler = handlers["user_input_transcribed"]

    # Noise / partials must not interrupt or speak.
    handler(MagicMock(transcript="Was bekomme", is_final=False))
    handler(MagicMock(transcript=ANNIVERSARY, is_final=False))
    session.interrupt.assert_not_called()
    assert session._spoken == []

    handler(MagicMock(transcript=ANNIVERSARY, is_final=True))
    await asyncio.sleep(0.05)
    # Allow the created task to finish.
    for _ in range(50):
        if session._spoken:
            break
        await asyncio.sleep(0.02)
    assert len(session._spoken) == 1
    assert session.say.call_count == 1
    assert session.generate_reply.call_count == 0


@pytest.mark.asyncio
async def test_conversation_continues_after_retrieval_failure(monkeypatch):
    session = _session()

    async def boom(_query: str):
        raise OSError("boom")

    monkeypatch.setattr("agent.retrieve_krn_for_voice", boom)
    await krn_text_input(session, MagicMock(text=ANNIVERSARY))
    assert session._spoken == [RETRIEVAL_UNAVAILABLE_DE]

    # Restore and continue with ordinary chat.
    monkeypatch.undo()
    await krn_text_input(session, MagicMock(text="Hallo, wie geht es dir?"))
    session.generate_reply.assert_called_with(user_input="Hallo, wie geht es dir?")


def test_greeting_and_weather_skip_krn_processing():
    assert not is_krn_internal_question("Hallo, wie geht es dir?")
    assert not is_krn_internal_question("Wie ist das Wetter heute?")
    assert is_krn_internal_question(ANNIVERSARY)
    assert is_krn_internal_question(INVENTORY)


def test_short_answer_never_leaks_markers():
    from krn_docs import search_krn_index

    packed = search_krn_index(ANNIVERSARY)
    text = short_krn_voice_answer(ANNIVERSARY, packed)
    for marker in (
        "KRN_EVIDENCE",
        "END_EVIDENCE",
        "required_citation",
        "question_language",
        "HIT 1",
    ):
        assert marker not in text
