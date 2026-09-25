"""Reproducible source/hash/page/retrieval audit and warm local benchmark."""

import hashlib
import json
import re
import statistics
import sys
import time
import zipfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from krn_catalog_cases import CATALOG_CASES  # noqa: E402

from krn_docs import (  # noqa: E402
    detect_question_language,
    fold_text,
    format_citation,
    search_krn_index,
    short_krn_voice_answer,
)


def main():
    payload = json.loads(
        (ROOT / "data/index/krn_docs.json").read_text(encoding="utf-8")
    )
    archive = Path.home() / "Downloads/KRN-JARVIS_TRANSFER.zip"
    originals = {}
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.infolist():
            if entry.filename.lower().endswith(".pdf"):
                originals[Path(entry.filename).name] = hashlib.sha256(
                    zipped.read(entry)
                ).hexdigest()
    docs = {d["filename"]: d for d in payload["documents"]}
    files = {p.name: p for p in (ROOT / "data/pdf-quellen").glob("*.pdf")}
    cases = [
        *CATALOG_CASES,
        {
            "id": "W01",
            "query": "Welche Preisstufe gilt innerhalb Bingen laut Wabenplan?",
            "filenames": ["DOC-20260920-WA0006.pdf"],
            "pages": [1],
            "must_contain": ["preisstufe 31"],
            "refusal": False,
        },
    ]
    results = []
    for case in cases:
        packed = search_krn_index(case["query"], limit=8)
        evidence = [
            h
            for h in packed["results"]
            if h["filename"] in case["filenames"] and h["page"] in case["pages"]
        ]
        text = fold_text(" ".join(h["text"] for h in evidence))
        passed = bool(evidence) and all(t in text for t in case["must_contain"])
        answer = short_krn_voice_answer(case["query"], packed)
        expected_answer = {
            "M03": ["minute", "working time"],
            "M04": ["no additional people"],
        }.get(case["id"], case["must_contain"])
        refusal_only = case["id"] in {"F06", "N01", "N02", "N03"}
        if refusal_only:
            passed = packed["status"] == "no_evidence" and not packed["results"]
        answer_pass = (
            ("nicht" in answer and not packed["results"])
            if refusal_only
            else bool(expected_answer)
            and all(t in fold_text(answer) for t in expected_answer)
        )
        cited = [
            h
            for h in evidence
            if format_citation(
                h["filename"], h["page"], detect_question_language(case["query"])
            )
            in answer
        ]
        results.append(
            {
                **case,
                "retrieval_pass": passed,
                "answer": answer,
                "answer_fact_check": answer_pass,
                "citation_metadata_pass": bool(cited) or refusal_only,
                "cited_filenames": sorted({h["filename"] for h in cited}),
            }
        )
    rows = []
    for name in sorted(set(originals) | set(files) | set(docs)):
        path = files.get(name)
        chunks = [c for c in payload["chunks"] if c["filename"] == name]
        document = docs.get(name, {})
        source_error = None
        try:
            if path is None:
                raise FileNotFoundError(name)
            with pymupdf.open(path) as pdf:
                page_count = len(pdf)
        except (OSError, RuntimeError) as exc:
            page_count = document.get("pages", 0)
            source_error = type(exc).__name__
        checks = [
            r
            for r in results
            if name in r["filenames"]
            and not r["refusal"]
            and (len(r["filenames"]) == 1 or name in r["cited_filenames"])
        ]
        pages = []
        for page in range(1, page_count + 1):
            details = next(
                (p for p in document.get("page_details", []) if p["page"] == page), {}
            )
            pages.append(
                {
                    **details,
                    "page": page,
                    "chunks": sum(c["page"] == page for c in chunks),
                }
            )
            searchable = False
            probe = ""
            for chunk in [
                c for c in chunks if c["page"] == page and c["kind"] != "answer_fact"
            ]:
                words = re.findall(r"\w+", chunk["text"], re.UNICODE)
                probe = " ".join(words[:18])
                hits = search_krn_index(probe, limit=8)["results"]
                if any(h["filename"] == name and h["page"] == page for h in hits):
                    searchable = True
                    break
            pages[-1]["search_probe"] = probe
            pages[-1]["searchable"] = searchable
        partial = any(
            p.get("quality") in {"needs_review", "partial_verified_facts"}
            or not p["chunks"]
            for p in pages
        )
        row = {
            "filename": name,
            "source_error": source_error,
            "pages": page_count,
            "original_matches": bool(path)
            and hashlib.sha256(path.read_bytes()).hexdigest() == originals.get(name),
            "processed": bool(document),
            "chunks": len(chunks),
            "page_details": pages,
            "extraction": "native + OCR reviewed"
            if any(p.get("method") == "native+ocr_reviewed" for p in pages)
            else "OCR reviewed"
            if document.get("used_ocr")
            else "native",
            "retrieval_pass": any(c["retrieval_pass"] for c in checks),
            "citation_pass": any(c["citation_metadata_pass"] for c in checks),
            "answer_pass": bool(checks) and all(c["answer_fact_check"] for c in checks),
            "all_pages_searchable": all(p["searchable"] for p in pages),
            "factual_tests_passed": sum(c["retrieval_pass"] for c in checks),
            "factual_tests_total": len(checks),
            "answer_tests_passed": sum(c["answer_fact_check"] for c in checks),
            "in_overview": name
            in (ROOT / "docs/DOKUMENTEN_UEBERSICHT.md").read_text(encoding="utf-8"),
            "status": "PARTIAL" if partial else "PASS",
        }
        if not all(
            [
                row["original_matches"],
                row["processed"],
                row["chunks"],
                row["retrieval_pass"],
                row["citation_pass"],
                row["answer_pass"],
                row["all_pages_searchable"],
            ]
        ):
            row["status"] = "FAIL"
        rows.append(row)
    timings = []
    for _ in range(5):
        for case in cases:
            start = time.perf_counter()
            search_krn_index(case["query"])
            timings.append((time.perf_counter() - start) * 1000)
    report = {
        "scope": "All PDFs in original transfer ZIP and project source directory; exact SHA256 comparison",
        "documents": rows,
        "tests": results,
        "performance_ms": {
            "mean": statistics.mean(timings),
            "p50": statistics.median(timings),
            "p95": sorted(timings)[int(len(timings) * 0.95)],
            "searches": len(timings),
        },
        "limitations": [
            "Timetable: all 25 numbered trips normalized; unnumbered repeat service is retained as a 60-minute interval note, without invented trip IDs.",
            "Map labels searchable; geometric connections cannot be inferred from label order.",
            "Final answers checked locally for required facts and actual filename/page citations. This is not live Gemini or microphone evaluation.",
            "Live voice stability requires manual verification.",
        ],
    }
    dest = ROOT / "data/index/document_coverage.json"
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# KRN document coverage audit",
        "",
        report["scope"],
        "",
        "PASS means source hash, extraction, every-page search, document factual retrieval, required answer facts and actual final-text citations passed. Live audio playback remains unverified.",
        "",
        "| Document | Pages | Extraction | Chunks | Retrieval | Final-text citation | Status |",
        "|---|---:|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['filename']} | {row['pages']} | {row['extraction']} | {row['chunks']} | {'PASS' if row['retrieval_pass'] else 'FAIL'} ({row['factual_tests_passed']}/{row['factual_tests_total']}) | {'PASS' if row['citation_pass'] else 'FAIL'} | {row['status']} |"
        )
    lines += [
        "",
        "## Final-answer diagnostics",
        "",
        "Lexical expected-fact checks on the current spoken answer builder (not live Gemini):",
        "",
        *[
            f"- {r['filename']}: {r['answer_tests_passed']}/{r['factual_tests_total']} factual checks pass."
            for r in rows
        ],
        "",
        "Performance: " + json.dumps(report["performance_ms"]),
        "",
        *report["limitations"],
        "",
        "See data/index/document_coverage.json for every page, query, answer diagnostic and source comparison.",
    ]
    (ROOT / "docs/DOCUMENT_COVERAGE_AUDIT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "documents": [
                    {k: v for k, v in r.items() if k != "page_details"} for r in rows
                ],
                "performance": report["performance_ms"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
