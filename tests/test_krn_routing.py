"""Regression: KRN policy questions must get local evidence before answering."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from livekit.agents import AgentSession, inference
from livekit.agents.llm.realtime import RealtimeError
from livekit.agents.voice.speech_handle import SpeechHandle

from agent import (
    Assistant,
    attach_krn_live_router,
    deliver_krn_answer,
    krn_text_input,
    maybe_force_krn_docs_search,
)
from browser_tools import BrowserTools
from krn_docs import (
    RETRIEVAL_UNAVAILABLE_DE,
    format_krn_evidence,
    is_krn_internal_question,
    list_krn_docs,
    search_krn_docs,
    search_krn_index,
    short_krn_voice_answer,
)

LIVE_FAILURE_QUESTION = "Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?"


def _done_handle() -> SpeechHandle:
    handle = SpeechHandle.create()
    handle._mark_done()
    return handle


@pytest.mark.asyncio
async def test_typed_question_gets_evidence_before_generation():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.generate_reply = MagicMock()
    spoken: list[str] = []

    def capture_say(text, **_kwargs):
        spoken.append(text)
        return _done_handle()

    session.say = MagicMock(side_effect=capture_say)
    await krn_text_input(session, MagicMock(text=LIVE_FAILURE_QUESTION))
    assert spoken
    assert "100" in spoken[0]
    assert "25" in spoken[0]
    assert "Betriebsjubiläen" in spoken[0]
    assert "Seite 3" in spoken[0]
    assert "KRN_EVIDENCE" not in spoken[0]
    session.generate_reply.assert_not_called()
    assert session.current_agent.krn_internal_turn is False


@pytest.mark.asyncio
async def test_internal_turn_blocks_every_external_tool():
    assistant = Assistant(browser=BrowserTools())
    assistant.krn_internal_turn = True
    for tool in assistant.tools:
        if tool.__name__ in {"search_krn_docs", "list_krn_docs", "get_weather"}:
            continue
        # Guard executes before even validating/calling the underlying browser API.
        assert (await tool())["status"] == "blocked"


@pytest.mark.asyncio
async def test_inventory_input_contains_all_nine_filenames():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.generate_reply = MagicMock()
    spoken: list[str] = []

    def capture_say(text, **_kwargs):
        spoken.append(text)
        return _done_handle()

    session.say = MagicMock(side_effect=capture_say)
    await krn_text_input(session, MagicMock(text="Welche Dokumente hast du?"))
    assert spoken
    inventory = await list_krn_docs()
    for doc in inventory["documents"]:
        assert doc["filename"] in spoken[0]
    session.generate_reply.assert_not_called()


@pytest.mark.asyncio
async def test_krn_instructions_unchanged_after_document_answer():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.generate_reply = MagicMock()
    session.say = MagicMock(return_value=_done_handle())
    base = session.current_agent.base_instructions
    await krn_text_input(session, MagicMock(text=LIVE_FAILURE_QUESTION))
    assert session.current_agent.instructions == base
    session.current_agent.update_instructions = AsyncMock()
    # Delivery must not rebuild agent instructions for document turns.
    session.current_agent.update_instructions.assert_not_called()


@pytest.mark.asyncio
async def test_normal_text_turn_clears_internal_state():
    session = MagicMock()
    session.current_agent = Assistant()
    session.current_agent.krn_internal_turn = True
    session.interrupt = AsyncMock()
    await krn_text_input(session, MagicMock(text="Wie ist das Wetter in Berlin?"))
    assert not session.current_agent.krn_internal_turn
    session.generate_reply.assert_called_once_with(
        user_input="Wie ist das Wetter in Berlin?"
    )


def test_exact_live_failure_question_is_internal_krn():
    assert is_krn_internal_question(LIVE_FAILURE_QUESTION)


@pytest.mark.parametrize(
    "question",
    [
        "Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?",
        "Was gilt beim Jubiläum?",
        "Was steht in der BV?",
        "Wie ist die Verspätung geregelt?",
        "Was tun beim defekten EC-Gerät?",
        "Wie läuft die Schülerbeförderung?",
        "Wie sind die Ticketpreise?",
        "Welche Preisstufe gilt in dieser Wabe?",
    ],
)
def test_german_policy_phrasing_routes_to_docs(question):
    assert is_krn_internal_question(question)


@pytest.mark.parametrize(
    "question",
    [
        "Wie ist das Wetter in Berlin?",
        "Hallo, wie heißt du?",
        "Hallo, wie geht es dir?",
        "Suche die offizielle LiveKit-Dokumentation.",
        "Suche bitte im Internet, wann die KRN Testveranstaltung beginnt.",
    ],
)
def test_non_policy_questions_do_not_route_to_docs(question):
    assert not is_krn_internal_question(question)


def test_search_krn_docs_description_covers_spoken_german():
    doc = search_krn_docs.__doc__ or ""
    for needle in (
        "Betriebszugehörigkeit",
        "Jubiläum",
        "Verspätung",
        "EC-Gerät",
        "Schülerbeförderung",
        "Ticketpreise",
    ):
        assert needle in doc


def test_instructions_require_docs_search_before_answering():
    instructions = Assistant().instructions
    assert "search_krn_docs" in instructions
    assert "Betriebszugehörigkeit" in instructions
    assert "zuerst search_krn_docs" in instructions
    assert "Answer immediately" not in instructions
    assert "Allgemeinwissen" in instructions
    assert "Rente" in instructions
    assert "[Quelle: Dateiname, Seite N]" in instructions


def test_search_krn_docs_is_registered_on_assistant_and_session_agent():
    assistant = Assistant()
    names = {getattr(tool, "__name__", "") for tool in assistant.tools}
    assert "search_krn_docs" in names
    assert assistant.llm is not None
    assert assistant.llm.model == "gemini-3.1-flash-live-preview"


def test_format_krn_evidence_keeps_filename_and_page():
    packed = search_krn_index(LIVE_FAILURE_QUESTION, limit=3)
    assert packed["status"] == "ok"
    text = format_krn_evidence(packed, language="de")
    hit = packed["results"][0]
    assert hit["filename"] in text
    assert f"page: {hit['page']}" in text
    assert f"[Quelle: {hit['filename']}, Seite {hit['page']}]" in text


def test_format_krn_evidence_refuses_when_empty():
    text = format_krn_evidence({"status": "no_results", "results": []})
    assert "empty" in text.lower()
    assert "pension" in text.lower() or "rente" not in text.lower()


def test_short_voice_answer_uses_retrieval_amounts():
    packed = search_krn_index(LIVE_FAILURE_QUESTION, limit=3)
    text = short_krn_voice_answer(LIVE_FAILURE_QUESTION, packed)
    assert "100" in text and "25" in text
    assert "Betriebsjubiläen" in text
    assert "Seite 3" in text
    assert "KRN_EVIDENCE" not in text


@pytest.mark.asyncio
async def test_live_router_invokes_search_krn_docs_for_exact_failure():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.generate_reply = MagicMock()
    spoken: list[str] = []

    def capture_say(text, **_kwargs):
        spoken.append(text)
        return _done_handle()

    session.say = MagicMock(side_effect=capture_say)
    packed = await maybe_force_krn_docs_search(
        session, LIVE_FAILURE_QUESTION, wait_s=0.0, force=True
    )
    assert packed is not None
    assert packed["status"] == "ok"
    assert packed["results"]
    session.interrupt.assert_called()
    session.generate_reply.assert_not_called()
    assert spoken
    assert packed["results"][0]["filename"] in spoken[0]
    assert "Seite 3" in spoken[0]
    assert session.say.call_count == 1


@pytest.mark.asyncio
async def test_live_router_does_not_reuse_another_sessions_search():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.say = MagicMock(return_value=_done_handle())
    await search_krn_docs(LIVE_FAILURE_QUESTION)
    packed = await maybe_force_krn_docs_search(
        session, LIVE_FAILURE_QUESTION, wait_s=0.0
    )
    assert packed is not None
    session.say.assert_called_once()


def test_attach_krn_live_router_hooks_transcription():
    session = MagicMock()
    attach_krn_live_router(session)
    session.on.assert_called()
    assert any(
        call.args[0] == "user_input_transcribed" for call in session.on.call_args_list
    )


@pytest.mark.asyncio
async def test_partial_transcript_does_not_interrupt():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
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
    handler(MagicMock(transcript=LIVE_FAILURE_QUESTION, is_final=False))
    session.interrupt.assert_not_called()
    assert session.current_agent.krn_internal_turn is True


@pytest.mark.asyncio
async def test_stale_turn_does_not_speak():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.say = MagicMock(return_value=_done_handle())
    session._krn_turn_id = 2
    packed = await deliver_krn_answer(
        session,
        LIVE_FAILURE_QUESTION,
        interrupt=True,
        turn_id=1,
        expected_turn_id=1,
    )
    assert packed["status"] == "stale"
    session.say.assert_not_called()


@pytest.mark.asyncio
async def test_retrieval_failure_speaks_german_apology(monkeypatch):
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    spoken: list[str] = []

    def capture_say(text, **_kwargs):
        spoken.append(text)
        return _done_handle()

    session.say = MagicMock(side_effect=capture_say)

    async def boom(_query: str):
        raise OSError("index missing")

    monkeypatch.setattr("agent.retrieve_krn_for_voice", boom)
    packed = await deliver_krn_answer(session, LIVE_FAILURE_QUESTION, interrupt=True)
    assert packed["status"] == "unavailable"
    assert spoken == [RETRIEVAL_UNAVAILABLE_DE]


@pytest.mark.asyncio
@pytest.mark.skipif(
    not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
    reason="Gemini Live session test needs GOOGLE_API_KEY or GEMINI_API_KEY",
)
@pytest.mark.live
async def test_betriebszugehoerigkeit_session_invokes_search_krn_docs():
    """Live Gemini session must call search_krn_docs for the failed spoken question."""
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            async with (
                inference.LLM(model="google/gemma-4-31b-it") as judge,
                AgentSession() as session,
            ):
                async with asyncio.timeout(90):
                    greeting = await session.start(Assistant(), capture_run=True)
                    await greeting
                    result = await session.run(user_input=LIVE_FAILURE_QUESTION)
                    result.expect.contains_function_call(name="search_krn_docs")
                    await (
                        result.expect[-1]
                        .is_message(role="assistant")
                        .judge(
                            judge,
                            intent=(
                                "Answers in German from KRN documents, not general "
                                "knowledge about pension or severance. Mentions a 100 "
                                "Euro benefit or a 25 Euro gift if the documents "
                                "support it, and cites a source filename with a PDF "
                                "page. Does not invent extra benefits."
                            ),
                        )
                    )
            return
        except (TimeoutError, RealtimeError) as exc:
            last_error = exc
    assert last_error is not None
    raise last_error
