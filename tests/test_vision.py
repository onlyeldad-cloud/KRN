import asyncio

import pytest
from livekit import rtc
from livekit.agents import AgentSession, inference
from livekit.agents.voice import io

from agent import Assistant


class ColorVideo(io.VideoInput):
    """Synthetic video: exercises vision without accessing a real camera."""

    def __init__(self):
        super().__init__(label="synthetic-green-video")

    async def __anext__(self):
        await asyncio.sleep(0.5)
        return rtc.VideoFrame(
            320, 240, rtc.VideoBufferType.RGBA, bytes([0, 255, 0, 255]) * (320 * 240)
        )


@pytest.mark.asyncio
async def test_gemini_understands_video():
    async with (
        inference.LLM(model="google/gemma-4-31b-it") as judge,
        AgentSession() as session,
    ):
        session.input.video = ColorVideo()
        async with asyncio.timeout(90):
            greeting = await session.start(Assistant(), capture_run=True)
            await greeting
            # Give the video input time to deliver frames before asking.
            await asyncio.sleep(3)
            result = await session.run(
                user_input="Welche Farbe hat das Bild, das ich gerade teile?"
            )
            await (
                result.expect.next_event()
                .is_message(role="assistant")
                .judge(
                    judge, intent="Answers in German that the shared image is green."
                )
            )
