# KRN document coverage audit

All PDFs in original transfer ZIP and project source directory; exact SHA256 comparison

PASS means source hash, extraction, every-page search, document factual retrieval, required answer facts and actual final-text citations passed. Live audio playback remains unverified.

| Document | Pages | Extraction | Chunks | Retrieval | Final-text citation | Status |
|---|---:|---|---:|---|---|---|
| BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf | 5 | OCR reviewed | 17 | PASS (12/12) | PASS | PASS |
| BV_Regelung von Fahrzeugverspätungen.pdf | 4 | OCR reviewed | 5 | PASS (8/8) | PASS | PASS |
| DA001-2026 Schülerbeförderung.pdf | 1 | native | 6 | PASS (9/9) | PASS | PASS |
| DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf | 1 | native | 7 | PASS (9/9) | PASS | PASS |
| DOC-20260920-WA0002.pdf | 1 | OCR reviewed | 34 | PASS (4/4) | PASS | PASS |
| DOC-20260920-WA0003.pdf | 1 | native | 25 | PASS (1/1) | PASS | PASS |
| DOC-20260920-WA0004.pdf | 1 | native | 84 | PASS (4/4) | PASS | PASS |
| DOC-20260920-WA0005.pdf | 15 | native | 55 | PASS (16/16) | PASS | PASS |
| DOC-20260920-WA0006.pdf | 1 | OCR reviewed | 6 | PASS (1/1) | PASS | PASS |

## Final-answer diagnostics

Lexical expected-fact checks on the current spoken answer builder (not live Gemini):

- BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf: 12/12 factual checks pass.
- BV_Regelung von Fahrzeugverspätungen.pdf: 8/8 factual checks pass.
- DA001-2026 Schülerbeförderung.pdf: 9/9 factual checks pass.
- DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf: 9/9 factual checks pass.
- DOC-20260920-WA0002.pdf: 4/4 factual checks pass.
- DOC-20260920-WA0003.pdf: 1/1 factual checks pass.
- DOC-20260920-WA0004.pdf: 4/4 factual checks pass.
- DOC-20260920-WA0005.pdf: 16/16 factual checks pass.
- DOC-20260920-WA0006.pdf: 1/1 factual checks pass.

Performance: {"mean": 9.788068116134694, "p50": 9.475099999690428, "p95": 17.06199999898672, "searches": 345}

Timetable: all 25 numbered trips normalized; unnumbered repeat service is retained as a 60-minute interval note, without invented trip IDs.
Map labels searchable; geometric connections cannot be inferred from label order.
Final answers checked locally for required facts and actual filename/page citations. This is not live Gemini or microphone evaluation.
Live voice stability requires manual verification.

See data/index/document_coverage.json for every page, query, answer diagnostic and source comparison.