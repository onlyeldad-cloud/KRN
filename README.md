<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# LiveKit Agents Starter - Python

**KRN web app and Android/iPhone setup:** see [KRN_SETUP.md](KRN_SETUP.md).
On this Windows PC use `start-agent.ps1` and `start-web.ps1`; the agent script
selects the separate environment that avoids the Windows-blocked XML module.

## KRN Agent: Gemini Live and cameras

KRN can also search the internet with the `search_web` tool using
`langchain-community` and `ddgs` (no separate search API key). Ask, for example:
“Suche im Internet nach der offiziellen LiveKit-Dokumentation.” Results contain
up to five titles, source links, and snippets; the tool does not read full pages.
Search runs outside the audio event loop with a 20-second response timeout.
Unavailable or empty results are reported explicitly. Queries go to external
search providers, so do not include confidential data.

Run offline search checks with `uv run pytest tests/test_web_search.py -q`.
`tests/test_search_behavior.py` additionally uses a real Gemini session with
mock search results to verify tool calling and German answers (inference usage).

KRN now uses `gemini-3.1-flash-live-preview` with the `Charon` voice,
German instructions, and live video input. Gemini handles speech recognition,
responses, audio output, and turn detection. The original template description
below describes the former STT/LLM/TTS pipeline.

Set `GOOGLE_API_KEY` in `.env.local`, alongside the three LiveKit credentials
listed in `.env.example`. Keep this file private. The Google plugin must be
version 1.8.2 or later for Gemini 3.1's mid-session updates and greeting.

From the `KRN` directory:

```powershell
uv sync --locked
lk agent dev
```

Connect a browser frontend to the configured LiveKit project and dispatch name
`my-agent`. The spoken assistant/company name is **KRN Agent**; the dispatch name
remains unchanged so existing console links continue to work.

For camera use:

1. Connect your USB webcam, if using an external camera.
2. In your browser frontend, allow microphone/camera access and publish your
   camera track. Choose the built-in camera or USB webcam in its device selector
   (or the browser's camera settings if the frontend has no selector).
3. Ask in German, for example: “Was siehst du gerade?”
4. To switch cameras, choose the other device and republish/reconnect if needed.

The backend receives video published by the connected participant; it does not
open Windows camera devices itself. One video track is used at a time (the most
recently published camera or screen share). A network/IP camera requires a
separate publisher or virtual-camera integration and is not configured here.
Use a camera-capable frontend if your console view does not offer video
publishing. Camera permission alone does not publish a track.

See [LiveKit video input](https://docs.livekit.io/agents/multimodality/vision/video/)
and [Gemini Live configuration](https://docs.livekit.io/agents/models/realtime/plugins/gemini/).

Validation: `uv run pytest tests/test_german.py tests/test_vision.py -q` uses
configured Google and LiveKit credentials and incurs inference usage. The vision
test sends synthetic green frames, not images from your physical camera.

A complete starter project for building voice AI apps with [LiveKit Agents for Python](https://github.com/livekit/agents) and [LiveKit Cloud](https://cloud.livekit.io/).

The starter project includes:

- A simple voice AI assistant, ready for extension and customization
- A voice AI pipeline built on [LiveKit Inference](https://docs.livekit.io/agents/models/inference), providing zero-configuration access to [models](https://docs.livekit.io/agents/models) from top labs
  - Uses the fast, open-weight Gemma 4 31B model, [hosted by LiveKit](https://docs.livekit.io/agents/models/llm/livekit/) and tuned for optimal performance in voice AI, as the default LLM
  - Uses Fish Audio S2.1 Pro for TTS, which renders the inline delivery markup that expressive mode relies on
  - Supports more than 50 models from OpenAI, Cartesia, Deepgram, and other providers
  - Access to a wide range of other models, including [Realtime models](https://docs.livekit.io/agents/models/realtime), through extensive plugin ecosystem
- Expressive mode, enabled by default: the framework injects the TTS provider's markup guide into the LLM prompt, so the model emits inline delivery tags (emotion, pacing, non-verbal sounds) that the TTS renders and the transcript never shows
- Eval suite based on the LiveKit Agents [testing & evaluation framework](https://docs.livekit.io/agents/start/testing/)
- [LiveKit Turn Detector](https://docs.livekit.io/agents/logic/turns/turn-detector/), an end-of-turn model that listens to the user's audio directly, combining semantic understanding with acoustic cues for state-of-the-art accuracy across 14 languages
- [Background voice cancellation](https://docs.livekit.io/transport/media/noise-cancellation/)
- Deep session insights from LiveKit [Agent Observability](https://docs.livekit.io/deploy/observability/)
- A Dockerfile ready for [production deployment to LiveKit Cloud](https://docs.livekit.io/deploy/agents/)

This starter app is compatible with any [custom web/mobile frontend](https://docs.livekit.io/frontends/) or [telephony](https://docs.livekit.io/telephony/).

## Using coding agents

This project is designed to work with coding agents like [Claude Code](https://claude.com/product/claude-code), [Cursor](https://www.cursor.com/), and [Codex](https://openai.com/codex/).

For your convenience, LiveKit offers both a CLI and an [MCP server](https://docs.livekit.io/reference/developer-tools/docs-mcp/) that can be used to browse and search its documentation. The [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/) (`lk docs`) works with any coding agent that can run shell commands. Install it for your platform:

**macOS:**

```console
brew install livekit-cli
```

**Linux:**

```console
curl -sSL https://get.livekit.io/cli | bash
```

**Windows:**

```console
winget install LiveKit.LiveKitCLI
```

The `lk docs` subcommand requires version 2.15.0 or higher. Check your version with `lk --version` and update if needed. Once installed, your coding agent can search and browse LiveKit documentation directly from the terminal:

```console
lk docs search "voice agents"
lk docs get-page /agents/start/voice-ai-quickstart
```

See the [Using coding agents](https://docs.livekit.io/intro/coding-agents/) guide for more details, including MCP server setup.

The project includes a complete [AGENTS.md](AGENTS.md) file for these assistants. You can modify this file to suit your needs. To learn more about this file, see [https://agents.md](https://agents.md).

## Dev Setup

Create a project from this template with the LiveKit CLI (recommended):

```bash
lk cloud auth
lk agent init my-agent --template agent-starter-python
```

The CLI clones the template and configures your environment. Then follow the rest of this guide from [Run the agent](#run-the-agent).

<details>
<summary>Alternative: Manual setup without the CLI</summary>

Clone the repository and install dependencies to a virtual environment:

```console
cd agent-starter-python
uv sync
```

Sign up for [LiveKit Cloud](https://cloud.livekit.io/) then set up the environment by copying `.env.example` to `.env.local` and filling in the required keys:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

You can load the LiveKit environment automatically using the [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/):

```bash
lk cloud auth
lk app env --write --destination .env.local
```

</details>

## Run the agent

### Windows native runtime prerequisite

Install the current **x64 Microsoft Visual C++ v14 Redistributable** from
[Microsoft's official download page](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
Restart Windows if the installer requests it.

On this machine, `livekit-local-inference==0.2.7` crashed during import with
`0xc0000005` in `C:\Windows\System32\MSVCP140.dll` version `14.0.23026.0`.
Updating the runtime to `14.51.36247.0` fixed the import and native VAD/EOT
inference with Python 3.12.14 and LiveKit Agents 1.8.2. No Python version change,
package downgrade, or edits to installed packages were needed.

From the `KRN` directory, verify startup with:

```powershell
uv run python -X faulthandler -c "import livekit.local_inference; import livekit.agents; print('LiveKit imports OK')"
uv run python src/agent.py dev
```

Wait for `registered worker` before connecting a frontend. Agents 1.8.2 recommends
`lk agent dev` for development with hot reload; the Python `dev` command still
starts the worker but is deprecated. These commands run the backend; open the
[LiveKit Cloud agent console](https://cloud.livekit.io/projects/p_/agents/console)
separately, select the configured project, and use agent name `my-agent` (the
name currently registered by `src/agent.py`).

Run this command to speak to your agent directly in your terminal:

```console
uv run python src/agent.py console
```

To run the agent for use with a frontend or telephony, use the `dev` command:

```console
uv run python src/agent.py dev
```

In production, use the `start` command:

```console
uv run python src/agent.py start
```

## Frontend & Telephony

Get started quickly with our pre-built frontend starter apps, or add telephony support:

| Platform | Link | Description |
|----------|----------|-------------|
| **Web** | [`livekit-examples/agent-starter-react`](https://github.com/livekit-examples/agent-starter-react) | Web voice AI assistant with React & Next.js |
| **iOS/macOS** | [`livekit-examples/agent-starter-swift`](https://github.com/livekit-examples/agent-starter-swift) | Native iOS, macOS, and visionOS voice AI assistant |
| **Flutter** | [`livekit-examples/agent-starter-flutter`](https://github.com/livekit-examples/agent-starter-flutter) | Cross-platform voice AI assistant app |
| **React Native** | [`livekit-examples/voice-assistant-react-native`](https://github.com/livekit-examples/voice-assistant-react-native) | Native mobile app with React Native & Expo |
| **Android** | [`livekit-examples/agent-starter-android`](https://github.com/livekit-examples/agent-starter-android) | Native Android app with Kotlin & Jetpack Compose |
| **Web Embed** | [`livekit-examples/agent-starter-embed`](https://github.com/livekit-examples/agent-starter-embed) | Voice AI widget for any website |
| **Telephony** | [Documentation](https://docs.livekit.io/telephony/) | Add inbound or outbound calling to your agent |

For advanced customization, see the [complete frontend guide](https://docs.livekit.io/frontends/).

## Tests and evals

Simulations run full multi-turn conversations between a simulated user and your agent on LiveKit Cloud, then judge each transcript. The scenarios live in [`scenarios.yaml`](scenarios.yaml). Run them locally with the [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/):

```console
lk agent simulate --scenarios scenarios.yaml
```

The `Simulations` workflow in `.github/workflows/simulations.yml` runs the same file on every merge to `main` and on demand from the Actions tab. It runs there rather than on every pull request push because each run spends real inference. See the [simulations guide](https://docs.livekit.io/agents/start/testing/simulations/) for how to write scenarios and read results.

For turn-level checks that don't need a live session, the LiveKit Agents [testing & evaluation framework](https://docs.livekit.io/agents/start/testing/) runs your agent in-process under `pytest`. A commented-out example lives in [`tests/test_agent.py`](tests/test_agent.py).

## Using this template repo for your own project

Once you've started your own project based on this repo, you should:

1. **Check in your `uv.lock`**: This file is currently untracked for the template, but you should commit it to your repository for reproducible builds and proper configuration management. (The same applies to `livekit.toml`, if you run your agents in LiveKit Cloud)

2. **Add your own repository secrets**: You must [add secrets](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-what-your-workflow-does/using-secrets-in-github-actions) for `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` so that the simulations can run in CI.

## Deploying to production

This project is production-ready and includes a working `Dockerfile`. To deploy it to LiveKit Cloud or another environment, see the [deploying to production](https://docs.livekit.io/deploy/agents/) guide.

## Self-hosted LiveKit

You can also self-host LiveKit instead of using LiveKit Cloud. See the [self-hosting](https://docs.livekit.io/transport/self-hosting/local/) guide for more information. If you choose to self-host, you'll need to also use [model plugins](https://docs.livekit.io/agents/models/#plugins) instead of LiveKit Inference and will need to remove the [LiveKit Cloud noise cancellation](https://docs.livekit.io/transport/media/noise-cancellation/) plugin.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
