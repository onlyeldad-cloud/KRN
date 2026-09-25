from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from livekit.agents import AgentSession, inference
from livekit.agents.voice.speech_handle import SpeechHandle

from agent import (
    GREETING_TEXT,
    Assistant,
    attach_krn_live_router,
    greet_after_connect,
)
from krn_docs import is_krn_internal_question


def _done_handle() -> SpeechHandle:
    handle = SpeechHandle.create()
    handle._mark_done()
    return handle


@pytest.mark.asyncio
async def test_automatic_german_greeting():
    session = MagicMock()
    with patch.object(
        Assistant, "session", new_callable=PropertyMock, return_value=session
    ):
        await Assistant().on_enter()
    session.generate_reply.assert_not_called()
    session.say = MagicMock(return_value=_done_handle())
    await greet_after_connect(session)
    session.say.assert_called_once()
    assert session.say.call_args.args[0] == GREETING_TEXT
    session.generate_reply.assert_not_called()
    assert session._krn_greeting_active is False


@pytest.mark.asyncio
async def test_empty_final_transcript_does_not_suppress_greeting():
    session = MagicMock()
    session.current_agent = Assistant()
    session.interrupt = MagicMock()
    session.say = MagicMock(return_value=_done_handle())
    session._krn_greeting_active = True
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
    handler(MagicMock(transcript="", is_final=True))
    handler(MagicMock(transcript="   ", is_final=True))
    session.interrupt.assert_not_called()
    assert session._krn_turn_id == 0
    assert not is_krn_internal_question(GREETING_TEXT)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_input", "intent"),
    [
        (
            "Mein WLAN spinnt schon wieder, ich kenn mich damit gar nicht aus.",
            "Responds in everyday conversational German, with informal du, "
            "showing understanding and offering one easy next step or one clear "
            "question. Avoids technical jargon, bureaucratic wording, exaggerated "
            "slang, and a long troubleshooting list.",
        ),
        (
            "Hello! What can you help me with?",
            "Responds in natural German and briefly offers help. Uses informal du "
            "if addressing the user. Does not use a markdown list.",
        ),
        (
            "Wie heißt du und zu welcher Firma gehörst du?",
            "Identifies itself as KRN Agent, the digital assistant of the company "
            "KRN Agent. Responds briefly in German.",
        ),
        (
            "Hast du mein Support-Ticket schon angelegt?",
            "Does not claim to have created a ticket or accessed a ticket system. "
            "Honestly explains its limitation and offers help in German.",
        ),
    ],
)
@pytest.mark.live
async def test_german_support_behavior(user_input, intent):
    async with (
        inference.LLM(model="google/gemma-4-31b-it") as judge,
        AgentSession() as session,
    ):
        await session.start(Assistant())
        result = await session.run(user_input=user_input)
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                judge,
                intent=intent,
            )
        )
        result.expect.no_more_events()
