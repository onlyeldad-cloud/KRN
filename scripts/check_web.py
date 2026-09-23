"""Live browser check using synthetic microphone input and real agent audio."""

import asyncio
import os
import time
from pathlib import Path

from playwright.async_api import async_playwright


async def main():
    base = os.environ.get("KRN_WEB_URL", "http://127.0.0.1:3000")
    Path("artifacts").mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--autoplay-policy=no-user-gesture-required",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 960}, permissions=["microphone"]
        )
        await context.add_init_script("""
            window.krnPeers = [];
            const Original = window.RTCPeerConnection;
            window.RTCPeerConnection = class extends Original {
                constructor(...args) { super(...args); window.krnPeers.push(this); }
            };
        """)
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        started = time.monotonic()
        await page.goto(base, timeout=120000, wait_until="domcontentloaded")
        button = page.get_by_role("button", name="Gespräch starten")
        await button.wait_for(timeout=120000)
        print(f"Welcome ready in {time.monotonic() - started:.1f}s", flush=True)
        assert await page.locator('input[type="password"]').count() == 0
        token = await context.request.post(f"{base}/api/token", timeout=120000)
        assert token.status == 200, token.status
        if os.environ.get("KRN_CHECK_PRODUCTION") == "1":
            rejected = await context.request.post(
                f"{base}/api/token",
                headers={"Origin": "https://example.com", "Sec-Fetch-Site": "cross-site"},
            )
            assert rejected.status == 401, rejected.status
        started = time.monotonic()
        await button.click()
        try:
            await page.wait_for_function(
                """async () => {
                for (const peer of window.krnPeers) {
                    const stats = await peer.getStats();
                    for (const stat of stats.values()) {
                        if (stat.type === 'inbound-rtp' && stat.kind === 'audio'
                            && stat.totalAudioEnergy > 0) return true;
                    }
                }
                return false;
            }""",
                timeout=90000,
            )
            print(
                f"Agent audio received in {time.monotonic() - started:.1f}s", flush=True
            )
            await page.wait_for_timeout(5000)
            assert not await button.is_visible(), "Session returned to welcome screen"
            assert not errors, errors
            print(
                "Live session stayed connected; no browser runtime errors", flush=True
            )
        finally:
            print((await page.locator("body").inner_text())[:2000], flush=True)
            await page.screenshot(path="artifacts/krn-session.png")
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
