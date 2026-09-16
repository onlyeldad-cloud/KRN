from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from livekit.agents import AgentSession, inference

from agent import GREETING_INSTRUCTIONS, Assistant, greet_after_connect


@pytest.mark.asyncio
async def test_automatic_german_greeting():
    session = MagicMock()
    with patch.object(
        Assistant, "session", new_callable=PropertyMock, return_value=session
    ):
        await Assistant().on_enter()
    session.generate_reply.assert_not_called()
    await greet_after_connect(session)
    session.generate_reply.assert_called_once_with(
        instructions=GREETING_INSTRUCTIONS,
    )
    session.say.assert_not_called()


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
