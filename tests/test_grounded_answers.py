"""Final answers must contain the fact and cite the evidence actually selected."""

import pytest
from krn_catalog_cases import CATALOG_CASES

from krn_docs import fold_text, search_krn_index, short_krn_voice_answer


@pytest.mark.parametrize(
    "case",
    [c for c in CATALOG_CASES if not c["refusal"] and not c["id"].startswith("M")],
    ids=lambda c: c["id"],
)
def test_catalog_final_answer(case):
    packed = search_krn_index(case["query"])
    answer = short_krn_voice_answer(case["query"], packed)
    assert all(t in fold_text(answer) for t in case["must_contain"]), (
        case["id"],
        answer,
    )
    assert any(
        f"{name}, Seite {page}" in answer
        for name in case["filenames"]
        for page in case["pages"]
    ), answer
    assert "KRN_EVIDENCE" not in answer


@pytest.mark.parametrize(
    "query,expected",
    [
        ("What should I do if the card reader is broken?", ["cash", "control centre"]),
        (
            "Que faire si le paiement par carte est impossible ?",
            ["espèces", "régulation"],
        ),
        ("How is a 20-minute vehicle delay compensated?", ["minute", "working time"]),
        ("Comment un retard du véhicule est-il rémunéré ?", ["minute", "travail"]),
        (
            "What happens when a pupil has no ticket on the way to school?",
            ["school", "name", "quality"],
        ),
    ],
)
def test_multilingual_final_answers(query, expected):
    answer = short_krn_voice_answer(query, search_krn_index(query))
    assert all(word in answer for word in expected), answer
    assert ".pdf, page " in answer


@pytest.mark.parametrize(
    "query",
    [
        "Welche arbeitsrechtlichen Ansprüche habe ich außerhalb dieser Betriebsvereinbarungen?",
        "Welche KRN Regelung gibt es zum Homeoffice?",
        "Wie hoch ist der KRN Zuschuss für eine Marsreise?",
    ],
)
def test_unsupported_policy_is_not_answered_by_nearby_fact(query):
    answer = short_krn_voice_answer(query, search_krn_index(query))
    assert "nicht" in answer or "keine" in answer
    assert "Euro" not in answer


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Wann fährt Fahrt 128 bei Michelin und am Bahnhof?", ["22:19", "22:27"]),
        ("Wann fährt Fahrt 104 ab Ippesheim?", ["7:21", "Schultagen"]),
        ("Was kostet eine Einzelfahrkarte Kinder in Preisstufe 5?", ["Kinder: 5,55"]),
        ("Was kostet der Einzelzuschlag in Preisstufe 23?", ["3,90"]),
        ("Was kostet der Einzelzuschlag in Preisstufe 1?", ["1,80"]),
    ],
)
def test_structured_values_keep_row_and_column(query, expected):
    answer = short_krn_voice_answer(query, search_krn_index(query))
    assert all(word in answer for word in expected), answer


def test_french_map_question_routes_locally():
    from krn_docs import is_krn_internal_question

    query = "Quel niveau tarifaire s'applique aux billets à l'intérieur de Bingen selon le plan des zones ?"
    assert is_krn_internal_question(query)
    answer = short_krn_voice_answer(query, search_krn_index(query))
    assert "31" in answer and "page 1" in answer
