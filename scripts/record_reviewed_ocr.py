"""Record the 2026-09-25 visual review; does not modify original PDFs.

Corrections were read from rendered original pages, including dates and amounts.
The resulting cache is valid only for the exact source SHA256.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
J = "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
V = "BV_Regelung von Fahrzeugverspätungen.pdf"
REPLACEMENTS = {
    J: {
        2: [
            (
                r"Min[^\n]+",
                "Mitarbeitern in besonderen Lebenssituationen einen wichtigen Beitrag zu einer",
            ),
            (
                r"en  n en[^\n]+",
                "einheitliche und transparente Regelungen zu Betriebsjubiläen, Ehrungen sowie zur",
            ),
            (r"(§8 Inkrafttreten und Schlussbestimmung\.\.)", r"\1\n4"),
        ],
        3: [
            (
                r"Die bn[^\n]+",
                "Die folgenden rechtlichen Rahmenbedingungen liegen dieser Betriebsvereinbarung zu",
            ),
            (r"von25", "von 25"),
            (
                r"4ot[^\n]+\nArbeitsentgelts",
                "40 Jahre: 400,00 € sowie ein zusätzlicher freier Tag unter Fortzahlung des Arbeitsentgelts",
            ),
            (
                r"Zn n[^\n]+",
                "Zu folgenden runden Geburtstagen erhalten Mitarbeitende eine Gratulation sowie ein",
            ),
            (r"\n40 Jahre:.*\Z", ""),
        ],
        4: [
            (
                r"Died[^\n]+\nKarte\.",
                "Diese besteht aus einem Sachgeschenk im Wert von 25,00 € sowie einer persönlichen Karte.",
            ),
            (
                r"Din d[^\n]+",
                "Die Ehrung sowie die Übergabe der vorgesehenen Leistungen erfolgen in einem",
            ),
            (
                r"Die  e e[^\n]+",
                "Diese Betriebsvereinbarung tritt nach Beschluss der Geschäftsführung und des",
            ),
            (
                r"Kae[^\n]+",
                "Kalenderjahres, frühestens jedoch zum 31.12.2028, gekündigt werden. Die Kündigung",
            ),
            (r"\nDiese besteht.*\Z", ""),
        ],
        5: [
            (
                r"koz[^\n]+",
                "Kommt es bezüglich den in dieser Vereinbarung beschriebenen Regelungen zu",
            ),
            (
                r"un nz[^\n]+",
                "unwirksamen Bestimmung möglichst nahekommende Regelung zu treffen.",
            ),
        ],
    },
    V: {
        2: [
            (
                r"r unr[^\n]+",
                "Arbeitgeber und Betriebsrat vereinbaren mit dieser Betriebsvereinbarung eine",
            )
        ],
        3: [
            (
                r"Die be[^\n]+",
                "Die folgenden rechtlichen Rahmenbedingungen liegen dieser Betriebsvereinbarung zu",
            )
        ],
        4: [
            (
                r"Betn[^\n]+",
                "Betriebsparteien verständigen. Beide Seiten können jeweils einen Sachverständigen",
            ),
            (
                r"un\s+Bg[^\n]+",
                "unwirksamen Bestimmung möglichst nahekommende Regelung zu treffen.",
            ),
            (r"\n7\.L\nwe\n", "\n"),
        ],
    },
}


def main():
    destination = ROOT / "data/reviewed-ocr"
    destination.mkdir(exist_ok=True)
    for name, fixes in REPLACEMENTS.items():
        source = ROOT / "data/pdf-quellen" / name
        raw = (ROOT / "data/aufbereitet" / f"{source.stem}.md").read_text(
            encoding="utf-8"
        )
        pages = {}
        for number, text in re.findall(
            r"## PDF-Seite (\d+)\n(.*?)(?=\n## PDF-Seite |\Z)", raw, re.S
        ):
            text = text.strip().replace("loannis", "Ioannis")
            for pattern, replacement in fixes.get(int(number), []):
                text, count = re.subn(pattern, replacement, text)
                if count != 1:
                    raise ValueError((name, number, pattern, count))
            pages[number] = {
                "text": text,
                "quality": "visually_verified",
                "method": "ocr_reviewed",
            }
        (destination / f"{source.stem}.json").write_text(
            json.dumps(
                {
                    "filename": name,
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "reviewed_at": "2026-09-25",
                    "review": "Compared all printed text to rendered original PDF pages; signatures excluded.",
                    "pages": pages,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
