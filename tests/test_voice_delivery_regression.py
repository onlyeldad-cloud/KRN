from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent import _say_text
from krn_docs import is_krn_internal_question, is_krn_inventory_question


@pytest.mark.asyncio
async def test_document_tool_returns_complete_authoritative_answer():
    from krn_docs import search_krn_docs

    result = await search_krn_docs("was bekommen ich nach 10 Jahr bei KRN?")
    assert "100" in result["answer"]
    assert "BV_Regelung" in result["answer"]
    assert "Seite 3" in result["answer"]
    assert len(result["allowed_filenames"]) == 9
    assert "RNN_Preistabelle_2024_01.pdf" not in result["allowed_filenames"]


@pytest.mark.asyncio
async def test_native_audio_router_does_not_start_competing_generation():
    import asyncio

    from agent import attach_krn_live_router

    handlers = {}
    session = SimpleNamespace(
        on=lambda name: lambda callback: handlers.setdefault(name, callback),
        current_agent=SimpleNamespace(krn_internal_turn=False),
        interrupt=MagicMock(),
        say=MagicMock(),
        generate_reply=MagicMock(),
    )
    attach_krn_live_router(session, model_handles_audio=True)
    handlers["user_input_transcribed"](
        SimpleNamespace(
            transcript="What should I do if a card reader is broken?", is_final=True
        )
    )
    await asyncio.sleep(0)
    assert session.current_agent.krn_internal_turn
    session.interrupt.assert_not_called()
    session.say.assert_not_called()
    session.generate_reply.assert_not_called()


@pytest.mark.asyncio
async def test_realtime_without_tts_uses_supported_generation():
    session = SimpleNamespace(
        say=MagicMock(
            side_effect=RuntimeError(
                "trying to generate speech from text without a TTS model or a RealtimeSession that supports say(); add a TTS model to AgentSession to enable say()"
            )
        ),
        generate_reply=MagicMock(),
    )
    answer = "20 minutes. [Source: BV_Regelung von Fahrzeugverspätungen.pdf, page 3]"
    await _say_text(session, answer)
    session.generate_reply.assert_called_once()
    assert answer in session.generate_reply.call_args.kwargs["instructions"]
    assert session.generate_reply.call_args.kwargs["tool_choice"] == "none"


@pytest.mark.asyncio
async def test_unrelated_speech_failure_is_not_hidden():
    session = SimpleNamespace(say=MagicMock(side_effect=RuntimeError("session closed")))
    with pytest.raises(RuntimeError, match="session closed"):
        await _say_text(session, "Hallo")


def test_actual_spoken_school_question_routes_to_documents():
    assert is_krn_internal_question(
        "Darf ich eine Grundschule ohne gültige Ticket auf dem Schulwege stehen lassen?"
    )


def test_actual_spoken_inventory_question():
    assert is_krn_inventory_question(
        "Okay. Welche car er k r n Dokument hast du nehmen alles original Daten?"
    )


@pytest.mark.asyncio
async def test_incomplete_spoken_fare_question_asks_for_level():
    from krn_docs import search_krn_docs

    result = await search_krn_docs(
        "Was kostet eine 1? Einzelfahrkarte für Erwachsene in eine Preisstufe"
    )
    assert "Welche Preisstufe" in result["answer"]
    assert "keine Preise" not in result["answer"]


@pytest.mark.asyncio
async def test_unavailable_index_tool_fails_closed(monkeypatch):
    import krn_docs

    def unavailable():
        raise OSError("index unavailable")

    monkeypatch.setattr(krn_docs, "load_search_bundle", unavailable)
    result = await krn_docs.search_krn_docs("KRN 10 Jahre")
    assert result["status"] == "unavailable"
    assert result["allowed_filenames"] == []
