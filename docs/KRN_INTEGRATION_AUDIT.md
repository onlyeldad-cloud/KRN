# KRN integration audit — 24 September 2026

This audit concerns the existing LiveKit/Gemini Live agent. The transfer documents were treated as background and source material; their older instructions to stop after planning or replace frontend features were not adopted.

## Root cause and verified architecture

`src/agent.py` constructs `Assistant`, registers its tools, and passes it to `AgentSession.start`. Gemini Live remains `gemini-3.1-flash-live-preview`, voice Charon. The Next.js and Flutter clients, Entra authentication, weather and existing browser implementations are unchanged.

The original incident has no supplied runtime trace, so its exact execution cannot be reconstructed. The inspected implementation had these demonstrable gaps:

- Search was registered, but registration and a prompt do not force Gemini to call it. The installed Google plugin explicitly does not support required/per-response tool choice.
- The voice fallback waited 700 ms after final transcription. A general-knowledge answer could already have started.
- A process-global two-second search timestamp could suppress retrieval for a different question or another session.
- Typed chat used the default RoomIO callback and bypassed the added voice router.
- There was no inventory tool. A top-five chunk search cannot enumerate nine source documents.
- German-only response instructions conflicted with multilingual document instructions; brevity/formatting rules conflicted with complete inventory and exact citations.
- English/French service-anniversary queries were missing from lexical routing/query expansion.
- Query text was logged verbatim. The replacement logs only status/counts and a worker source fingerprint.
- The voice fallback supplied evidence through `generate_reply(instructions=...)`. The installed Google plugin serializes that argument as a **model-role message**, not a system update. New strict live tests exposed internal-looking text and malformed citations. The corrected document path uses `Agent.update_instructions` before normal generation; ordinary turns restore the base instructions.
- The installed Python `dev` command explicitly reports that in-process auto-reload was removed. Editing a file does not update an already-running worker. No old agent worker was present during this audit; a freshly started worker registered successfully with LiveKit.

The existing startup script selects `.venv-windows313`. Worker startup now prints a SHA-256 prefix of `agent.py` and the document tool names, so a restart can be verified without exposing credentials.

## Changes

Modified existing implementation files:

- `src/agent.py`: complete inventory registration, deterministic local preflight for recognized text questions, immediate voice fallback with session-local external-tool blocking, cancellation on newer input/close, multilingual/source instructions, disabled thought output, startup fingerprint.
- `src/krn_docs.py`: metadata-driven `list_krn_docs`, multilingual recognition/query expansion, fail-closed index errors, safe logging, removal of cross-session timestamp, index cache refresh on replacement.
- `scripts/prepare_krn_docs.py`: discover actual PDFs and embed their preparation metadata in the index; support metadata defaults for newly added files.
- `scripts/run_krn_catalog.py`: explicitly label retrieval-only results and untested answer dimensions.
- `tests/test_krn_routing.py`: typed routing, session isolation, external-tool blocking, inventory and ordinary-chat regressions.
- `README.md`: link to this audit and test instructions.

Created:

- `tests/test_krn_inventory.py`: actual-file/index inventory equality, refresh, metadata, multilingual retrieval, factual retrieval from every PDF.
- `tests/test_krn_live.py`: opt-in real Gemini Live tests using production callback arguments and the SDK complete-turn runner; no microphone/RoomIO transport coverage.
- This audit report.

Regenerated local extraction/index/catalog artifacts under `data/`. Original PDFs were not modified. All nine SHA-256 hashes match the supplied transfer originals. The workspace already contained substantial uncommitted prior implementation changes; these were preserved.

## Inventory

Nine PDFs, 126 chunks, 30 PDF pages; OCR on 10 pages in three files. No unreadable pages were reported by the preparation script.

| Original filename | PDF pages | OCR used |
| --- | ---: | --- |
| BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf | 5 | Yes |
| BV_Regelung von Fahrzeugverspätungen.pdf | 4 | Yes |
| DA001-2026 Schülerbeförderung.pdf | 1 | No |
| DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf | 1 | No |
| DOC-20260920-WA0002.pdf | 1 | Yes |
| DOC-20260920-WA0003.pdf | 1 | No |
| DOC-20260920-WA0004.pdf | 1 | No |
| DOC-20260920-WA0005.pdf | 15 | No |
| DOC-20260920-WA0006.pdf | 1 | No |

The anniversary PDF page 3 was independently rendered and visually inspected: ten years gives 100 euros, with congratulations and a 25-euro gift. Its scope excludes marginal/short-term employees and working students. Retrieval tests do not constitute visual verification of every table or map relationship. The existing preparation pipeline includes curated OCR corrections and map summaries; maps are not a general routing engine.

## Validation and remaining boundary

Final validation results are recorded below after the last run.

The 68 catalog cases check retrieval, expected document/page and evidence terms. They do not evaluate generated answer language, final citation accuracy or absence of hallucinations. F06, N01 and N02 check explicit real-time-data refusal. N03/N04 only check bounded source retrieval, not a generated legal/procedural refusal. The new per-source test additionally covers the Wabenplan, which the original catalog did not independently prove searchable.

**Native microphone strictness remains a release boundary:** with Gemini's server-side audio turn detection, a final transcription event is not a guaranteed pre-generation hook. The corrected voice router interrupts as soon as an internal topic is recognized and retrieves immediately, but cannot prove that no audio or external tool call occurred before that transcript arrived. Arbitrary multilingual phrasing and contextual follow-ups can also escape a lexical classifier. Prompt instructions are not a formal evidence/citation validator. Do not describe these changes as a proven universal no-hallucination guarantee. A strict guarantee needs a pre-generation audio/transcription gate and output validation, with latency and microphone regression testing.

## Manual acceptance questions

Run `start-agent.ps1` again after source changes, confirm `KRN worker revision=...` and `registered worker`, then connect the existing browser app. Test each question by typing and by microphone. Check the complete visible response, audible response, language, exact filename/page and absence of external tools. Repeat the first three turns in two concurrent sessions to check isolation.

1. **German:** “Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?” Expected: 100 euros and 25-euro gift, scope respected; `[Quelle: BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf, Seite 3]`. No pension or severance claims.
2. **Inventory:** “Welche KRN-Richtlinien und internen Dokumente hast du in deiner Wissensdatenbank? Bitte liste alle verfügbaren Dokumente mit dem genauen Original-Dateinamen auf.” Expected: all nine filenames above, no invented source.
3. **English:** “What do I receive after 10 years of service?” Expected: English answer, same benefits and original filename; `[Source: BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf, page 3]`.
4. **French:** “Que reçois-je après 10 ans d'ancienneté ?” Expected: French answer, same benefits; `[Source : BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf, page 3]`.
5. **Unavailable:** “Wie hoch ist die KRN-Prämie für die geheime Mondbasis?” Expected: not found in the available documents, no amount or web fallback.

Additional factual questions, together with question 1 covering all nine PDFs:

| Question | Expected evidence | Original filename / PDF page |
| --- | --- | --- |
| Wie werden 20 Minuten Fahrzeugverspätung vergütet? | 20 minutes working time | BV_Regelung von Fahrzeugverspätungen.pdf / 3 |
| Was mache ich mit einem Schüler ohne gültiges Ticket auf dem Schulweg? | Transport, record name/school, written QM report | DA001-2026 Schülerbeförderung.pdf / 1 |
| Was mache ich bei einem defekten EC-Gerät? | Cash payment; promptly report defect to control centre; no invented enforcement measures | DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf / 1 |
| Was bedeutet das S im Fahrplan der Linie 216? | School days in Rheinland-Pfalz | DOC-20260920-WA0002.pdf / 1 |
| Seit wann gilt der RNN-Gesamtnetzplan 2025? | 15 December 2024 | DOC-20260920-WA0003.pdf / 1 |
| Welche ist die höchste Preisstufe der RNN-Preistafel? | 10, entire RNN network | DOC-20260920-WA0004.pdf / 1 |
| Kann ich mit dem Deutschland-Ticket einen weiteren Erwachsenen mitnehmen? | No; distinction from free children under six | DOC-20260920-WA0005.pdf / 7 |
| Welche Preisstufe gilt innerhalb Bingen laut Wabenplan? | 31 | DOC-20260920-WA0006.pdf / 1 |

Also verify ordinary weather, public web search, browser interaction, camera switching and authenticated connection in the actual clients. Automated API tests do not cover microphone permissions, acoustic transcription, Entra login or physical camera hardware.

## Reproduce

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv run pytest -q
uv run python scripts/run_krn_catalog.py
$env:KRN_LIVE_TESTS = '1'
uv run pytest tests/test_krn_live.py -q
uv run ruff check src scripts tests
```

The live tests use configured credentials and incur inference usage. Credentials and authentication configuration were not changed.

## Final validation (continued after Codex usage limit)

Continuation completed the unfinished instruction-update path and re-verified against installed `livekit-agents` / Google Realtime plugin sources in `.venv-windows313`:

- `Agent.update_instructions` → `AgentActivity.update_instructions` → `RealtimeSession.update_instructions`
- Google Live mid-session updates still send `LiveClientContent` with `role="model"` and `turn_complete=False` (APIs reject `role="system"`)
- `generate_reply(instructions=...)` also injects `role="model"` content but with `turn_complete=True` (higher leak risk for evidence payloads)
- Production KRN path: retrieve locally → `update_instructions(base + evidence)` → `generate_reply()` / `generate_reply(user_input=...)` **without** extra instructions → await SpeechHandle → append missing citation via `session.say` from retrieval metadata → restore `base_instructions`
- Explicit “im Internet”/web requests are not treated as internal document questions, so public web search for events mentioning KRN still works
- External tools are blocked only while `krn_internal_turn` is set (not by scanning tool-argument strings for “KRN”)

**Native microphone boundary (unchanged honesty):** final transcription is not a guaranteed pre-generation gate under Gemini server-side turn detection. Typed chat has deterministic pre-retrieval; voice interrupts as soon as an internal topic is recognized and retrieves immediately, but cannot prove zero audio/tool activity before the transcript arrives.

