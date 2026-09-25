"""Offline OCR audit for outlined Wabenplan labels absent from native extraction.

Writes confidence and coordinates for review. It never publishes unreviewed OCR.
"""

import hashlib
import json
from pathlib import Path

import pymupdf
from rapidocr import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
NAME = "DOC-20260920-WA0006.pdf"


def main():
    path = ROOT / "data/pdf-quellen" / NAME
    out = ROOT / "data/ocr-tmp/map-audit"
    out.mkdir(parents=True, exist_ok=True)
    engine = RapidOCR(
        params={
            "EngineConfig.onnxruntime.intra_op_num_threads": 2,
            "EngineConfig.onnxruntime.inter_op_num_threads": 2,
        }
    )
    rows = []
    with pymupdf.open(path) as doc:
        page = doc[0]
        for col in range(3):
            for row in range(2):
                clip = pymupdf.Rect(
                    max(0, col * page.rect.width / 3 - 15),
                    max(0, row * page.rect.height / 2 - 15),
                    min(page.rect.width, (col + 1) * page.rect.width / 3 + 15),
                    min(page.rect.height, (row + 1) * page.rect.height / 2 + 15),
                )
                target = out / f"tile-{col}-{row}.png"
                page.get_pixmap(dpi=240, clip=clip).save(str(target))
                result = engine(str(target))
                for text, score, box in zip(
                    result.txts or [],
                    result.scores or [],
                    result.boxes if result.boxes is not None else [],
                    strict=True,
                ):
                    rows.append(
                        {
                            "text": text,
                            "confidence": float(score),
                            "tile": [col, row],
                            "box": box.tolist(),
                            "quality": "candidate" if score >= 0.95 else "needs_review",
                        }
                    )
                print(f"Tile {col},{row}: {len(result.txts or [])} labels", flush=True)
    payload = {
        "filename": NAME,
        "page": 1,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "needs_visual_review",
        "reason": "Native extraction loses outlined map labels and parts of legend; OCR candidates are not live answer evidence.",
        "rows": rows,
    }
    (out / "ocr-quality.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
