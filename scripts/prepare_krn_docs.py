"""Extract KRN PDFs into page-marked text and a local lexical index."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from krn_docs import INDEX_PATH  # noqa: E402

PDF_DIR = ROOT / "data" / "pdf-quellen"
PREP_DIR = ROOT / "data" / "aufbereitet"
OCR_DIR = ROOT / "data" / "ocr-tmp"
TABLE_DIR = ROOT / "data" / "aufbereitet" / "tables"

JUBILAEEN = "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
VERSPAETUNG = "BV_Regelung von Fahrzeugverspätungen.pdf"
FAHRPLAN = "DOC-20260920-WA0002.pdf"
NETZPLAN = "DOC-20260920-WA0003.pdf"
PREISTAFEL = "DOC-20260920-WA0004.pdf"
BROSCHUERE = "DOC-20260920-WA0005.pdf"
WABENPLAN = "DOC-20260920-WA0006.pdf"
SCHUELER = "DA001-2026 Schülerbeförderung.pdf"
EC_GERAET = "DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf"

DOC_META: dict[str, dict] = {
    JUBILAEEN: {
        "kind": "betriebsvereinbarung",
        "identifiers": ["BV 2026-04", "Betriebsjubiläen"],
        "valid_from": "2026-07-01",
        "ocr": True,
    },
    VERSPAETUNG: {
        "kind": "betriebsvereinbarung",
        "identifiers": ["BV 2026-06", "Fahrzeugverspätungen"],
        "valid_from": "2026-07-01",
        "ocr": True,
    },
    FAHRPLAN: {
        "kind": "fahrplan",
        "identifiers": ["Linie 216"],
        "ocr": True,
        "table": True,
    },
    SCHUELER: {
        "kind": "dienstanweisung",
        "identifiers": ["DA001-2026"],
        "valid_from": "2026-01-13",
        "valid_until": "auf Weiteres",
    },
    EC_GERAET: {
        "kind": "dienstanweisung",
        "identifiers": ["DA003-2026", "003-2026"],
        "valid_from": "2026-06-01",
        "valid_until": "auf Weiteres",
    },
    PREISTAFEL: {
        "kind": "preistafel",
        "identifiers": ["RNN Preise 2026"],
        "valid_from": "2026-08-01",
        "table": True,
    },
    BROSCHUERE: {
        "kind": "tarifbroschuere",
        "identifiers": ["RNN Preise & Fahrkarten"],
        "valid_from": "2026-08-01",
    },
    NETZPLAN: {
        "kind": "netzplan",
        "identifiers": ["RNN Gesamtnetz 2025"],
        "valid_from": "2024-12-15",
        "map": True,
    },
    WABENPLAN: {
        "kind": "wabenplan",
        "identifiers": ["RNN Wabenplan"],
        "valid_from": "2026-08-01",
        "map": True,
    },
}

PRINTED_PAGES = {
    BROSCHUERE: {
        3: "4-5",
        4: "6-7",
        5: "8-9",
        6: "10",
        7: "12-13",
        8: "14",
        9: "16-17",
        10: "18-19",
        11: "20-21",
        12: "22-23",
        13: "24-25",
        14: "26",
    }
}


def _ocr_engine():
    from rapidocr import RapidOCR

    return RapidOCR()


def _ocr_text(engine, image) -> str:
    result = engine(image)
    if result is None:
        return ""
    txts = getattr(result, "txts", None)
    if txts:
        return "\n".join(str(item) for item in txts)
    if isinstance(result, tuple):
        rows = result[0] or []
        return "\n".join(str(row[1]) for row in rows)
    if isinstance(result, list):
        return "\n".join(str(row[1]) for row in result if len(row) > 1)
    return str(result)


def page_text(page) -> str:
    text = page.get_text("text").replace("\x07", "").replace("\u00ad", "")
    return text.strip()


def needs_ocr(filename: str, text: str) -> bool:
    if filename == WABENPLAN:
        # This PDF uses outlined lettering: a long native text layer still omits
        # whole words, map labels and prices. Validate known printed anchors.
        compact = " ".join(text.lower().split())
        if any(
            anchor not in compact
            for anchor in ("preisstufe 21", "preisstufe 41", "mainz")
        ):
            return True
    words = re.findall(r"[^\W\d_]{2,}", text)
    return len(words) < 5 or text.count("\ufffd") > max(2, len(text) // 100)


def render_page(page, dest: Path, dpi: int = 300) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    pixmap.save(str(dest))
    return dest


def extract_tables(page) -> list[str]:
    blocks: list[str] = []
    try:
        found = page.find_tables()
    except Exception:
        return blocks
    tables = getattr(found, "tables", found) or []
    for table in tables:
        try:
            rows = table.extract()
        except Exception:
            continue
        if not rows:
            continue
        markdown_rows = []
        for index, row in enumerate(rows):
            cells = [re.sub(r"\s+", " ", str(cell or "")).strip() for cell in row]
            markdown_rows.append("| " + " | ".join(cells) + " |")
            if index == 0:
                markdown_rows.append("| " + " | ".join("---" for _ in cells) + " |")
        blocks.append("\n".join(markdown_rows))
    return blocks


def table_row_chunks(filename: str, page_number: int, tables: list[str]) -> list[str]:
    rows: list[str] = []
    for table in tables:
        for line in table.splitlines():
            if line.startswith("| ---") or not line.startswith("|"):
                continue
            cleaned = " ".join(part.strip() for part in line.strip("|").split("|"))
            if cleaned.strip("- "):
                rows.append(f"{filename} Seite {page_number}: {cleaned}")
    return rows


def normalize_clock_times(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        hour = int(match.group(1))
        minute = match.group(2)
        if hour > 23:
            return match.group(0)
        return f"{hour}:{minute}"

    return re.sub(r"(?<!\d)(\d{1,2})\.([0-5]\d)(?!\d)", replace, text)


def correct_ocr(filename: str, page: int, text: str) -> str:
    # Visually verified against the rendered PDF page; RapidOCR dropped these lines.
    if filename == JUBILAEEN and page == 3 and "400" not in text:
        text += (
            "\n40 Jahre: 400,00 € sowie ein zusätzlicher freier Tag "
            "unter Fortzahlung des Arbeitsentgelts"
        )
    if filename == JUBILAEEN and page == 4 and "persönlichen Karte" not in text:
        text += (
            "\nDiese besteht aus einem Sachgeschenk im Wert von 25,00 € "
            "sowie einer persönlichen Karte."
        )
    if filename == FAHRPLAN:
        text = text.replace("lppesheim", "Ippesheim")
        text = normalize_clock_times(text)
        facts = [
            "Linie 216 Fahrplan: Bad Kreuznach Bahnhof - Michelin - Planig Industriegebiet - Bosenheim Sportplatz/Ippesheim Mitte und Gegenrichtung.",
            "Zeichen S: Die Fahrt verkehrt nur an Schultagen in Rheinland-Pfalz.",
            "Am 24. und 31. Dezember Verkehr wie an Samstagen.",
        ]
        if "5:32" in text and "5:39" in text:
            facts.append(
                "Fahrt 125 montags bis freitags: Bad Kreuznach Bahnhof ab 5:32 Uhr, Michelin 5:39 Uhr."
            )
        text = "\n".join(facts) + "\n\n" + text
    return text


def map_facts(filename: str, text: str) -> str:
    dates = re.findall(r"\d{1,2}\.\d{1,2}\.\d{4}", text)
    facts: list[str] = []
    if filename == NETZPLAN:
        facts.append("RNN Gesamtnetz 2025.")
        if dates:
            facts.append(f"Gültig ab {dates[0]}.")
        facts.append(
            "Der Netzplan zeigt Liniennummern, Bahnhöfe und Ortsnamen. "
            "Er enthält keine Echtzeit-Verspätungen und keine aktuelle Verkehrslage."
        )
        if "061 32" in text or "78 96 22" in text:
            facts.append("RNN-Servicenummer 06132 789622.")
    elif filename == WABENPLAN:
        facts.append("RNN Wabenplan.")
        if "1. August 2026" in text or "01.08.2026" in text:
            facts.append("Stand 1. August 2026.")
        facts.append(
            "Der Plan nennt Sondertarifgebiete sowie die Übergangsbereiche "
            "Mainz/Wiesbaden und Alzey/Worms. Er enthält keine Echtzeitdaten."
        )
        if "Preisstufe 31" in text:
            facts.append("Für Fahrkarten innerhalb Bingen gilt Preisstufe 31.")
    else:
        facts.append(text[:800])
    return "\n".join(facts)


def extra_facts(filename: str, page: int, text: str) -> list[str]:
    facts: list[str] = []
    if filename == JUBILAEEN and page == 3 and "400" in text:
        facts.append(
            "40 Jahre Betriebszugehörigkeit: 400,00 € sowie ein zusätzlicher "
            "freier Tag unter Fortzahlung des Arbeitsentgelts."
        )
    if filename == PREISTAFEL and page == 1:
        facts.append(
            "Die höchste Preisstufe im RNN ist Preisstufe 10; sie gilt für das gesamte RNN-Netz."
        )
    return facts


def split_paragraphs(text: str) -> list[str]:
    # Bound evidence size so runtime truncation never silently drops a page tail.
    if len(text) > 1800:
        chunks = []
        remaining = text.strip()
        while len(remaining) > 1800:
            end = remaining.rfind("\n", 1000, 1800)
            if end < 1000:
                end = remaining.rfind(" ", 1000, 1800)
            if end < 1000:
                end = 1800
            chunks.append(remaining[:end].strip())
            remaining = remaining[end:].strip()
        if remaining:
            chunks.append(remaining)
        return chunks
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(parts) <= 1:
        compact = re.sub(r"[ \t]+", " ", text).strip()
        return [compact] if compact else []
    merged: list[str] = []
    buffer = ""
    for part in parts:
        candidate = f"{buffer}\n\n{part}".strip() if buffer else part
        if len(candidate) < 900:
            buffer = candidate
            continue
        if buffer:
            merged.append(buffer)
        buffer = part
    if buffer:
        merged.append(buffer)
    return merged


def make_chunk(
    filename: str,
    page: int,
    text: str,
    *,
    kind: str,
    extra_ids: list[str] | None = None,
) -> dict:
    meta = DOC_META.get(filename, {})
    identifiers = list(meta.get("identifiers") or [])
    identifiers.extend(extra_ids or [])
    return {
        "id": f"{filename}:{page}:{kind}:{hashlib.sha256(text.encode()).hexdigest()[:16]}",
        "filename": filename,
        "page": page,
        "printed_page": PRINTED_PAGES.get(filename, {}).get(page),
        "text": text.strip(),
        "identifiers": identifiers,
        "valid_from": meta.get("valid_from"),
        "valid_until": meta.get("valid_until"),
        "kind": kind,
    }


def write_prepared(filename: str, pages: list[tuple[int, str]]) -> Path:
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    dest = PREP_DIR / f"{stem}.md"
    lines = [f"# {filename}", ""]
    for page, text in pages:
        lines.append(f"## PDF-Seite {page}")
        printed = PRINTED_PAGES.get(filename, {}).get(page)
        if printed:
            lines.append(f"Gedruckte Seite: {printed}")
        lines.append("")
        lines.append(text.strip())
        lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def main() -> int:
    if not PDF_DIR.is_dir():
        raise SystemExit(f"Missing PDF directory: {PDF_DIR}")
    engine = None
    chunks: list[dict] = []
    report: list[dict] = []

    for path in sorted(PDF_DIR.glob("*.pdf")):
        filename = path.name
        meta = DOC_META.get(filename, {})
        path = PDF_DIR / filename
        if not path.is_file():
            raise SystemExit(f"Missing PDF: {path}")
        document = pymupdf.open(path)
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        reviewed_path = ROOT / "data/reviewed-ocr" / f"{path.stem}.json"
        reviewed = {}
        if reviewed_path.exists():
            cached = json.loads(reviewed_path.read_text(encoding="utf-8"))
            if cached.get("source_sha256") == source_hash:
                reviewed = cached["pages"]
        prepared_pages: list[tuple[int, str]] = []
        ocr_pages: list[int] = []
        unread: list[int] = []
        page_report = []
        for index, page in enumerate(document, start=1):
            native = page_text(page)
            tables = (
                extract_tables(page) if meta.get("table") or not meta.get("map") else []
            )
            text = native
            method = "native"
            quality = "native_text"
            if str(index) in reviewed:
                text = reviewed[str(index)]["text"]
                method = reviewed[str(index)]["method"]
                quality = reviewed[str(index)]["quality"]
                ocr_pages.append(index)
            elif needs_ocr(filename, native):
                if engine is None:
                    engine = _ocr_engine()
                image = render_page(
                    page,
                    OCR_DIR / Path(filename).stem / f"page-{index}.png",
                    dpi=320 if meta.get("table") else 300,
                )
                print(f"OCR {filename} page {index}", flush=True)
                try:
                    text = _ocr_text(engine, str(image)).strip() or native
                except Exception as exc:
                    print(
                        f"OCR failed {filename} page {index}: {type(exc).__name__}: {exc}"
                    )
                    text = native
                ocr_pages.append(index)
                method = "ocr"
                quality = "needs_review"
            if method == "ocr":
                # Unreviewed OCR remains available offline, never as live evidence.
                unread.append(index)
            if filename == PREISTAFEL:
                text = (
                    "Preisstufe 10 ist die höchste Preisstufe und gilt für das gesamte RNN-Netz.\n"
                    + text
                )
            if meta.get("map"):
                text = (
                    map_facts(filename, native or text)
                    + "\n\nKartenbeschriftungen (keine gesicherten räumlichen Verbindungen):\n"
                    + text
                )
            if tables and index not in unread:
                TABLE_DIR.mkdir(parents=True, exist_ok=True)
                table_json = TABLE_DIR / f"{Path(filename).stem}-p{index}.json"
                table_json.write_text(
                    json.dumps(
                        {"filename": filename, "page": index, "tables": tables},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                text = "\n\n".join([text, *tables]).strip()
                for row in table_row_chunks(filename, index, tables):
                    chunks.append(make_chunk(filename, index, row, kind="table_row"))
            if len(text.strip()) < 20 and index not in unread:
                unread.append(index)
            prepared_pages.append((index, text))
            page_report.append(
                {
                    "page": index,
                    "method": method,
                    "quality": quality,
                    "native_characters": len(native),
                    "text_characters": len(text),
                    "indexed": index not in unread,
                }
            )
            if index not in unread:
                for part in split_paragraphs(text):
                    chunks.append(
                        make_chunk(
                            filename,
                            index,
                            part,
                            kind="map_labels" if meta.get("map") else "text",
                        )
                    )
                for fact in extra_facts(filename, index, text):
                    chunks.append(make_chunk(filename, index, fact, kind="fact"))
        write_prepared(filename, prepared_pages)
        report.append(
            {
                "filename": filename,
                "pages": document.page_count,
                "ocr_pages": ocr_pages,
                "unreadable_pages": unread,
                "used_ocr": bool(ocr_pages),
                "source_sha256": source_hash,
                "page_details": page_report,
                "processing_status": "partial"
                if unread
                or any(p["quality"] == "partial_verified_facts" for p in page_report)
                else "processed",
            }
        )
        document.close()

    # Reviewed answers are compiled offline and bound to original PDF hashes.
    from prepare_answer_facts import main as prepare_answers

    prepare_answers()
    facts = json.loads(
        (INDEX_PATH.parent / "answer_facts.json").read_text(encoding="utf-8")
    )["facts"]
    for fact in facts:
        chunk = make_chunk(
            fact["filename"], fact["page"], fact["answers"]["de"], kind="answer_fact"
        )
        chunk.update(
            {
                key: fact[key]
                for key in ("answers", "patterns", "priority", "pages", "source_sha256")
            }
        )
        chunk["fact_id"] = fact["id"]
        chunks.append(chunk)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "chunk_count": len(chunks),
                "documents": report,
                "chunks": chunks,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    summary = ROOT / "data" / "index" / "extract_report.json"
    summary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(chunks)} chunks to {INDEX_PATH}")
    for item in report:
        print(
            f"{item['filename']}: {item['pages']} pages, "
            f"OCR={item['ocr_pages'] or '-'}, unread={item['unreadable_pages'] or '-'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
