# Validation, 2026-09-25

All nine original PDFs match the transfer ZIP by SHA256. All 30 pages are represented in 239 indexed chunks, including reviewed timetable transcription and hybrid native/OCR fare-zone labels. Original PDFs are unchanged. See [per-document audit](DOCUMENT_COVERAGE_AUDIT.md) and `data/index/document_coverage.json`.

- Local regression suite: 247 passed, 15 live tests explicitly deselected. One dependency deprecation warning. Changed Python files pass Ruff.
- Catalog: 68 retrieval checks pass; 69 final-answer cases pass. All 30 page probes pass. These are bounded checks, not proof for every possible question.
- Cached retrieval benchmark: mean 9.788 ms, median 9.475 ms, p95 17.062 ms over 345 searches. This is local retrieval, not voice latency.
- Frontend: production build succeeded; lint has no errors and four warnings.

## User voice test and corrective changes

The second user transcript demonstrated five invented filenames (including RNN_Preistabelle_2024_01.pdf), unsupported extra policy claims, duplicate/concatenated answers, and failure to match "10 Jahr bei KRN". None of those five additional filenames exists in the local source directory; they are not additional indexed documents.

The production audio router now only classifies turns and guards external tools. It no longer interrupts Gemini and starts another generation on final realtime transcripts, which may arrive after the model has started responding. Gemini owns one audio response path and receives the reviewed answer from the document tool, together with the complete filename allowlist. Inventory tools also return the complete ready-to-speak inventory. These constraints reduce opportunities for invented additions but are not a deterministic guarantee of model audio fidelity. Typed messages still use direct retrieval and explicit speech delivery.

Numeric singular "Jahr" is normalized to "Jahre", fixing the actual anniversary question. An incomplete single-ticket question mentioning Preisstufe without its number requests clarification rather than claiming prices are absent. Regression tests cover these exact inputs, no competing local generation in native audio mode, and unavailable-index handling. The garbled network-plan question should be repeated clearly; no 2024 tariff document was added to justify the model's invented answer.

The changes below describe the earlier speech and performance correction, retained for explicit text delivery and greeting.

The supplied live transcript/logs show delayed replies, escaped filename underscores, and a citation interrupted across output segments. Local retrieval success did not demonstrate audio delivery: the voice path suppressed the RuntimeError raised when Gemini Live receives session.say without a TTS backend.

The corrected speech helper uses generate_reply for that specific unsupported-speech error and propagates other failures. It passes the reviewed answer and citation for spoken delivery and requests no tools. Model-generated wording is not guaranteed verbatim. Live citation fidelity and duplicate-response behavior therefore remain unverified.

Caption synchronization is disabled to bypass the speaking-rate FFT path sampled in multi-second event-loop stalls. Captions now publish immediately. Logging, transport and other sampled stalls may still need profiling. The actual spoken school-ticket variant now routes locally; the inventory transcript already passes current routing.

Restart the worker and open a fresh call to verify the changes. Retest inventory, English delay, spoken school-ticket question, and English broken-card-reader question. Confirm one timely audible answer and a complete filename/page citation. No new live API test was run by Codex; the previous broad live-test escalation was rejected by automatic approval review because of possible external transmission of workspace content.

Automated document and routing tests pass, but live voice stability still requires manual verification.

## Reproduction

Use uv with UV_PROJECT_ENVIRONMENT=.venv-windows313 and UV_CACHE_DIR=.uv-cache:

1. `uv run --no-sync --offline python scripts/prepare_krn_docs.py`
2. `uv run --no-sync --offline python scripts/audit_krn_coverage.py`
3. `uv run --no-sync --offline pytest -m "not live" -q -p no:cacheprovider`

Reviewed OCR sidecars are source-hash-bound. Unreviewed OCR is excluded from live evidence. Map text order does not establish geographic relationships. `scripts/record_reviewed_ocr.py` is a one-time correction script, not a routine rebuild command.
