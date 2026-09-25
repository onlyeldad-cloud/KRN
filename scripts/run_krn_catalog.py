"""Run all 68 catalog questions against the local KRN index."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
TESTS_DIR = ROOT / "tests"
for path in (SRC_DIR, TESTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from krn_catalog_cases import CATALOG_CASES  # noqa: E402

from krn_docs import fold_text, search_krn_index  # noqa: E402


def evaluate(case: dict) -> dict:
    packed = search_krn_index(case["query"], limit=8)
    hits = packed.get("results") or []
    joined = fold_text(" ".join(hit.get("text", "") for hit in hits))
    files = {hit["filename"] for hit in hits}
    file_ok = (not case["filenames"]) or bool(files & set(case["filenames"]))
    page_ok = True
    if case["pages"] and case["filenames"]:
        page_ok = any(
            hit["filename"] in case["filenames"] and hit["page"] in case["pages"]
            for hit in hits
        )
    missing = [needle for needle in case["must_contain"] if needle not in joined]
    if case["refusal"] and case["id"] in {"F06", "N01", "N02", "N03"}:
        ok = packed.get("status") == "no_evidence" and not hits
        return {
            "id": case["id"],
            "status": packed.get("status"),
            "ok": ok,
            "file_ok": True,
            "page_ok": True,
            "missing": [],
            "hits": [],
        }
    ok = bool(hits) and file_ok and page_ok and not missing
    return {
        "id": case["id"],
        "status": packed.get("status"),
        "ok": ok,
        "file_ok": file_ok,
        "page_ok": page_ok,
        "missing": missing,
        "hits": [
            {"filename": hit["filename"], "page": hit["page"], "score": hit["score"]}
            for hit in hits[:3]
        ],
    }


def main() -> int:
    rows = [evaluate(case) for case in CATALOG_CASES]
    passed = sum(1 for row in rows if row["ok"])
    payload = {
        "scope": "retrieval_only_not_live_answers",
        "not_evaluated": [
            "answer_language",
            "final_citation",
            "factual_answer",
            "hallucination_absence",
        ],
        "generated_at": datetime.now(UTC).isoformat(),
        "total": len(rows),
        "passed": passed,
        "failed": [row["id"] for row in rows if not row["ok"]],
        "results": rows,
    }
    dest = ROOT / "data" / "index" / "catalog_retrieval.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{passed}/{len(rows)} catalog retrieval cases passed")
    if payload["failed"]:
        print("Failed:", ", ".join(payload["failed"]))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
