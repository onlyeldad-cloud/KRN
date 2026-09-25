# Testprotokoll: KRN-Dokumentwissen

Stand: 2026-09-23  
Agent: bestehender LiveKit/Gemini-Live-Agent (`gemini-3.1-flash-live-preview`)  
Index: `data/index/krn_docs.json` (126 Chunks, 9 PDFs)  
Umgebung: Windows, `.venv-windows313`, `uv`

## Kurzfassung

| Kennzahl | Wert |
| --- | ---: |
| PDFs eingebunden | 9 von 9 |
| Fragen getestet (Retrieval) | 68 von 68 |
| Retrieval korrekt | 68 |
| Teilweise korrekt | 0 |
| Falsch | 0 |
| Fremdsprachen (M01–M08) | 8 von 8 finden die deutsche Quelle |
| Ablehnungen ohne Echtzeit-Erfindung (F06, N01, N02) | 3 von 3 |
| Offline-Pytest | 92 bestanden (KRN-Docs, Wetter, Websuche, Browser, Vision-Memory) |

Die 68 Fälle prüfen die lokale Suche, nicht eine Live-Gemini-Antwort.
Sprache, Zitatformat und Tool-Routing sind in den Agent-Anweisungen hinterlegt.

## Automatische Retrieval-Serie

Befehl:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv run python scripts/run_krn_catalog.py
uv run pytest tests/test_krn_docs.py -q
```

Rohdaten: `data/index/catalog_retrieval.json`

| Gruppe | IDs | Ergebnis |
| --- | --- | --- |
| Jubiläen | J01–J10 | bestanden |
| Fahrzeugverspätungen | V01–V07 | bestanden |
| Schülerbeförderung | S01–S08 | bestanden |
| EC-Geräte | E01–E07 | bestanden |
| Tarife | T01–T18 | bestanden |
| Fahrplan/Netz | F01–F05 | bestanden |
| Echtzeit-Ablehnung | F06, N01, N02 | `no_evidence`, keine erfundenen Verspätungen |
| Fremdsprache → deutscher Treffer | M01–M08 | bestanden |
| Begrenzte Auskunft | N03, N04 | Treffer nur aus vorhandenen BV/DA-Stellen |

## Pytest

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-windows313'
uv run pytest tests/test_krn_docs.py tests/test_weather.py tests/test_web_search.py tests/test_browser.py tests/test_vision_memory.py -q
```

Ergebnis: 92 bestanden.

Nicht in diesem Lauf (Live-Inferenz, unverändert gelassen):
`tests/test_german.py`, `tests/test_search_behavior.py`, `tests/test_docs_browser.py`, `tests/test_vision.py`.

## Bestehende Fähigkeiten

Diese Dateien wurden für das Dokumentwissen nicht umgebaut:
`src/weather.py`, `src/web_search.py`, `src/browser_tools.py`, Frontend, Gemini `RealtimeModel`.

`Assistant` registriert weiterhin `search_web`, `get_weather` und die Playwright-Browser-Tools.
Neu ist nur `search_krn_docs`.

## Manueller Probelauf

1. `.\start-agent.cmd` und `.\start-web.cmd`
2. Gespräch starten (Mikrofon oder Textchat)
3. Dokumentfrage: „Was bekomme ich bei 10 Jahren Betriebszugehörigkeit?“
   Erwartung: 100 Euro, 25-Euro-Sachgeschenk, `[Quelle: BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf, Seite 3]`
4. Fremdsprache: „How is a 20-minute vehicle delay compensated?“
   Erwartung: Antwort auf Englisch, Quelle BV Verspätungen, Seite 3
5. Ablehnung: „Hat der Bus heute 15 Minuten Verspätung?“
   Erwartung: keine Echtzeit, kein Web-Fallback
6. Kontrolle, dass Unverwandtes weiter geht: Wetter Berlin, Websuche, Browser, Kamera

## Bekannte Grenzen

- RapidOCR hat auf den Bild-BVs einzelne Zeilen verschluckt (40-Jahre-Prämie, Austrittsgeschenk). Diese Stellen wurden gegen die gerenderte Seite nachgetragen.
- Fahrplan-OCR liest Zeiten zuverlässig für Fahrt 125; andere Spalten können versetzt sein.
- Netz- und Wabenplan liefern nur Titel, Gültigkeit und Servicefakten, keine Routen.
- Die 68 Katalogfälle sind Retrieval-Tests. Die gesprochene Formulierung hängt weiter von Gemini Live ab.
