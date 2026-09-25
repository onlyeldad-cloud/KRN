# Quelleninventar der KRN-PDFs

Stand: 2026-09-23

Originale liegen unverändert in `data/pdf-quellen/`. Abgeleiteter Text
liegt in `data/aufbereitet/`. Der lexikalische Index ist `data/index/krn_docs.json`.

| Dateiname | Art | Nummer | PDF-Seiten | Gültig ab | Gültig bis | Stelle | Text/Bild | OCR |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf` | Betriebsvereinbarung | 2026-04 | 5 | 01.07.2026 | unbestimmt | KRN | Bild | Ja |
| `BV_Regelung von Fahrzeugverspätungen.pdf` | Betriebsvereinbarung | 2026-06 | 4 | 01.07.2026 | unbestimmt | KRN Kommunalverkehr Rhein-Nahe GmbH | Bild | Ja |
| `DOC-20260920-WA0002.pdf` | Fahrplan Linie 216 | — | 1 | aus Dokument | — | RNN / KRN | Bild, Tabelle | Ja |
| `DA001-2026 Schülerbeförderung.pdf` | Dienstanweisung | DA001-2026 | 1 | 13.01.2026 | auf Weiteres | Planung und Produktion | Text | Nein |
| `DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf` | Dienstanweisung | 003-2026 | 1 | 01.06.2026 | auf Weiteres | Produktion und Planung | Text | Nein |
| `DOC-20260920-WA0004.pdf` | Preistafel | Preise 2026 | 1 | 01.08.2026 | — | RNN | Text, Tabelle | Nein |
| `DOC-20260920-WA0005.pdf` | Tarifbroschüre | Preise & Fahrkarten | 15 | 01.08.2026 | — | RNN GmbH | Text | Nein |
| `DOC-20260920-WA0003.pdf` | Gesamtnetzplan | RNN 2025 | 1 | 15.12.2024 | — | RNN GmbH | Karte | Fakten |
| `DOC-20260920-WA0006.pdf` | Wabenplan | Stand 01.08.2026 | 1 | 01.08.2026 | — | RNN | Karte | Fakten |

## OCR-Hinweise

- RapidOCR (`rapidocr` + `onnxruntime`) läuft nur in `scripts/prepare_krn_docs.py`.
- Bild-PDFs: beide Betriebsvereinbarungen (alle Seiten) und der Fahrplan Linie 216.
- RapidOCR hat auf BV 2026-04 Seite 3 die 40-Jahre-Zeile und auf Seite 4 die
  Austrittszeile verschluckt. Beide wurden gegen die gerenderte Seite ergänzt.
- Präambeln und Unterschriftenzeilen bleiben stellenweise lückenhaft; die
  Regelparagraphen sind lesbar.
- Fahrplanzeiten wurden von `5.32` auf `5:32` normalisiert. Fahrt 125 ist
  belegt; andere Spalten können versetzt sein.
- Netz- und Wabenplan: keine OCR der gesamten Karte, nur extrahierbare Fakten.

## Aufbereitungsregeln

- Originaldateien werden nur kopiert, nie überschrieben.
- Jeder Abschnitt trägt den Originaldateinamen und die 1-basierte PDF-Seite.
- Weicht eine gedruckte Seitenzahl ab, steht sie zusätzlich als `printed_page`.
- Tabellen bleiben Markdown/JSON, kein plattgedrückter Fließtext.
- Netz- und Wabenplan: nur sicher lesbare Fakten (Titel, Gültigkeit, Herausgeber, Service). Keine erfundenen Linienverbindungen.
- Bild-PDFs werden nur beim Vorbereiten per OCR gelesen, nicht zur Laufzeit.

## Themen

- Jubiläen, Geburtstage, Genesungspakete, Austritte
- Fahrzeugverspätungen und Meldung an die Leitstelle
- Schülerbeförderung ohne gültiges Ticket
- Defekte EC-Geräte
- RNN-Preisstufen, Tickets, Fahrradmitnahme
- Linie 216, Gesamtnetz 2025, Wabenplan 2026
