"""Retrieval expectations from docs/FRAGENKATALOG_JARVIS.md (68 cases)."""

from __future__ import annotations

from typing import TypedDict


class CatalogCase(TypedDict):
    id: str
    query: str
    filenames: list[str]
    pages: list[int]
    must_contain: list[str]
    refusal: bool


JUBILAEEN = "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
VERSPAETUNG = "BV_Regelung von Fahrzeugverspätungen.pdf"
SCHUELER = "DA001-2026 Schülerbeförderung.pdf"
EC_GERAET = "DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf"
FAHRPLAN = "DOC-20260920-WA0002.pdf"
NETZPLAN = "DOC-20260920-WA0003.pdf"
PREISTAFEL = "DOC-20260920-WA0004.pdf"
BROSCHUERE = "DOC-20260920-WA0005.pdf"


def _case(
    case_id: str,
    query: str,
    filenames: list[str],
    pages: list[int],
    must_contain: list[str],
    *,
    refusal: bool = False,
) -> CatalogCase:
    return {
        "id": case_id,
        "query": query,
        "filenames": filenames,
        "pages": pages,
        "must_contain": must_contain,
        "refusal": refusal,
    }


CATALOG_CASES: list[CatalogCase] = [
    _case(
        "J01",
        "Fuer wen gilt die Betriebsvereinbarung zu Jubilaeen?",
        [JUBILAEEN],
        [3],
        ["beschaeftigten", "geringfuegig", "werkstudierende"],
    ),
    _case(
        "J02",
        "Was bekomme ich bei 10 Jahren Betriebszugehoerigkeit?",
        [JUBILAEEN],
        [3],
        ["100", "25"],
    ),
    _case(
        "J03",
        "Was bekomme ich bei 25 Jahren Betriebszugehoerigkeit?",
        [JUBILAEEN],
        [3],
        ["250", "25"],
    ),
    _case(
        "J04",
        "Was bekomme ich bei 40 Jahren Betriebszugehoerigkeit?",
        [JUBILAEEN],
        [3],
        ["400", "freier tag"],
    ),
    _case(
        "J05",
        "Was bekomme ich bei 50 Jahren Betriebszugehoerigkeit?",
        [JUBILAEEN],
        [3],
        ["500", "zwei"],
    ),
    _case(
        "J06",
        "Zu welchen runden Geburtstagen gibt es ein Geschenk?",
        [JUBILAEEN],
        [3, 4],
        ["20", "30", "80", "25"],
    ),
    _case(
        "J07",
        "Wann gibt es ein Genesungspaket?",
        [JUBILAEEN],
        [4],
        ["acht wochen", "25"],
    ),
    _case(
        "J08",
        "Wohin wird das Genesungspaket geschickt?",
        [JUBILAEEN],
        [4],
        ["privatadresse"],
    ),
    _case(
        "J09",
        "Was gibt es bei einem alters- oder krankheitsbedingten Austritt?",
        [JUBILAEEN],
        [4],
        ["25", "karte"],
    ),
    _case(
        "J10",
        "Seit wann gilt diese Betriebsvereinbarung zu Jubilaeen?",
        [JUBILAEEN],
        [4],
        ["01.07.2026"],
    ),
    _case(
        "V01",
        "Fuer wen gilt die Regelung zu Fahrzeugverspaetungen?",
        [VERSPAETUNG],
        [3],
        ["kommunalverkehr", "rhein-nahe"],
    ),
    _case(
        "V02",
        "Wie wird eine Fahrzeugverspaetung von 20 Minuten verguetet?",
        [VERSPAETUNG],
        [3],
        ["minutengenau", "arbeitszeit"],
    ),
    _case(
        "V03",
        "Wie werden Verspaetungen bis einschliesslich 30 Minuten verguetet?",
        [VERSPAETUNG],
        [3],
        ["30", "minutengenau"],
    ),
    _case(
        "V04",
        "Wie werden Verspaetungen von mehr als 30 Minuten verguetet?",
        [VERSPAETUNG],
        [3],
        ["halbe stunde", "beztv"],
    ),
    _case(
        "V05",
        "Wann und wo muss ich die Verspaetung melden?",
        [VERSPAETUNG],
        [3],
        ["dienstende", "leitstelle"],
    ),
    _case(
        "V06",
        "Wird eine spaeter nachgemeldete Verspaetung beruecksichtigt?",
        [VERSPAETUNG],
        [3],
        ["nicht beruecksichtigt"],
    ),
    _case(
        "V07",
        "Seit wann gilt die Betriebsvereinbarung zu Fahrzeugverspaetungen?",
        [VERSPAETUNG],
        [3],
        ["01.07.2026"],
    ),
    _case(
        "S01",
        "Was mache ich, wenn ein Schueler auf dem Schulweg kein gueltiges Ticket hat?",
        [SCHUELER],
        [1],
        ["name", "schule", "qualitaetsmanagement"],
    ),
    _case(
        "S02",
        "Muss ich das Ticket eines Schuelers beim Einstieg kontrollieren?",
        [SCHUELER],
        [1],
        ["einstieg", "kontrollieren"],
    ),
    _case(
        "S03",
        "Darf ich einen Grundschueler ohne Ticket auf dem Schulweg stehen lassen?",
        [SCHUELER],
        [1],
        ["dennoch", "befoerderung"],
    ),
    _case(
        "S04",
        "Welche Daten soll ich bei einem Kind ohne gueltiges Ticket notieren?",
        [SCHUELER],
        [1],
        ["name", "schule"],
    ),
    _case(
        "S05",
        "Wohin muss der Vorfall eines Kindes ohne Ticket gemeldet werden?",
        [SCHUELER],
        [1],
        ["qualitaetsmanagement"],
    ),
    _case(
        "S06",
        "Fahren ausserhalb der Schulzeiten alle Kinder generell kostenlos?",
        [SCHUELER],
        [1],
        ["ausdruecklich nicht"],
    ),
    _case(
        "S07",
        "Was gilt bei Dunkelheit, schlechtem Wetter oder in abgelegenen Bereichen?",
        [SCHUELER],
        [1],
        ["nicht zurueckgelassen", "fuersorgepflicht"],
    ),
    _case(
        "S08",
        "Seit wann gilt die Dienstanweisung DA001-2026?",
        [SCHUELER],
        [1],
        ["13.01.2026"],
    ),
    _case(
        "E01",
        "Hat ein Fahrgast Anspruch auf Kartenzahlung?",
        [EC_GERAET],
        [1],
        ["anspruch", "nicht"],
    ),
    _case(
        "E02",
        "Was muss ich einem Fahrgast sagen, wenn das EC-Geraet defekt ist?",
        [EC_GERAET],
        [1],
        ["keine kartenzahlung"],
    ),
    _case(
        "E03",
        "Wie ist der Fahrpreis bei defektem EC-Geraet zu bezahlen?",
        [EC_GERAET],
        [1],
        ["bar"],
    ),
    _case(
        "E04",
        "Was gilt, wenn der Fahrgast nicht bar bezahlen kann?",
        [EC_GERAET],
        [1],
        ["ohne gueltigen fahrschein", "befoerderungsbedingungen"],
    ),
    _case(
        "E05",
        "Wem muss ich den Defekt des EC-Geraets melden?",
        [EC_GERAET],
        [1],
        ["leitstelle"],
    ),
    _case(
        "E06",
        "Wie soll ich mit Fahrgaesten ueber den Ausfall sprechen?",
        [EC_GERAET],
        [1],
        ["sachlich", "ruhig"],
    ),
    _case(
        "E07",
        "Seit wann gilt die Dienstanweisung 003-2026?",
        [EC_GERAET],
        [1],
        ["01.06.2026"],
    ),
    _case(
        "T01",
        "Wie ermittle ich die Preisstufe?",
        [PREISTAFEL, BROSCHUERE],
        [1, 3],
        ["waben", "preisstufe", "300"],
    ),
    _case(
        "T02",
        "Was ist die hoechste Preisstufe im RNN?",
        [PREISTAFEL],
        [1],
        ["preisstufe 10"],
    ),
    _case(
        "T03",
        "Was kostet eine Einzelfahrkarte fuer Erwachsene in Preisstufe 1?",
        [PREISTAFEL],
        [1],
        ["2,60"],
    ),
    _case(
        "T04",
        "Was kostet eine Einzelfahrkarte fuer Erwachsene im gesamten RNN-Netz?",
        [PREISTAFEL],
        [1],
        ["17,40"],
    ),
    _case(
        "T05",
        "Was kostet das Deutschland-Ticket?",
        [BROSCHUERE, PREISTAFEL],
        [1, 7],
        ["63"],
    ),
    _case(
        "T06",
        "Darf ich mit dem Deutschland-Ticket jemanden mitnehmen?",
        [BROSCHUERE],
        [7],
        ["keine weiteren personen", "unter 6"],
    ),
    _case(
        "T07",
        "Gilt das Deutschland-Ticket in der 1. Klasse?",
        [BROSCHUERE],
        [7],
        ["2. klasse", "zuschlag"],
    ),
    _case(
        "T08",
        "Wann ist die Fahrradmitnahme kostenpflichtig?",
        [PREISTAFEL, BROSCHUERE],
        [1, 13],
        ["6", "9"],
    ),
    _case(
        "T09",
        "Was kostet das Rheinland-Pfalz-Ticket fuer drei Personen?",
        [BROSCHUERE],
        [6],
        ["50", "30", "10"],
    ),
    _case(
        "T10",
        "Wie lange gilt eine Tageskarte?",
        [BROSCHUERE],
        [5],
        ["4 uhr"],
    ),
    _case(
        "T11",
        "Wie viele Personen duerfen mit einer Gruppen-Tageskarte fahren?",
        [BROSCHUERE],
        [5],
        ["5 personen"],
    ),
    _case(
        "T12",
        "Wie viele Personen duerfen als Kindergartengruppe mit der Gruppen-Tageskarte fahren?",
        [BROSCHUERE],
        [5],
        ["15", "5"],
    ),
    _case(
        "T13",
        "Was passiert beim Kauf einer Mehrfahrtenkarte?",
        [BROSCHUERE],
        [4],
        ["entwertet"],
    ),
    _case(
        "T14",
        "Gelten Zeitkarten ab August 2026 nur fuer bestimmte Waben?",
        [BROSCHUERE],
        [3, 9],
        ["gesamten", "1.8.2026"],
    ),
    _case(
        "T15",
        "Ab wann gilt die 9-Uhr-Zeitkarte?",
        [BROSCHUERE],
        [10],
        ["9 uhr", "wochenende"],
    ),
    _case(
        "T16",
        "Was passiert, wenn ich meine persoenliche Jahreskarte Jedermann vergessen habe?",
        [BROSCHUERE],
        [9],
        ["7", "60"],
    ),
    _case(
        "T17",
        "Was ist ein RNN-KombiTicket?",
        [BROSCHUERE],
        [14],
        ["eintrittskarte", "4 uhr"],
    ),
    _case(
        "T18",
        "Wann soll ein Gruppenausflug angemeldet werden?",
        [BROSCHUERE],
        [5],
        ["eine woche"],
    ),
    _case(
        "F01",
        "Welche Strecke zeigt der Fahrplan der Linie 216?",
        [FAHRPLAN],
        [1],
        ["bad kreuznach", "michelin", "bosenheim"],
    ),
    _case(
        "F02",
        "Was bedeutet das S im Fahrplan der Linie 216?",
        [FAHRPLAN],
        [1],
        ["schultagen"],
    ),
    _case(
        "F03",
        "Wann faehrt Fahrt 125 montags bis freitags am Bad Kreuznacher Bahnhof ab und wann ist sie bei Michelin?",
        [FAHRPLAN],
        [1],
        ["5:32", "5:39"],
    ),
    _case(
        "F04",
        "Was gilt am 24. und 31. Dezember fuer die Linie 216?",
        [FAHRPLAN],
        [1],
        ["samstag"],
    ),
    _case(
        "F05",
        "Seit wann gilt der RNN-Gesamtnetzplan 2025?",
        [NETZPLAN],
        [1],
        ["15.12.2024"],
    ),
    _case(
        "F06",
        "Kannst du mir aus dem Netzplan die aktuelle Verspaetung nennen?",
        [NETZPLAN],
        [1],
        [],
        refusal=True,
    ),
    _case(
        "M01",
        "EC cihazi bozuksa ne yapmaliyim?",
        [EC_GERAET],
        [1],
        ["kartenzahlung", "leitstelle"],
    ),
    _case(
        "M02",
        "Sekiz haftadan uzun suredir hastaysam iyilesme paketi alir miyim?",
        [JUBILAEEN],
        [4],
        ["acht wochen", "25"],
    ),
    _case(
        "M03",
        "How is a 20-minute vehicle delay compensated?",
        [VERSPAETUNG],
        [3],
        ["minutengenau", "arbeitszeit"],
    ),
    _case(
        "M04",
        "Can I take another adult with me on the Deutschland-Ticket?",
        [BROSCHUERE],
        [7],
        ["keine weiteren personen"],
    ),
    _case(
        "M05",
        "Ce trebuie sa fac daca un elev nu are bilet valabil in drum spre scoala?",
        [SCHUELER],
        [1],
        ["name", "schule", "qualitaetsmanagement"],
    ),
    _case(
        "M06",
        "Czy Deutschland-Ticket jest wazny w pierwszej klasie?",
        [BROSCHUERE],
        [7],
        ["2. klasse"],
    ),
    _case(
        "M07",
        "Що я отримаю за 40 років роботи в компанії?",
        [JUBILAEEN],
        [3],
        ["400"],
    ),
    _case(
        "M08",
        "ماذا أفعل إذا كان جهاز الدفع بالبطاقة معطلاً؟",
        [EC_GERAET],
        [1],
        ["kartenzahlung", "leitstelle"],
    ),
    _case(
        "N01",
        "Wie ist die aktuelle Verkehrslage auf meiner Linie?",
        [],
        [],
        [],
        refusal=True,
    ),
    _case(
        "N02",
        "Hat der Bus heute 15 Minuten Verspaetung?",
        [],
        [],
        [],
        refusal=True,
    ),
    _case(
        "N03",
        "Welche arbeitsrechtlichen Ansprueche habe ich ausserhalb dieser Betriebsvereinbarungen?",
        [JUBILAEEN, VERSPAETUNG],
        [3, 4],
        [],
        refusal=True,
    ),
    _case(
        "N04",
        "Was genau passiert mit dem Fahrgast ohne Bargeld bei defektem EC-Geraet?",
        [EC_GERAET],
        [1],
        ["befoerderungsbedingungen"],
        refusal=True,
    ),
]


assert len(CATALOG_CASES) == 68
assert len({case["id"] for case in CATALOG_CASES}) == 68
