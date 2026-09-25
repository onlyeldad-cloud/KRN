"""One-time transcription of all printed timetable cells, visually checked 2026-09-25.

The generated sidecar is hash-bound; normal preparation reads it, not this script.
An empty cell stays empty. The repeat column is preserved as a note, not invented IDs.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "DOC-20260920-WA0002.pdf"
OUT_IDS = [125, 101, 103, 105, 111, 113, 127, 115, 117, 119, 121, 123]
IN_IDS = [102, 104, 106, 108, 114, 116, 126, 118, 120, 130, 122, 124, 128]
OUT = [
    (
        "Bad Kreuznach, Bahnhof",
        "5:32 6:42 8:12 9:12 12:12 13:12 13:32 14:12 15:12 16:12 17:12 18:12",
    ),
    (
        "Bad Kreuznach, Gensinger Straße",
        "5:33 6:43 8:13 9:13 12:13 13:13 13:33 14:13 15:13 16:13 17:13 18:13",
    ),
    (
        "Bad Kreuznach, Heidenmauer",
        "5:34 6:44 8:14 9:14 12:14 13:14 13:34 14:14 15:14 16:14 17:14 18:14",
    ),
    (
        "Bad Kreuznach, Seitz-Werke",
        "5:35 6:45 8:15 9:15 12:15 13:15 13:35 14:15 15:15 16:15 17:15 18:15",
    ),
    (
        "Bad Kreuznach, Sandweg",
        "5:36 6:46 8:16 9:16 12:16 13:16 13:36 14:16 15:16 16:16 17:16 18:16",
    ),
    (
        "Bad Kreuznach, Otto-Meffert-Str./oddAG",
        "5:37 6:47 8:17 9:17 12:17 13:17 13:37 14:17 15:17 16:17 17:17 18:17",
    ),
    (
        "Bad Kreuznach, Michelin",
        "5:39 6:49 8:19 9:19 12:19 13:19 13:39 14:19 15:19 16:19 17:19 18:19",
    ),
    (
        "Bad Kreuznach, Mercedes",
        "- 6:52 8:22 9:22 12:22 13:22 - 14:22 15:22 16:22 17:22 18:22",
    ),
    (
        "Planig, Industriegebiet",
        "- 6:53 8:23 9:23 12:23 13:23 - 14:23 15:23 16:23 17:23 18:23",
    ),
    ("Planig, Mitte", "- 6:54 - - - 13:24 - - - 16:24 - -"),
    ("Planig, Römerdorf", "- - - - - 13:25 - - - 16:25 - -"),
    ("Planig, Bahnhof", "- - - - - 13:27 - - - 16:27 - -"),
    ("Planig, Grundschule", "- 6:55 - - - - - - - - - -"),
    ("Planig, Bosenbergstraße", "- - 8:24 9:24 12:24 - - 14:24 15:24 - 17:24 18:24"),
    ("Bosenheim, A. d. Pforte", "- - 8:26 9:26 12:26 - - 14:26 15:26 - 17:26 18:26"),
    ("Bosenheim, Rheingaustraße", "- - 8:27 9:27 12:27 - - 14:27 15:27 - 17:27 18:27"),
    ("Bosenheim, Sportplatz", "- - 8:30 9:30 12:30 - - 14:30 15:30 - 17:30 18:30"),
    ("Ippesheim, Junkerstraße", "- - - - - 13:30 - - - 16:30 - -"),
]
IN = [
    ("Bosenheim, Sportplatz", "- - 8:30 9:30 12:30 - - 14:30 15:30 - - 17:30 -"),
    ("Bosenheim, Parkstraße", "- - 8:31 9:31 12:31 - - 14:31 15:31 - - 17:31 -"),
    ("Bosenheim, Mitte", "- - 8:32 9:32 12:32 - - 14:32 15:32 - - 17:32 -"),
    ("Bosenheim, An der Pforte", "- - 8:33 9:33 12:33 - - 14:33 15:33 - - 17:33 -"),
    ("Planig, Bosenbergstraße", "- - 8:34 9:34 12:34 - - 14:34 15:34 - - 17:34 -"),
    ("Ippesheim, Ernst-Ludwig-Straße", "- 7:21 - - - 13:30 - - - - - - -"),
    ("Ippesheim, Junkerstraße", "- - - - - - - - - - 16:30 - -"),
    ("Planig, Bahnhof", "- 7:23 - - - 13:32 - - - - 16:32 - -"),
    ("Planig, Grundschule", "7:02 - - - - - - - - - - - -"),
    ("Planig, Römerdorf", "- 7:25 - - - 13:34 - - - - 16:34 - -"),
    ("Planig, Kirche", "7:03 7:26 - - - 13:35 - - - - 16:35 - -"),
    ("Planig, Mitte", "7:04 7:27 - - - 13:36 - - - - 16:36 - -"),
    (
        "Planig, Industriegebiet",
        "7:05 7:28 8:35 9:35 12:35 13:37 - 14:35 15:35 - 16:37 17:35 -",
    ),
    (
        "Bad Kreuznach, Mercedes",
        "7:06 7:29 8:36 9:36 12:36 13:38 - 14:36 15:36 - 16:38 17:36 -",
    ),
    (
        "Bad Kreuznach, Michelin",
        "7:09 7:32 8:39 9:39 12:39 13:41 14:19 14:39 15:39 15:49 16:41 17:39 22:19",
    ),
    (
        "Bad Kreuznach, Otto-Meffert-Str./oddAG",
        "7:10 7:33 8:40 9:40 12:40 13:42 14:20 14:40 15:40 15:50 16:42 17:40 22:20",
    ),
    (
        "Bad Kreuznach, Sandweg",
        "7:11 7:34 8:41 9:41 12:41 13:43 14:21 14:41 15:41 15:51 16:43 17:41 22:21",
    ),
    (
        "Bad Kreuznach, Seitz-Werke",
        "7:12 7:35 8:42 9:42 12:42 13:44 14:22 14:42 15:42 15:52 16:44 17:42 22:22",
    ),
    (
        "Bad Kreuznach, Heidenmauer",
        "7:13 7:36 8:43 9:43 12:43 13:45 14:23 14:43 15:43 15:53 16:45 17:43 22:23",
    ),
    (
        "Bad Kreuznach, Gensinger Straße",
        "7:14 7:37 8:44 9:44 12:44 13:46 14:24 14:44 15:44 15:54 16:46 17:44 22:24",
    ),
    (
        "Bad Kreuznach, Bahnhof",
        "7:17 7:40 8:47 9:47 12:47 13:49 14:27 14:47 15:47 15:57 16:49 17:47 22:27",
    ),
]


def main():
    path = ROOT / "data/reviewed-ocr" / NAME.replace(".pdf", ".json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert (
        payload["source_sha256"]
        == hashlib.sha256((ROOT / "data/pdf-quellen" / NAME).read_bytes()).hexdigest()
    )
    header = payload["pages"]["1"]["text"].split("\n\nFahrt ")[0]
    header += "\nIn beiden Richtungen steht zwischen den 9-Uhr- und 12-Uhr-Spalten: alle 60 Min. Fahrt 104 trägt S (nur an Schultagen in Rheinland-Pfalz)."
    trips = []
    for direction, ids, rows in [
        ("Richtung Bosenheim/Ippesheim", OUT_IDS, OUT),
        ("Richtung Bad Kreuznach Bahnhof", IN_IDS, IN),
    ]:
        assert all(len(times.split()) == len(ids) for _, times in rows)
        for col, trip in enumerate(ids):
            stops = [
                {"stop": stop, "time": times.split()[col]}
                for stop, times in rows
                if times.split()[col] != "-"
            ]
            trips.append(
                {
                    "trip": trip,
                    "direction": direction,
                    "days": "Montag bis Freitag",
                    "school_only": trip == 104,
                    "stops": stops,
                }
            )
    blocks = [header]
    for trip in trips:
        restrictions = (
            "; nur an Schultagen in Rheinland-Pfalz" if trip["school_only"] else ""
        )
        blocks.append(
            f"Fahrt {trip['trip']}, Linie 216, {trip['direction']}, Montag bis Freitag{restrictions}:\n"
            + "\n".join(f"{s['stop']}: {s['time']} Uhr" for s in trip["stops"])
        )
    payload["pages"]["1"].update(
        text="\n\n".join(blocks), quality="visually_verified", trips=trips
    )
    payload["review"] = (
        "All 25 explicitly numbered trip columns, 18 outbound and 21 inbound stop rows and printed restrictions checked against 230-dpi original rendering. Blank cells preserved; intermediate repeat trips not assigned invented IDs."
    )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
