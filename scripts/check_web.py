"""Development smoke check. Requires the local web server and agent running."""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def main():
    artifacts = Path('artifacts')
    artifacts.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream']
        )
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 960}, permissions=['microphone', 'camera']
        )
        page = await context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:3000', timeout=120000)
        await page.get_by_role('button', name='Gespräch starten').wait_for(timeout=120000)
        await page.screenshot(path=str(artifacts / 'krn-desktop.png'))
        forbidden = await context.request.post('http://127.0.0.1:3000/api/token')
        assert forbidden.status == 403, forbidden.status
        print('Welcome page and token access checks passed', flush=True)
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.screenshot(path=str(artifacts / 'krn-mobile.png'))
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.set_viewport_size({'width': 1440, 'height': 960})
        await page.get_by_role('button', name='Gespräch starten').click()
        await page.wait_for_timeout(20000)
        print('After connect:', (await page.locator('body').inner_text())[:3000], flush=True)
        print('Buttons:', await page.get_by_role('button').evaluate_all(
            '(buttons) => buttons.map(b => ({text: b.textContent, label: b.getAttribute("aria-label"), title:b.title}))'
        ), flush=True)
        await page.screenshot(path=str(artifacts / 'krn-session.png'))
        assert not errors, errors
        print('No browser runtime errors', flush=True)
        await context.close()
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
