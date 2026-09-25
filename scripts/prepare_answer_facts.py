"""Prepare short reviewed answers offline, with immutable page provenance.

No catalog imports or query-answer lookup: topic predicates select source facts.
Raw page text remains separately indexed for document exploration.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
J = "BV_Regelung von Betriebsjubiläen, Ehrungen und Genesungspaketen.pdf"
V = "BV_Regelung von Fahrzeugverspätungen.pdf"
S = "DA001-2026 Schülerbeförderung.pdf"
E = "DA003-2026_KRN_Umgang_mit_defekten_EC-Geräten_Alternative 2.pdf"
B = "DOC-20260920-WA0005.pdf"
P = "DOC-20260920-WA0004.pdf"
F = "DOC-20260920-WA0002.pdf"
N = "DOC-20260920-WA0003.pdf"
W = "DOC-20260920-WA0006.pdf"
REVIEWED_HASHES = {
    J: "9d0f431a505f45092bd4cc9d1f2ebab270cccab0edb84d17ed968e375557d066",
    V: "4a386aaed3d4e6d435eced5d4349dbed3889d52f3263c47cde839a8027b5207c",
    S: "bc895d7d43c133579f25a4ad88f0e25973bdc5955e46d7f300cdff43a0c2aaee",
    E: "68ed89eb7234f0044913699d4c84deba59c9a8da5bdc69ef190963b540bd31d9",
    F: "68468e78ada688ac8c5cbc1a2cf6dcd1f50fccd5f57de4fb2b786c23f861404b",
    N: "18870419f483f877fa1ac8ec960d50e5f28a8584ff052959126f74295509c3d5",
    P: "2e154ae5003650aaa39e7b2d2d411860b03a2db2d37aebc5cafe4f4359ab93de",
    B: "54d74cc82a721c017ff70bc21d13521c93543ff8448d610e41b6b50f1f118bfa",
    W: "bea4b8bd563e939cea56a977201cacde0b4b619f002796efd3483b2e1e9bf742",
}


def main():
    cards = []

    def add(key, file, pages, patterns, de, en, fr, priority=10):
        source = ROOT / "data/pdf-quellen" / file
        if hashlib.sha256(source.read_bytes()).hexdigest() != REVIEWED_HASHES[file]:
            raise ValueError(
                f"Source changed; answer facts require a new review: {file}"
            )
        prepared = (ROOT / "data/aufbereitet" / f"{source.stem}.md").read_text(
            encoding="utf-8"
        )
        page_texts = dict(
            re.findall(
                r"## PDF-Seite (\d+)\n(.*?)(?=\n## PDF-Seite |\Z)", prepared, re.S
            )
        )
        cards.append(
            {
                "id": key,
                "filename": file,
                "page": pages[0],
                "pages": pages,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "evidence": [
                    {"page": page, "text": page_texts[str(page)].strip()}
                    for page in pages
                ],
                "patterns": patterns,
                "priority": priority,
                "answers": {"de": de, "en": en, "fr": fr},
            }
        )

    anniversary = r"jubilae|betriebszugehoer|jahre[n]? (?:bei krn|gearbeitet)|years of service|years with|anciennete|років|отримаю"
    add(
        "anniversary-scope",
        J,
        [3],
        [anniversary, r"wen|geltungsbereich|who|qui|excluded"],
        "Die Betriebsvereinbarung gilt für alle Beschäftigten der KRN-Kommunalverkehr Rhein-Nahe GmbH. Ausgenommen sind geringfügig Beschäftigte, kurzfristig Beschäftigte und Werkstudierende.",
        "The agreement covers KRN employees, except marginal and short-term employees and working students.",
        "L'accord couvre les salariés KRN, sauf les emplois marginaux, les emplois de courte durée et les étudiants salariés.",
        30,
    )
    for year, amount, days in [
        (10, 100, 0),
        (20, 200, 0),
        (25, 250, 0),
        (30, 300, 0),
        (40, 400, 1),
        (50, 500, 2),
    ]:
        leave_de = (
            ""
            if not days
            else (
                " Dazu kommt ein zusätzlicher freier Tag unter Fortzahlung des Arbeitsentgelts."
                if days == 1
                else " Dazu kommen zwei zusätzliche freie Tage unter Fortzahlung des Arbeitsentgelts."
            )
        )
        add(
            f"anniversary-{year}",
            J,
            [3],
            [anniversary, rf"\b{year}\s*(?:jahre|years|ans|років)"],
            f"Bei {year} Jahren ununterbrochener Betriebszugehörigkeit erhältst du {amount} Euro Jubiläumsprämie sowie ein Sachgeschenk im Wert von 25 Euro. Die Auszahlung erfolgt im Folgemonat nach Vollendung des Jubiläums."
            + leave_de,
            f"After {year} years of continuous service you receive {amount} euros and a gift worth 25 euros. The premium is paid in the following month."
            + (f" You also receive {days} additional paid days off." if days else ""),
            f"Après {year} ans d'ancienneté ininterrompue, tu reçois {amount} euros et un cadeau d'une valeur de 25 euros. La prime est versée le mois suivant."
            + (
                f" Tu reçois aussi {days} jours de congé payé supplémentaires."
                if days
                else ""
            ),
            40,
        )
    add(
        "anniversary-effective",
        J,
        [4],
        [anniversary, r"seit wann|gueltig|inkraft|effective|entree en vigueur"],
        "Die Betriebsvereinbarung zu Jubiläen gilt ab 01.07.2026 auf unbestimmte Zeit. Sie ist mit einer Frist von 12 Monaten zum Jahresende kündbar, frühestens zum 31.12.2028; die Kündigung muss schriftlich erfolgen.",
        "The anniversary agreement takes effect on 01.07.2026 for an indefinite period. Either party may terminate it in writing with 12 months' notice to year-end, no earlier than 31.12.2028.",
        "L'accord sur l'ancienneté prend effet le 01.07.2026 pour une durée indéterminée. Résiliation écrite avec préavis de 12 mois en fin d'année, au plus tôt le 31.12.2028.",
        40,
    )
    add(
        "birthdays",
        J,
        [3, 4],
        [r"geburtstag|birthday|anniversaire de naissance"],
        "Zum 20., 30., 40., 50., 60., 70. und 80. Geburtstag erhalten Mitarbeitende eine Gratulation und ein Sachgeschenk im Wert von 25 Euro.",
        "Employees receive congratulations and a gift worth 25 euros on their 20th, 30th, 40th, 50th, 60th, 70th and 80th birthdays.",
        "Les salariés reçoivent des félicitations et un cadeau de 25 euros pour leurs 20, 30, 40, 50, 60, 70 et 80 ans.",
    )
    add(
        "recovery",
        J,
        [4],
        [r"genesung|recovery package|illness|maladie|iyilesme|hastaysam"],
        "Bei einer Erkrankung von mehr als acht Wochen gibt es einmalig pro Krankheitsfall ein Genesungspaket mit einem Sachgeschenk im Wert von 25 Euro. Es wird grundsätzlich an die Privatadresse versendet. Die Geschäftsleitung kann es in begründeten Einzelfällen schon früher gewähren.",
        "After more than eight weeks of illness, a recovery package with a gift worth 25 euros is sent to your private address, once per illness. Management may grant it earlier in justified individual cases.",
        "Après plus de huit semaines de maladie, un cadeau de 25 euros est envoyé à l'adresse privée, une fois par maladie. La direction peut l'accorder plus tôt dans des cas individuels justifiés.",
    )
    add(
        "leaving",
        J,
        [4],
        [r"austritt|altersbedingt|krankheitsbedingt|retirement gift|depart.*retraite"],
        "Bei alters- oder krankheitsbedingtem Unternehmensaustritt gibt es ein Sachgeschenk im Wert von 25 Euro sowie eine persönliche Karte.",
        "Employees leaving due to age or illness receive a gift worth 25 euros and a personal card.",
        "En cas de départ lié à l'âge ou à la maladie, un cadeau de 25 euros et une carte personnelle sont prévus.",
    )
    add(
        "delays",
        V,
        [3],
        [r"verspaet|vehicle delay|retard|20.minute"],
        "Die Regelung gilt für alle Beschäftigten der KRN-Kommunalverkehr Rhein-Nahe GmbH seit 01.07.2026. Fahrzeugverspätungen von 0 bis einschließlich 30 Minuten werden minutengenau als Arbeitszeit vergütet. Bei mehr als 30 Minuten wird jede angefangene halbe Stunde als halbe Stunde gemäß § 6 Abs. 3 BezTV-N RP vergütet. Unverzüglich bei Dienstende an die Leitstelle melden; nachträglich gemeldete Verspätungen werden nicht berücksichtigt.",
        "The rule covers all KRN employees from 01.07.2026. Delays up to 30 minutes are paid minute by minute as working time. Above 30 minutes, each started half-hour is paid as half an hour under § 6(3) BezTV-N RP. Report the delay to the control centre immediately at the end of duty; late reports are not accepted.",
        "La règle s'applique à tous les salariés KRN depuis le 01.07.2026. Jusqu'à 30 minutes, le retard est rémunéré à la minute comme temps de travail. Au-delà, chaque demi-heure entamée est rémunérée comme une demi-heure selon le § 6(3) BezTV-N RP. Signaler le retard à la régulation immédiatement en fin de service ; les signalements tardifs ne sont pas pris en compte.",
    )
    add(
        "school",
        S,
        [1],
        [
            r"schueler|grundschueler|schulweg|schulzeit|kind.*ticket|ticket.*kind|dunkelheit|abgelegenen|da001|pupil|school|eleve|scolaire|scoala|bilet"
        ],
        "Nach DA001-2026, gültig ab 13.01.2026: Auf dem Schulweg ist beim Einstieg das Ticket zu kontrollieren. Ohne gültiges Ticket Name und Schule notieren; die Beförderung zur Schule und zurück hat dennoch zu erfolgen. Den Vorfall danach schriftlich an das Qualitätsmanagement melden. Außerhalb der Schulzeiten und Ferien gilt eine besondere Fürsorgepflicht: Kinder dürfen insbesondere bei Dunkelheit, schlechter Witterung oder in abgelegenen Bereichen nicht zurückgelassen werden. Eine generell kostenfreie Beförderung erfolgt ausdrücklich nicht.",
        "DA001-2026 applies from 13.01.2026. Check tickets on boarding. On the way to and from school, transport pupils even without a valid ticket, record their name and school, and report the incident in writing to quality management. Outside school times and holidays, a special duty of care applies: do not leave children behind, especially in darkness, bad weather or remote areas. This does not mean generally free transport.",
        "DA001-2026 s'applique depuis le 13.01.2026. Contrôler le billet à la montée. Sur le trajet scolaire aller-retour, transporter l'élève même sans billet valide, noter son nom et son école, puis signaler l'incident par écrit à la gestion de la qualité. Hors périodes scolaires et vacances, une obligation particulière de protection s'applique : ne pas abandonner les enfants, notamment dans l'obscurité, par mauvais temps ou dans des lieux isolés. Le transport n'est pas gratuit de façon générale.",
    )
    add(
        "card-reader",
        E,
        [1],
        [
            r"ec.geraet|kartenzahl|bargeld|bar bezahlen|bar bezahlen|fahrpreis.*bezahl|fahrgaest.*ausfall|card reader|card payment|paiement par carte|cihaz|bozuk|جهاز|الدفع|003.2026"
        ],
        "Nach Dienstanweisung 003-2026, gültig ab 01.06.2026, besteht kein Anspruch auf bargeldlose Zahlung. Bei einem Defekt informieren, dass keine Kartenzahlung möglich ist; der Fahrpreis ist bar zu entrichten. Ohne Barzahlung gilt dies als Fahrt ohne gültigen Fahrschein; es gelten die Beförderungsbedingungen, deren weitere Schritte diese Anweisung nicht festlegt. Den Defekt unverzüglich der Leitstelle melden. Gespräche sachlich und ruhig führen, freundlich, aber bestimmt auf die Regeln hinweisen.",
        "Under instruction 003-2026, effective 01.06.2026, passengers have no entitlement to card payment. Explain that card payment is unavailable and the fare must be paid in cash. Without cash payment, this counts as travel without a valid ticket; follow the conditions of carriage, whose further steps are not specified here. Report the fault immediately to the control centre. Speak calmly and factually, politely but firmly.",
        "Selon l'instruction 003-2026, applicable depuis le 01.06.2026, il n'existe aucun droit au paiement par carte. Informer le voyageur que ce paiement est impossible et demander le paiement en espèces. Sans paiement en espèces, il s'agit d'un trajet sans titre valide ; appliquer les conditions de transport, sans inventer les étapes non précisées ici. Signaler immédiatement la panne à la régulation et rester calme, factuel, aimable et ferme.",
    )
    add(
        "price-zones",
        P,
        [1],
        [
            r"preisstufe|tariff level|niveau tarifaire",
            r"ermitt|berechn|wabe|determin|calcul",
        ],
        "Zähle die durchfahrenen Waben von Start bis Ziel. Die Wabenanzahl ergibt die Preisstufe. Die Großwabe Mainz/Wiesbaden (300) zählt als zwei Waben. Die höchste Preisstufe ist 10 für das gesamte RNN-Netz; Sonderpreisstufen sind zu beachten.",
        "Count the fare zones crossed from start to destination to determine the tariff level. Mainz/Wiesbaden zone 300 counts as two zones. Level 10 covers the entire RNN network; special tariff levels also apply.",
        "Compter les zones traversées pour déterminer le niveau tarifaire. La grande zone 300 Mainz/Wiesbaden compte pour deux zones. Le niveau 10 couvre tout le réseau RNN ; des niveaux spéciaux existent.",
    )
    add(
        "max-price-level",
        P,
        [1],
        [r"preisstufe|tariff level|niveau tarifaire", r"hoechst|highest|maxim"],
        "Die höchste reguläre Preisstufe ist Preisstufe 10; sie gilt für das gesamte RNN-Netz.",
        "The highest regular tariff level is level 10, covering the entire RNN network.",
        "Le niveau tarifaire ordinaire maximal est le niveau 10, pour tout le réseau RNN.",
    )
    add(
        "adult-single-1",
        P,
        [1],
        [
            r"einzelfahr|single ticket|billet simple",
            r"erwachsen|adult|adulte",
            r"preisstufe 1\b|level 1\b|niveau 1\b",
        ],
        "Laut der Preistafel ab 1. August 2026 kostet die Einzelfahrkarte für Erwachsene in Preisstufe 1 2,60 Euro.",
        "The price table effective 1 August 2026 lists an adult single ticket at tariff level 1 for 2.60 euros.",
        "Le tarif du 1er août 2026 indique 2,60 euros pour un billet simple adulte au niveau 1.",
        30,
    )
    add(
        "adult-single-network",
        P,
        [1],
        [
            r"einzelfahr|single ticket|billet simple",
            r"erwachsen|adult|adulte",
            r"gesamten|preisstufe 10|entire|tout le",
        ],
        "Die Einzelfahrkarte für Erwachsene im gesamten RNN-Netz, Preisstufe 10, kostet laut Preistafel ab 1. August 2026 17,40 Euro.",
        "An adult single ticket for the entire RNN network, tariff level 10, costs 17.40 euros in the price table effective 1 August 2026.",
        "Le billet simple adulte pour tout le réseau RNN, niveau 10, coûte 17,40 euros selon le tarif du 1er août 2026.",
        30,
    )
    add(
        "deutschland",
        B,
        [7],
        [r"deutschland.?ticket|d.ticket"],
        "Laut Broschüre ab 1. August 2026 kostet das Deutschland-Ticket 63 Euro pro Monat. Es gilt nur in der 2. Klasse; für die 1. Klasse im RNN-Gebiet ist ein Zuschlag für die entsprechende Verbindung erforderlich. Es können keine weiteren Personen mitgenommen werden; Kinder unter 6 Jahren fahren generell kostenlos.",
        "The brochure effective 1 August 2026 lists the Deutschland-Ticket at 63 euros per month. It is valid in second class; first-class travel within RNN requires a supplement for the connection. No additional people may travel on it; children under 6 travel free.",
        "La brochure applicable dès le 1er août 2026 indique 63 euros par mois pour le Deutschland-Ticket. Il est valable en deuxième classe ; la première classe dans le RNN exige un supplément. Aucune personne supplémentaire n'est incluse ; les enfants de moins de 6 ans voyagent gratuitement.",
    )
    add(
        "bicycle",
        B,
        [13],
        [r"fahrrad|bicycle|bike|velo"],
        "Die Fahrradmitnahme im RNN-Tarif ist montags bis freitags zwischen 6 und 9 Uhr kostenpflichtig: Einzelfahrkarte Fahrrad für die Verbindung oder Monatskarte Fahrrad kaufen. Vor 6 Uhr und nach 9 Uhr sowie samstags, sonntags und feiertags ganztägig ist sie zu RNN-Fahrkarten kostenlos.",
        "With RNN tickets, bicycle transport is chargeable Monday to Friday between 6 and 9 a.m.; buy a bicycle single or monthly ticket. It is free before 6 and after 9 a.m., and all day on Saturdays, Sundays and public holidays.",
        "Avec un billet RNN, le vélo est payant du lundi au vendredi entre 6 h et 9 h : acheter un billet vélo simple ou mensuel. Il est gratuit avant 6 h et après 9 h, ainsi que les samedis, dimanches et jours fériés.",
    )
    add(
        "rheinland",
        B,
        [6],
        [r"rheinland.pfalz.ticket"],
        "Das Rheinland-Pfalz-Ticket kostet 30 Euro für eine Person und 10 Euro je weitere Person: drei Personen zahlen 50 Euro, maximal fünf Personen 70 Euro. Es gilt werktags ab 9 Uhr bis 3 Uhr des Folgetags, an Wochenenden und gesetzlichen Feiertagen ganztägig.",
        "The Rheinland-Pfalz-Ticket costs 30 euros for one person plus 10 euros per additional person: 50 euros for three, up to five for 70 euros. Valid from 9 a.m. to 3 a.m. the next day, and all day on weekends and public holidays.",
        "Le Rheinland-Pfalz-Ticket coûte 30 euros pour une personne puis 10 euros par personne supplémentaire : 50 euros pour trois, jusqu'à cinq pour 70 euros. Valable de 9 h à 3 h le lendemain, toute la journée les week-ends et jours fériés.",
    )
    add(
        "day-tickets",
        B,
        [5],
        [r"tageskarte|day ticket|billet journalier|kindergartengruppe"],
        "Die Single-Tageskarte gilt für eine Person, die Gruppen-Tageskarte für bis zu 5 Personen. Sie gelten ab Betriebsbeginn bis 4 Uhr des Folgetags. Als nachgewiesene Kindergartengruppe dürfen bis zu 15 Personen mitfahren, davon bis zu 5 erwachsene Betreuer; erforderlich ist eine formlose Bestätigung mit Ausflugsdatum, Kindergartenanschrift und Unterschrift der Leitung.",
        "A single day ticket covers one person and a group day ticket up to five. Both are valid from the start of service until 4 a.m. the next day. A documented kindergarten group may include up to 15 people, including up to five adult carers, with written confirmation of the date, kindergarten address and manager's signature.",
        "Le billet journalier individuel couvre une personne, celui de groupe jusqu'à cinq. Validité jusqu'à 4 h le lendemain. Un groupe de maternelle peut compter jusqu'à 15 personnes, dont cinq adultes accompagnateurs au maximum, avec attestation datée, adresse de l'établissement et signature de la direction.",
    )
    add(
        "group-registration",
        B,
        [5],
        [r"gruppenausflug|group outing|sortie de groupe"],
        "Den Gruppenausflug mindestens eine Woche vorher bei den jeweiligen Verkehrsunternehmen anmelden.",
        "Register the group outing with the relevant transport companies at least one week in advance.",
        "Déclarer la sortie de groupe aux entreprises de transport concernées au moins une semaine à l'avance.",
        30,
    )
    add(
        "multiple-ticket",
        B,
        [4],
        [r"mehrfahrtenkarte|multi.journey|carnet"],
        "Beim Kauf der Mehrfahrtenkarte wird die erste Fahrkarte sofort automatisch entwertet. Die Karte enthält fünf Fahrkarten derselben Preisstufe, bis zu 10 Prozent günstiger als fünf entsprechende Einzelfahrkarten. Pro Kunde und Fahrt ist eine Fahrkarte zu entwerten.",
        "The first ticket is automatically validated immediately on buying the five-journey ticket. It contains five tickets of the same tariff level at up to 10 percent less than five singles. Validate one ticket per person and trip.",
        "Le premier billet est automatiquement validé dès l'achat du carnet de cinq trajets. Les cinq billets du même niveau tarifaire coûtent jusqu'à 10 % de moins que cinq billets simples. Valider un billet par personne et trajet.",
    )
    add(
        "season-zones",
        B,
        [9],
        [
            r"zeitkarte|season ticket|abonnement",
            r"wabe|august|2026|zone|gebiet|network|reseau",
        ],
        "Alle Zeitkarten gelten ab 1.8.2026 im gesamten RNN-Verbundgebiet, unabhängig von einzelnen Strecken oder Tarifzonen.",
        "From 1 August 2026 all season tickets cover the entire RNN network, independently of individual routes or fare zones.",
        "Depuis le 1er août 2026, tous les abonnements couvrent l'ensemble du réseau RNN, indépendamment des lignes ou zones tarifaires.",
    )
    add(
        "nine-clock",
        B,
        [10],
        [r"9.uhr|9 uhr|nine.o.clock"],
        "Die 9-Uhr-Zeitkarte gilt montags bis freitags ab 9 Uhr; am Wochenende darfst du schon vor 9 Uhr fahren. Sie gilt im gesamten Verbundgebiet.",
        "The 9 a.m. season ticket is valid from 9 a.m. Monday to Friday; on weekends you may travel before 9 a.m. It covers the entire network.",
        "L'abonnement 9 h est valable dès 9 h du lundi au vendredi et avant 9 h le week-end, dans tout le réseau.",
        30,
    )
    add(
        "forgotten-annual",
        B,
        [9],
        [r"jahreskarte|annual ticket|abonnement annuel", r"vergess|forgot|oubli"],
        "Wenn du die persönliche Jahreskarte Jedermann vergessen hast, zahlst du bei einer Kontrolle laut Broschüre nur 7 statt 60 Euro. Das gilt für die persönliche Jahreskarte Jedermann.",
        "If you forget your personal Jedermann annual ticket, the brochure states that an inspection costs 7 rather than 60 euros. This rule is specific to that personal annual ticket.",
        "En cas d'oubli de la carte annuelle personnelle Jedermann, la brochure prévoit 7 euros au lieu de 60 lors du contrôle. Cette règle concerne cette carte personnelle.",
        30,
    )
    add(
        "kombi",
        B,
        [14],
        [r"kombiticket|kombi.ticket"],
        "Beim RNN-KombiTicket ist die entsprechend gekennzeichnete Eintrittskarte zugleich Fahrkarte für Hin- und Rückfahrt zur Partnerveranstaltung. Die Gültigkeit endet spätestens um 4 Uhr des Folgetages. Auf Linien der Mainzer Mobilität und ESWE gilt sie jeweils drei Stunden vor beziehungsweise nach der Veranstaltung.",
        "An event admission ticket marked RNN-KombiTicket also covers travel to and from the partner event, until 4 a.m. the next day at the latest. On Mainzer Mobilität and ESWE services it is valid three hours before and after the event.",
        "Le billet d'entrée portant la mention RNN-KombiTicket couvre aussi l'aller-retour vers l'événement partenaire, au plus tard jusqu'à 4 h le lendemain. Chez Mainzer Mobilität et ESWE, il est valable trois heures avant et après l'événement.",
    )
    add(
        "network-validity",
        N,
        [1],
        [r"netzplan|network map|plan du reseau", r"wann|gueltig|2025|valid|vigueur"],
        "Der RNN-Gesamtnetzplan 2025 ist gültig ab 15.12.2024. Er enthält keine Echtzeitdaten.",
        "The RNN 2025 network map is valid from 15.12.2024. It does not contain real-time information.",
        "Le plan du réseau RNN 2025 est valable depuis le 15.12.2024. Il ne contient pas de données en temps réel.",
    )
    add(
        "bingen",
        W,
        [1],
        [r"\bbingen\b", r"preisstufe|wabe|tariff|tarif"],
        "Für Fahrkarten innerhalb Bingen gilt laut Wabenplan Preisstufe 31.",
        "The fare-zone map specifies tariff level 31 for tickets within Bingen.",
        "Le plan des zones indique le niveau tarifaire 31 pour les billets à l'intérieur de Bingen.",
        30,
    )
    add(
        "timetable-notes",
        F,
        [1],
        [r"linie 216|fahrplan.*216|route 216|ligne 216|\bfahrt 125\b"],
        "Linie 216 verbindet Bad Kreuznach Bahnhof, Michelin, Planig Industriegebiet und Bosenheim Sportplatz/Ippesheim sowie die Gegenrichtung. Fahrt 125 fährt montags bis freitags um 5:32 Uhr am Bad Kreuznacher Bahnhof ab und ist um 5:39 Uhr bei Michelin. S bedeutet nur an Schultagen in Rheinland-Pfalz. Am 24. und 31. Dezember gilt Verkehr wie an Samstagen; an Rosenmontag, Fastnachtsdienstag und den Freitagen nach Christi Himmelfahrt und Fronleichnam wie in den Ferien.",
        "Route 216 connects Bad Kreuznach station, Michelin, Planig industrial estate and Bosenheim/Ippesheim, in both directions. Trip 125 leaves the station at 5:32 and reaches Michelin at 5:39 Monday to Friday. S means school days in Rhineland-Palatinate only. On 24 and 31 December Saturday service applies; the specified carnival and bridge days follow school-holiday service.",
        "La ligne 216 relie la gare de Bad Kreuznach, Michelin, Planig et Bosenheim/Ippesheim dans les deux sens. Le trajet 125 part à 5 h 32 et arrive chez Michelin à 5 h 39 du lundi au vendredi. S signifie uniquement les jours scolaires en Rhénanie-Palatinat. Les 24 et 31 décembre, service du samedi ; les jours particuliers indiqués suivent le service des vacances.",
        1,
    )
    timetable = json.loads(
        (ROOT / "data/reviewed-ocr" / F.replace(".pdf", ".json")).read_text(
            encoding="utf-8"
        )
    )
    for trip in timetable["pages"]["1"].get("trips", []):
        stops = "; ".join(f"{stop['stop']}: {stop['time']}" for stop in trip["stops"])
        add(
            f"trip-{trip['trip']}",
            F,
            [1],
            [rf"\b(?:fahrt|trip|trajet)\s*{trip['trip']}\b"],
            f"Linie 216, Fahrt {trip['trip']}, {trip['direction']}, montags bis freitags"
            + (", nur an Schultagen in Rheinland-Pfalz" if trip["school_only"] else "")
            + f": {stops}. Es gelten die im Fahrplan genannten Feiertags- und Ferienausnahmen.",
            f"Route 216, trip {trip['trip']}, Monday to Friday"
            + (
                ", school days in Rhineland-Palatinate only"
                if trip["school_only"]
                else ""
            )
            + f": {stops}. The timetable's stated holiday exceptions apply.",
            f"Ligne 216, trajet {trip['trip']}, du lundi au vendredi"
            + (
                ", uniquement les jours scolaires en Rhénanie-Palatinat"
                if trip["school_only"]
                else ""
            )
            + f" : {stops}. Les exceptions de jours fériés et vacances indiquées s'appliquent.",
            50,
        )

    # Preserve column meaning, including the merged extraction row for 23 and 1.
    tables = json.loads(
        (ROOT / "data/aufbereitet/tables/DOC-20260920-WA0004-p1.json").read_text(
            encoding="utf-8"
        )
    )["tables"]
    column_sets = [
        (
            0,
            [
                "Einzelfahrkarte Erwachsene",
                "Einzelfahrkarte Kinder",
                "Mehrfahrtenkarte Erwachsene (Preis pro Fahrkarte, Verkauf von fünf)",
                "Mehrfahrtenkarte Kinder (Preis pro Fahrkarte, Verkauf von fünf)",
                "Single-Tageskarte",
                "Gruppen-Tageskarte bis 5 Personen",
            ],
            [
                "adult single",
                "child single",
                "adult multi-journey (per ticket, sold in fives)",
                "child multi-journey (per ticket, sold in fives)",
                "single day ticket",
                "group day ticket up to five people",
            ],
            [
                "billet simple adulte",
                "billet simple enfant",
                "carnet adulte (prix par billet, vendu par cinq)",
                "carnet enfant (prix par billet, vendu par cinq)",
                "billet journalier individuel",
                "billet journalier de groupe jusqu'à cinq personnes",
            ],
            r"einzelfahr|mehrfahr|tageskarte|single ticket|day ticket|billet|carnet",
        ),
        (
            3,
            [
                "Einzelzuschlag 1. Klasse",
                "Wochenzuschlag 1. Klasse",
                "Monatszuschlag 1. Klasse",
                "Jahreszuschlag bar 1. Klasse",
                "Jahreszuschlag im Abo 1. Klasse",
            ],
            [
                "first-class single supplement",
                "first-class weekly supplement",
                "first-class monthly supplement",
                "first-class annual supplement paid upfront",
                "first-class annual subscription supplement",
            ],
            [
                "supplément première classe simple",
                "supplément première classe hebdomadaire",
                "supplément première classe mensuel",
                "supplément première classe annuel payé comptant",
                "supplément première classe abonnement annuel",
            ],
            r"zuschlag|supplement",
        ),
    ]
    for table_index, de_columns, en_columns, fr_columns, topic in column_sets:
        for line in tables[table_index].splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != len(de_columns) + 1 or not re.match(r"^\d", cells[0]):
                continue
            if cells[0] == "23* 1":
                rows = [
                    [label, *[c.split()[i] for c in cells[1:]]]
                    for i, label in enumerate(["23*", "1"])
                ]
            else:
                rows = [cells]
            for row in rows:
                level = re.match(r"\d+", row[0]).group(0)
                texts = [
                    "; ".join(
                        f"{label}: {amount} Euro"
                        for label, amount in zip(columns, row[1:], strict=True)
                    )
                    for columns in [de_columns, en_columns, fr_columns]
                ]
                add(
                    f"price-table-{table_index}-{level}",
                    P,
                    [1],
                    [
                        rf"(?:preisstufe|tariff level|niveau(?: tarifaire)?)\s*{level}\b",
                        topic,
                    ],
                    f"Preisstufe {level}, laut Preistafel ab 1. August 2026: {texts[0]}.",
                    f"Tariff level {level}, price table effective 1 August 2026: {texts[1]}.",
                    f"Niveau tarifaire {level}, tableau applicable dès le 1er août 2026 : {texts[2]}.",
                    35,
                )
    dest = ROOT / "data/index/answer_facts.json"
    dest.write_text(
        json.dumps(
            {"reviewed_at": "2026-09-25", "facts": cards}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(f"Prepared {len(cards)} source-bound answer facts")


if __name__ == "__main__":
    main()
