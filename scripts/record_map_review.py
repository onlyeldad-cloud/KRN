"""Record visual review of the six original Wabenplan tiles and low-score labels."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = {
    70: "Wittlich",
    75: "Bruschied",
    85: "Asbach-Harfenmühle",
    89: None,
    96: "463",
    100: "Hahnenbach",
    133: "Kirnsulzbach",
    156: "Algenrodt",
    162: "471",
    199: "Hohl",
    255: "Freisen / Kusel",
    257: None,
    355: "Biebelsheim",
    400: None,
    406: "KREUZNACH",
    414: "412",
    415: "Allenfeld",
    423: "Entenpfuhl",
    429: "Roxheim",
    437: None,
    444: "Heinzenberg",
    456: "Pferdsfeld",
    459: "412",
    462: "Allenfeld",
    504: "414",
    530: "Staudernheim",
    551: "415",
    576: "Hochstätten",
    666: "Ost",
    694: "Ober-I.",
    703: "Groß-Winternheim",
    714: None,
    729: "Ober-Hilbersheim",
    738: "Klein-Winternheim",
    804: "Undenheim",
    819: "352 Gumbsheim",
    844: "372",
    857: "343",
    875: "Nack",
    877: "Az-Süd",
    899: "Mettenheim",
    932: "380",
    945: "377",
    972: None,
}


def main():
    raw = ROOT / "data/ocr-tmp/map-audit/ocr-quality.json"
    payload = json.loads(raw.read_text(encoding="utf-8"))
    assert (
        payload["source_sha256"]
        == "bea4b8bd563e939cea56a977201cacde0b4b619f002796efd3483b2e1e9bf742"
    )
    assert len(payload["rows"]) == 977
    texts = []
    for index, row in enumerate(payload["rows"]):
        if row["confidence"] < 0.95 and index not in CORRECTIONS:
            raise ValueError(f"Unreviewed low confidence label {index}")
        corrected = CORRECTIONS.get(index, row["text"])
        row["reviewed_text"] = corrected
        row["quality"] = (
            "visually_corrected" if index in CORRECTIONS else "confidence_checked"
        )
        if corrected:
            texts.append(corrected)
    payload["status"] = "reviewed"
    payload["review"] = (
        "Six original tiles inspected; all 44 labels below 0.95 reviewed, corrected or excluded as symbols/logos/crop fragments. Map topology is not inferred from OCR order."
    )
    text = "RNN Wabenplan. Stand 1. August 2026.\n\n" + "\n".join(dict.fromkeys(texts))
    # Native layer supplies complementary labels; geometry remains in the PDF.
    sidecar = {
        "filename": payload["filename"],
        "source_sha256": payload["source_sha256"],
        "reviewed_at": "2026-09-25",
        "review": payload["review"],
        "pages": {
            "1": {
                "text": text,
                "quality": "ocr_confidence_checked_and_reviewed",
                "method": "native+ocr_reviewed",
                "low_confidence_reviewed": len(CORRECTIONS),
            }
        },
    }
    dest = ROOT / "data/reviewed-ocr" / payload["filename"].replace(".pdf", ".json")
    dest.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")
    raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
