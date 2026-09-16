import asyncio

import pytest
from livekit.agents import AgentSession, inference

from agent import Assistant


@pytest.mark.asyncio
async def test_does_not_reuse_old_camera_objects():
    async with (
        inference.LLM(model="google/gemma-4-31b-it") as judge,
        AgentSession() as session,
    ):
        async with asyncio.timeout(90):
            greeting = await session.start(Assistant(), capture_run=True)
            await greeting
            await session.run(
                user_input="Ich habe dir eben ein Handy vor die Kamera gehalten."
            )
            result = await session.run(
                user_input="Die Kamera ist jetzt aus. Was siehst du gerade in meiner Hand?"
            )
            await (
                result.expect[-1]
                .is_message(role="assistant")
                .judge(
                    judge,
                    intent=(
                        "Responds in German. Does not claim to currently see a phone, "
                        "laptop, bottle, or any object. Says it has no current camera "
                        "picture or that the camera is off. Does not treat the earlier "
                        "phone as still visible."
                    ),
                )
            )
