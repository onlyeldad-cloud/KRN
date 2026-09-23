# KRN Agent: local web and phone development

KRN uses Gemini Live with the Charon voice, natural German instructions, automatic
German greeting, live video input, web search, Open-Meteo weather, and an isolated
Playwright browser. The web and Flutter interfaces are adapted from
[jarvis-voice-butler](https://github.com/ruxakK/jarvis-voice-butler).
A hosted demo (password-gated Vercel + LiveKit Cloud agent) is wired for GitHub
Actions; complete the first `lk agent create` and Vercel project secrets to go live.

## Start on this Windows PC

Open two PowerShell terminals in the `KRN` folder:

If PowerShell says running scripts is disabled, use the `.cmd` launchers
instead (they only bypass the policy for this start command):

```powershell
# Terminal 1: stop an older agent with Ctrl+C first to avoid duplicate workers.
.\start-agent.cmd
```

```powershell
# Terminal 2
.\start-web.cmd
```

Do not run `lk agent dev` by itself. That command uses `.venv` (Python 3.12),
which is missing Playwright and blocked from loading `pyexpat` on this PC.
`start-agent.cmd` uses `.venv-windows313` instead.

Open <http://127.0.0.1:3000> and select **Gespräch starten**. Allow microphone
access. Text chat can be used alongside voice. Turn the camera on only when you
want KRN to describe what you are holding; it uses the current frame, not
earlier objects from the same call. If speech starts breaking up, turn the
camera off again.

Normal `start-web.cmd` now builds the app once and reuses the compiled build
until source/configuration files change. The first build takes longer; later
starts do not compile pages or the token endpoint on the first request.
For UI development with hot reload, run
`powershell -ExecutionPolicy Bypass -File .\start-web.ps1 -Dev` instead.
Run only one frontend at a time; the launcher always uses port 3000.
The local launcher enables password-free loopback access (`KRN_LOCAL_MODE=true`)
and does not show a demo password field. Hosted demo authentication remains
optional for a public Vercel URL.
The backend keeps one runner warm and allows 120 seconds for cold Windows
initialization, preventing the previous 10-second initialization timeout.

To verify a real call with synthetic microphone input and incoming agent audio:
`uv run python scripts/check_web.py` (uses configured LiveKit/Google services).

Try: “Wie ist das Wetter in Berlin?”, “Suche die offizielle LiveKit-Dokumentation”,
“Öffne example.com im Browser”, or “Zeig mir einen Screenshot des Browsers”.
A **separate Chromium or Chrome window** should appear on this PC; that is the
isolated KRN browser, not the KRN welcome tab. Clicks, typing, and Enter run
immediately (no **Einmal erlauben** prompt). Set `KRN_BROWSER_REQUIRE_APPROVAL=1`
before `start-agent` if you want those prompts back. The browser has its own
temporary session; it does not control your personal Chrome profile or inherit
passwords. Private/local addresses and file URLs are blocked. This is a personal
development tool, not a multi-tenant browser sandbox.

## OpenCode, Big Pickle, and MCP

Coding agents (OpenCode and Cursor) get LiveKit docs and isolated Chrome here.
This is **not** the voice conversation; do not add these MCP tools to Gemini Live.

1. Install [OpenCode](https://opencode.ai) (`npm install -g opencode-ai@latest` in PowerShell
   if `opencode` is not on PATH). Keep Node.js/`npx` plus Google Chrome on this PC.
2. From the `KRN` folder run `opencode`. The project file `opencode.json` selects
   `opencode/big-pickle` and these MCP servers:
   - `livekit-docs` — `https://docs.livekit.io/mcp` (full current LiveKit docs)
   - `chrome-devtools` — Google Chrome DevTools MCP, `--isolated` (not your login Chrome)
   - `playwright` — `@playwright/mcp` with the Chrome channel
3. Confirm with `opencode mcp list`. Cursor loads the same servers from `.cursor/mcp.json`
   (reload MCP / restart Cursor if they do not appear).
4. If both browser MCPs fight over Chrome, set `"disabled": true` on `playwright` in
   `opencode.json` and keep `chrome-devtools`.

Big Pickle is OpenCode Zen’s free stealth model; their terms may allow using traffic
to improve it. Change `"model"` in `opencode.json` if you want a different provider.

## Windows Security workaround

Windows Code Integrity logs showed that Smart App Control blocked `pyexpat.pyd`
from uv's managed Python 3.12.14 distribution. A separate `.venv-windows` was
created using the existing official Python 3.14.7 installation, whose XML module
loads successfully. Both XML and LiveKit imports were verified. The original
`.venv` is preserved and Windows security settings were not disabled.
This addresses the new module-blocking message; it is separate from the earlier
LiveKit native-library crash fixed by updating the Microsoft C++ runtime.

On 2026-09-23, Smart App Control also blocked the Python 3.14 gRPC binary (`cygrpc.cp314-win_amd64.pyd`). The launcher now uses `.venv-windows313`, created with official Python 3.13.15 through Python Install Manager. XML, gRPC, LiveKit, and Google plugin imports passed with the same locked dependencies. Both previous environments are preserved; Windows security settings remain unchanged.

The launch script selects `.venv-windows313`. For manual commands:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv sync --locked
uv run python src/agent.py dev
# For hot reload, prefer: lk agent dev
```

If recreating only this optional environment on this PC:

```powershell
py install 3.13
uv venv --python "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" .venv-windows313
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv sync --locked
uv run playwright install chromium
```

## Credentials and dependencies

Keep LiveKit and Google credentials in the root `.env.local`. Run
`uv run python scripts/configure_frontend.py` with the environment selected above
after changing LiveKit credentials. This writes server credentials to
`frontend/.env.local` and a separate random development access token to
`mobile/assets/.env`; it never copies the Google key into either app.
These files are ignored by Git. Rotate any credential exposed in a screenshot.

The token endpoint allows same-origin development web requests, the personal
mobile bearer token, or the shared `KRN_DEMO_PASSWORD` on the hosted demo.
Do not send an open link without that password. A compiled mobile development
token is extractable: do not distribute development builds publicly. Provider
credentials stay on the server.

## Hosted demo for your boss

The welcome screen has a demo password. On Vercel set `KRN_DEMO_PASSWORD` and
`NEXT_PUBLIC_KRN_REQUIRES_PASSWORD=true`. Voice, chat, weather, search, and
camera work in the browser. Isolated Chrome still runs on the **agent host**
(LiveKit Cloud), not on your boss’s PC.

Push to `main` or `cursor/krn-web-browser-and-mobile` runs
`.github/workflows/deploy-demo.yml` after the first cloud agent exists.

First-time create (this PC, LiveKit CLI already logged in as `krn-01`):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create-hosted-demo.ps1
```

Commit the generated `livekit.toml`. Then add GitHub Actions secrets and a Vercel
project for `frontend` so later pushes update the live demo automatically.

Add these GitHub Actions secrets on `onlyeldad-cloud/KRN`:
`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`,
`VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.

On Vercel also set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`,
`KRN_DEMO_PASSWORD`, and `NEXT_PUBLIC_KRN_REQUIRES_PASSWORD=true`.

Send your boss the Vercel URL plus the demo password (not the GitHub repo).
After you push code, wait for the Actions run to finish, then they refresh.

The web app uses npm and Node 24. Reinstall with `npm ci` in `frontend`.
`npm run build` checks compilation; use `npm run dev` for the development token
endpoint. The PostCSS override keeps Next 15's nested dependency on a patched
compatible release. Do not reintroduce the upstream pnpm lockfile.

## Android and iPhone source projects

`mobile` contains Flutter source with Android and iOS projects, KRN branding,
German welcome text, voice/chat/camera, browser approval, and browser previews.
The development bundle/application identifier is `com.krn.agent`; choose a
unique identifier you own before publishing. Flutter is not installed on this PC,
so native binaries have not been compiled or device-tested here.

Install Flutter stable and the Android SDK, then:

```powershell
cd mobile
flutter doctor
flutter pub get
flutter analyze
flutter run
# Optional local APK after resolving any doctor/analyzer findings:
flutter build apk --debug
```

For the Android emulator, `mobile/assets/.env` defaults to
`KRN_TOKEN_ENDPOINT=http://10.0.2.2:3000/api/token`. Start the web development server
bound to `0.0.0.0` when using an emulator or another device:
`npm run dev -- --hostname 0.0.0.0`. HTTP is allowed only in Android debug builds.
Restrict access to your trusted development network.

For a physical phone, configure a reachable **HTTPS** development endpoint in
`KRN_TOKEN_ENDPOINT`, keeping the bearer token matched with the web server.
The phone cannot reach the PC through its own `localhost`. Browser microphone
and camera access also require HTTPS outside localhost. No public tunnel has
been created automatically. The web manifest supports home-screen use; this is
an online app, not an offline voice assistant.

iPhone builds require macOS, Xcode, a signing team, and a connected device:
run `flutter pub get`, open `ios/Runner.xcworkspace`, set Signing & Capabilities,
then use `flutter run`. App Store/TestFlight and Play Store releases are separate
steps and have not been attempted. Native screen broadcasting is not configured;
use the web app for screen sharing.

## Checks

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv run python -c "import pyexpat, livekit.agents; print('Imports OK')"
uv run pytest tests/test_browser.py tests/test_weather.py tests/test_web_search.py -q
uv run ruff check src tests scripts
cd frontend
npm run build
npm audit
```

German, search-behavior, and vision tests use live model services and incur normal
inference usage. The local browser tests use the installed Playwright Chromium.
Weather uses Open-Meteo's public development/non-commercial API; review its usage
terms and obtain an appropriate plan before commercial deployment.

See [THIRD_PARTY.md](THIRD_PARTY.md) for upstream attribution.
