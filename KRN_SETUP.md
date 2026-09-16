# KRN Agent: local web and phone development

KRN uses Gemini Live with the Charon voice, natural German instructions, automatic
German greeting, live video input, web search, Open-Meteo weather, and an isolated
Playwright browser. The web and Flutter interfaces are adapted from
[jarvis-voice-butler](https://github.com/ruxakK/jarvis-voice-butler).
Nothing has been deployed to production or an app store.

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
`start-agent.cmd` uses `.venv-windows` instead.

Open <http://127.0.0.1:3000> and select **Gespräch starten**. Allow microphone
access. Text chat can be used alongside voice. Camera input is currently off in
the agent because video encoding on Windows stalled speech; screen share in the
web UI still works for the participant, but the agent will not describe the
picture until that is re-enabled.

Try: “Wie ist das Wetter in Berlin?”, “Suche die offizielle LiveKit-Dokumentation”,
“Öffne example.com im Browser”, or “Zeig mir einen Screenshot des Browsers”.
A **separate Chromium or Chrome window** should appear on this PC; that is the
isolated KRN browser, not the KRN welcome tab. Clicks, typing, and Enter require
**Einmal erlauben** in the app. The browser has its own temporary session; it
does not control your personal Chrome profile or inherit passwords.
Private/local addresses and file URLs are blocked. This is a personal
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

The launch script selects `.venv-windows`. For manual commands:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows'
uv sync --locked
uv run python src/agent.py dev
# For hot reload, prefer: lk agent dev
```

If recreating only this optional environment on this PC:

```powershell
uv venv --python "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" .venv-windows
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows'
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

The token endpoint allows same-origin development web requests or the personal
mobile bearer token. It is deliberately disabled in production until actual user
authentication is implemented. A compiled mobile development token is extractable:
do not distribute development builds publicly. The provider credentials stay on
the server.

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
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows'
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
