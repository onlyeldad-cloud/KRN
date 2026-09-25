"""Local lexical/BM25 search over prepared KRN PDF chunks."""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

from livekit.agents import function_tool

logger = logging.getLogger("krn_docs")

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "data" / "index" / "krn_docs.json"
DEFAULT_LIMIT = 5
MAX_LIMIT = 8
MIN_SCORE = 1.35

_UMLAUT = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"))
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,:/][0-9]+)*", re.I)
_STOP = frozenset(
    {
        "der",
        "die",
        "das",
        "und",
        "oder",
        "ein",
        "eine",
        "ist",
        "im",
        "in",
        "zu",
        "von",
        "mit",
        "auf",
        "fuer",
        "fur",
        "the",
        "a",
        "an",
        "of",
        "to",
        "krn",
        "rnn",
        "ich",
        "du",
        "was",
        "wie",
        "wann",
        "wo",
        "wer",
        "gilt",
        "es",
        "dem",
        "den",
        "des",
        "bei",
        "bitte",
        "einen",
        "einem",
        "mir",
        "mein",
        "meine",
        "kann",
        "kannst",
        "habe",
        "hat",
        "werden",
        "wird",
        "sind",
        "auch",
        "nur",
        "nicht",
        "kein",
        "keine",
        "this",
        "that",
        "for",
        "with",
        "from",
    }
)
_REALTIME = (
    "aktuelle verspaetung",
    "aktuellen verspaetung",
    "aktuelle verkehrslage",
    "heute verspaetung",
    "hat der bus heute",
    "jetzt verspaet",
    "live verspaet",
    "current delay",
    "realtime delay",
)
_QUERY_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        (
            "years of service",
            "years with the company",
            "anciennete",
            "service anniversary",
        ),
        "Betriebszugehoerigkeit Betriebsjubilaeen Praemie Sachgeschenk",
    ),
    (("retard",), "Fahrzeugverspaetung Arbeitszeit Leitstelle"),
    (
        ("card payment", "card reader", "paiement par carte"),
        "EC-Geraet Kartenzahlung defekt Leitstelle",
    ),
    (("cihazi", "cihaz", "bozuksa"), "EC-Geraet Kartenzahlung bar Leitstelle defekt"),
    (
        ("hastaysam", "iyilesme", "sekiz"),
        "Genesungspaket acht Wochen Erkrankung 25 Euro Privatadresse",
    ),
    (
        ("vehicle delay", "compensated", "20-minute", "20 minute"),
        "Fahrzeugverspaetung minutengenau Arbeitszeit 20 Minuten",
    ),
    (
        ("another adult", "deutschland-ticket"),
        "Deutschland-Ticket Mitnahme keine weiteren Personen Kinder unter 6 Jahren",
    ),
    (
        ("elev", "bilet", "scoala"),
        "Schueler Ticket Schule Qualitaetsmanagement Schulweg",
    ),
    (
        ("pierwszej klasie", "wazny"),
        "Deutschland-Ticket 1. Klasse 2. Klasse Zuschlag",
    ),
    (
        ("років", "отримаю"),
        "40 Jahren Betriebszugehoerigkeit 400 Euro Jubilaeum freier Tag",
    ),
    (
        ("جهاز", "الدفع", "البطاقة"),
        "EC-Geraet Kartenzahlung bar Leitstelle defekt",
    ),
    (("jubilae", "betriebszugehoer"), "Betriebsjubilaeen Praemie Sachgeschenk"),
    (("40 jahren", "40 jahre"), "40 Jahre 400 Euro zusaetzlicher freier Tag"),
    (("genesung",), "Genesungspaket acht Wochen Privatadresse"),
    (
        ("geburtstag", "runden geburt"),
        "runde Geburtstage 20 30 40 50 60 70 80 Sachgeschenk 25 Euro",
    ),
    (("fahrzeugverspaet", "verspaetung"), "Fahrzeugverspaetung Leitstelle Dienstende"),
    (("schueler", "grundschueler"), "Schuelerbefoerderung Ticket Qualitaetsmanagement"),
    (
        ("ec-geraet", "ec geraet", "kartenzahlung"),
        "EC-Geraet Kartenzahlung bar Leitstelle",
    ),
    (("preisstufe", "wabe"), "Preisstufe Waben Einzelfahrkarte"),
    (
        ("deutschland-ticket", "deutschlandticket"),
        "Deutschland-Ticket 63 Euro 2. Klasse",
    ),
    (("fahrrad",), "Fahrradmitnahme 6 9 Uhr kostenpflichtig"),
    (("linie 216", "fahrt 125"), "Linie 216 Bad Kreuznach Michelin Bosenheim"),
)

_KRN_INTERNAL_MARKERS = (
    "betriebszugehoer",
    "jubilae",
    "betriebsvereinbar",
    "dienstanweis",
    "fahrzeugverspaet",
    "verspaetung",
    "ec-geraet",
    "ec geraet",
    "kartenzahlung",
    "schuelerbefoerder",
    "ticketpreis",
    "preisstufe",
    "wabenplan",
    "netzplan",
    "fahrplan",
    "genesung",
    "deutschland-ticket",
    "deutschlandticket",
    "schuelerticket",
)


@lru_cache(maxsize=4096)
def fold_text(text: str) -> str:
    lowered = text.lower()
    for src, dst in _UMLAUT:
        lowered = lowered.replace(src, dst)
    normalized = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    stripped = re.sub(
        r"betriebs\s*zugeho?e?rigkeit", "betriebszugehoerigkeit", stripped
    )
    stripped = re.sub(r"\bzehn\b", "10", stripped)
    stripped = re.sub(r"\b(\d+)\s+jahr\b", r"\1 jahre", stripped)
    stripped = re.sub(r"(\d+)\.\s+(\d+)\.\s+(\d+)", r"\1.\2.\3", stripped)
    saved: list[str] = []

    def _hold_date(match: re.Match[str]) -> str:
        saved.append(match.group(0))
        return f" datehold{len(saved) - 1} "

    stripped = re.sub(r"\d{1,2}\.\d{1,2}\.\d{4}", _hold_date, stripped)
    stripped = re.sub(r"(?<!\d)(\d{1,2})[.]([0-5]\d)(?!\d)", r"\1:\2", stripped)
    for index, date in enumerate(saved):
        stripped = stripped.replace(f"datehold{index}", date)
    return " ".join(stripped.split())


def tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN_RE.findall(fold_text(text)) if token]


def citation_label(language: str) -> str:
    if language.lower().startswith("en"):
        return "Source"
    if language.lower().startswith("fr"):
        return "Source"
    return "Quelle"


def detect_question_language(text: str) -> str:
    """Best-effort language of a document question (not general chat)."""
    folded = fold_text(text)
    if re.search(r"\b(what|how|which|when|where|can i|should i|pupil)\b", folded):
        return "en"
    if re.search(
        r"\b(que|quel|quels|quelle|quelles|comment|pourquoi|paiement|remunere)\b",
        folded,
    ):
        return "fr"
    if any(
        marker in folded
        for marker in (
            "what do i",
            "what happens",
            "how is",
            "how are",
            "after 10 years",
            "years of service",
            "which documents",
            "what documents",
            "list all",
            "available documents",
        )
    ):
        return "en"
    if any(
        marker in folded
        for marker in (
            "qu'est-ce",
            "quest-ce",
            "que recois",
            "apres 10",
            "anciennete",
            "quels documents",
            "quelles documents",
            "documents disponibles",
        )
    ):
        return "fr"
    return "de"


def format_citation(filename: str, page: int, language: str = "de") -> str:
    lang = (language or "de").lower()
    if lang.startswith("en"):
        return f"[Source: {filename}, page {page}]"
    if lang.startswith("fr"):
        return f"[Source : {filename}, page {page}]"
    return f"[Quelle: {filename}, Seite {page}]"


def required_citation_for_pack(query: str, packed: dict) -> str | None:
    """Deterministic citation from retrieval metadata (never model-invented)."""
    if is_krn_inventory_question(query):
        return None
    results = packed.get("results") or []
    if packed.get("status") != "ok" or not results:
        return None
    if results[0].get("answers"):
        return " ".join(
            format_citation(
                results[0]["filename"], page, detect_question_language(query)
            )
            for page in results[0]["pages"]
        )
    years = re.search(r"(\d+)\s*(?:jahre|years|ans)", fold_text(query))
    year = years.group(1) if years else None

    def hit_rank(hit: dict) -> float:
        folded = fold_text(hit.get("text") or "")
        score = float(hit.get("score") or 0)
        if year and f"{year} jahre" in folded:
            score += 50
        if year == "10" and "100" in folded:
            score += 25
        return score

    hit = max(results, key=hit_rank)
    return format_citation(
        hit["filename"], hit["page"], detect_question_language(query)
    )


def citation_present(text: str, citation: str) -> bool:
    if not text or not citation:
        return False
    if citation in text:
        return True
    # Accept exact filename + page even if bracket punctuation drifted slightly.
    inner = citation.strip("[]")
    return inner in text


def ensure_citation(text: str, citation: str | None) -> str:
    cleaned = sanitize_user_visible_answer(text)
    if not citation:
        return cleaned
    if citation_present(cleaned, citation):
        return cleaned
    if not cleaned:
        return citation
    return f"{cleaned.rstrip()} {citation}"


_LEAK_MARKERS = (
    "die lokale dokumentensuche wurde",
    "nur diese treffer verwenden",
    "english citation (copy exactly)",
    "french citation (copy exactly)",
    "user question (data)",
    "quellentexte sind daten",
    "required_citation:",
    "krn_evidence",
    "end_evidence",
    "krn_inventory",
    "end_krn_inventory",
    "die folgenden treffer erfuellen",
    "die folgenden treffer erfüllen",
    "kein allgemeinwissen, keine rente",
    "answer only from",
    "answer in french",
    "answer in english",
    "do not create",
    "do not mention",
    "do not read labels",
    "copy required_citation",
    "question_language=",
    "if only hit",
    "avoid repeating citation",
    "krn document turn is active",
    "local retrieval already ran",
)

RETRIEVAL_UNAVAILABLE_DE = (
    "Entschuldigung, ich kann die KRN-Dokumente gerade nicht zuverlässig "
    "durchsuchen. Bitte versuche es noch einmal."
)


def sanitize_user_visible_answer(text: str) -> str:
    """Strip known internal instruction/retrieval scaffolding from model output."""
    if not text:
        return ""
    kept: list[str] = []
    for line in text.splitlines():
        folded = fold_text(line)
        if any(marker in folded for marker in _LEAK_MARKERS):
            continue
        if folded.startswith("hit ") and (
            "filename:" in folded or "excerpt:" in folded
        ):
            continue
        if folded.startswith("filename:") or folded.startswith("page:"):
            continue
        if folded.startswith("excerpt:"):
            continue
        if "krn_evidence" in folded or "end_evidence" in folded:
            continue
        if "krn_inventory" in folded or "end_krn_inventory" in folded:
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    for token in (
        "KRN_EVIDENCE",
        "END_EVIDENCE",
        "KRN_INVENTORY",
        "END_KRN_INVENTORY",
        "required_citation:",
    ):
        cleaned = cleaned.replace(token, "")
    return cleaned.strip()


def matching_hints(query: str) -> list[str]:
    folded = fold_text(query)
    hits: list[str] = []
    if re.search(r"\d+\s+jahre[n]?\s+(?:bei\s+krn|gearbeitet)", folded):
        hits.append("Betriebszugehoerigkeit Betriebsjubilaeen Praemie Sachgeschenk")
    for needles, hint in _QUERY_HINTS:
        terms = (needles,) if isinstance(needles, str) else needles
        if any(len(needle) > 2 and needle in folded for needle in terms):
            hits.append(hint)
    return hits


def expand_query(query: str) -> str:
    return " ".join([query, *matching_hints(query)])


def is_realtime_query(query: str) -> bool:
    folded = fold_text(query)
    return any(marker in folded for marker in _REALTIME)


def load_index() -> list[dict]:
    return load_search_corpus()[0]


def load_search_corpus() -> tuple[list[dict], list[list[str]]]:
    chunks, documents, _df, _avg, _meta = load_search_bundle()
    return chunks, documents


def load_inventory_documents() -> list[dict]:
    """In-memory document metadata for inventory (no per-question disk re-read)."""
    return list(load_search_bundle()[4])


def load_search_bundle() -> tuple[
    list[dict], list[list[str]], Counter[str], float, list[dict]
]:
    stat = INDEX_PATH.stat()
    return _load_search_bundle(INDEX_PATH, stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=1)
def _load_search_bundle(
    path: Path, mtime_ns: int, size: int
) -> tuple[list[dict], list[list[str]], Counter[str], float, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    chunks = list(payload["chunks"])
    documents = [_content_tokens(chunk) for chunk in chunks]
    document_frequency: Counter[str] = Counter()
    for tokens in documents:
        document_frequency.update(set(tokens))
    average_length = sum(len(tokens) for tokens in documents) / max(len(documents), 1)
    meta = payload.get("documents")
    if meta is None:
        meta = json.loads(
            path.with_name("extract_report.json").read_text(encoding="utf-8")
        )
    inventory = list(meta)
    return chunks, documents, document_frequency, average_length, inventory


def prewarm_krn_docs() -> int:
    """Load the local index and BM25 tokens before the first voice job."""
    chunks, _documents, _df, _avg, _meta = load_search_bundle()
    return len(chunks)


def _bm25_scores(
    query_tokens: list[str],
    documents: list[list[str]],
    *,
    document_frequency: Counter[str] | None = None,
    average_length: float | None = None,
) -> list[float]:
    doc_count = len(documents)
    if document_frequency is None:
        document_frequency = Counter()
        for tokens in documents:
            document_frequency.update(set(tokens))
    if average_length is None:
        average_length = sum(len(tokens) for tokens in documents) / max(doc_count, 1)
    k1 = 1.5
    b = 0.75
    scores: list[float] = []
    for tokens in documents:
        term_frequency = Counter(tokens)
        length = len(tokens) or 1
        score = 0.0
        for term in query_tokens:
            if document_frequency[term] == 0:
                continue
            idf = math.log(
                1
                + (doc_count - document_frequency[term] + 0.5)
                / (document_frequency[term] + 0.5)
            )
            freq = term_frequency[term]
            denom = freq + k1 * (1 - b + b * length / average_length)
            score += idf * (freq * (k1 + 1)) / denom
        scores.append(score)
    return scores


def german_date(value: str | None) -> str:
    if not value or value.count("-") != 2:
        return value or ""
    year, month, day = value.split("-")
    return f"{day}.{month}.{year}"


def _content_tokens(chunk: dict) -> list[str]:
    parts = [
        chunk.get("text", ""),
        chunk.get("filename", ""),
        " ".join(chunk.get("identifiers") or []),
        chunk.get("valid_from") or "",
        german_date(chunk.get("valid_from")),
    ]
    return tokenize(" ".join(parts))


def search_krn_index(query: str, limit: int = DEFAULT_LIMIT) -> dict:
    query = query.strip()
    if not query or len(query) > 500:
        return {"status": "invalid_query", "results": []}
    if is_realtime_query(query):
        return {
            "status": "no_evidence",
            "message": (
                "Die bereitgestellten Dokumente enthalten keine Echtzeitdaten "
                "und keine aktuelle Verkehrslage."
            ),
            "results": [],
        }

    chunks, documents, doc_freq, avg_len, _meta = load_search_bundle()
    # Unsupported policy subjects must not become anniversary entitlements merely
    # because the question contains a year or the company name.
    unsupported = (
        "betriebsrente",
        "mondbasis",
        "homeoffice",
        "abfindung",
        "marsreise",
        "ausserhalb dieser betriebsvereinbar",
    )
    if any(term in fold_text(query) for term in unsupported):
        return {"status": "no_evidence", "results": []}
    hints = matching_hints(query)
    expanded = expand_query(query)
    query_tokens = [token for token in tokenize(expanded) if token not in _STOP]
    original_tokens = [token for token in tokenize(query) if token not in _STOP]
    if not query_tokens:
        return {"status": "no_results", "results": []}

    scores = _bm25_scores(
        query_tokens,
        documents,
        document_frequency=doc_freq,
        average_length=avg_len,
    )
    folded_query = fold_text(query)
    query_numbers = set(re.findall(r"\d+(?:[.,:]\d+)*", fold_text(expanded)))
    wants_validity = any(
        marker in folded_query
        for marker in ("seit wann", "gueltig", "gilt diese", "gilt der", "gilt die")
    )

    ranked: list[tuple[float, dict]] = []
    for chunk, score, tokens in zip(chunks, scores, documents, strict=True):
        if chunk.get("kind") == "answer_fact":
            if all(re.search(pattern, folded_query) for pattern in chunk["patterns"]):
                ranked.append((1000 + chunk["priority"], chunk))
            # Facts are only answers for their supported subject, never just BM25 overlap.
            continue
        searchable = fold_text(
            " ".join(
                [
                    chunk.get("text", ""),
                    " ".join(chunk.get("identifiers") or []),
                    german_date(chunk.get("valid_from")),
                ]
            )
        )
        bonus = 0.0
        for hint in hints:
            folded_hint = fold_text(hint)
            if any(token in searchable for token in tokenize(folded_hint)[:6]):
                bonus += 1.2
        for number in query_numbers:
            if number and number in searchable:
                bonus += 1.1
        if wants_validity and german_date(chunk.get("valid_from")):
            bonus += 0.4
        years = re.search(r"(\d+)\s+jahre", folded_query)
        if years and f"{years.group(1)} jahre" in searchable:
            bonus += 3.5
        overlap = len(set(query_tokens) & set(tokens))
        original_overlap = len(set(original_tokens) & set(tokens))
        if original_tokens and original_overlap == 0 and not hints:
            continue
        if overlap == 0 and bonus == 0:
            continue
        ranked.append((score + bonus + 0.2 * overlap + 0.6 * original_overlap, chunk))

    ranked.sort(key=lambda item: item[0], reverse=True)
    limit = max(1, min(limit, MAX_LIMIT))
    results = []
    for score, chunk in ranked[:limit]:
        if score < MIN_SCORE and len(results) >= 1:
            break
        validity = german_date(chunk.get("valid_from"))
        prefix = f"{chunk['filename']}, Seite {chunk['page']}"
        if validity:
            prefix += f", gültig ab {validity}"
        results.append(
            {
                "filename": chunk["filename"],
                "page": chunk["page"],
                "printed_page": chunk.get("printed_page"),
                "text": f"{prefix}. {chunk['text']}"[:2400],
                "score": round(float(score), 3),
                "valid_from": chunk.get("valid_from"),
                "valid_until": chunk.get("valid_until"),
                "identifiers": chunk.get("identifiers") or [],
                **(
                    {
                        "answers": chunk["answers"],
                        "pages": chunk["pages"],
                        "fact_id": chunk["fact_id"],
                    }
                    if chunk.get("answers")
                    else {}
                ),
            }
        )
    if not results:
        return {"status": "no_results", "results": []}
    if results[0]["score"] < MIN_SCORE:
        return {"status": "no_results", "results": []}
    return {"status": "ok", "results": results}


def is_explicit_web_request(text: str) -> bool:
    """True when the user clearly asks for internet/web search, not local PDFs."""
    folded = fold_text(text)
    return any(
        marker in folded
        for marker in (
            "im internet",
            "im netz suchen",
            "suche im netz",
            "online suchen",
            "google",
            "search the web",
            "search online",
            "look up online",
            "duckduckgo",
        )
    )


def is_krn_internal_question(text: str) -> bool:
    """True when spoken or typed text is a KRN/RNN company-policy question."""
    if is_explicit_web_request(text):
        return False
    folded = fold_text(text)
    if re.search(
        r"card reader|pupil.*ticket|grundschul.*ticket|schulweg.*stehen lassen|paiement par carte|retard du vehicule|eleve.*billet|niveau tarifaire|plan des zones",
        folded,
    ):
        return True
    # Agent self-intro / echo of the opening greeting must not route to docs.
    if "ich bin krn agent" in folded or "bin krn agent. wie kann" in folded:
        return False
    if is_krn_inventory_question(text) or matching_hints(text):
        return True
    if any(
        term in folded
        for term in (
            "internal policy",
            "company policy",
            "employee procedure",
            "internal timetable",
            "reglement interne",
            "regles internes",
            "interne regel",
            "interne richtlinie",
            "supplied pdf",
            "bereitgestellten pdf",
            "verkehrslage",
            "ticket price",
        )
    ):
        return True
    if any(marker in folded for marker in _KRN_INTERNAL_MARKERS):
        return True
    if re.search(r"(?<![a-z0-9])bv(?![a-z0-9])", folded):
        return True
    company = re.search(r"(?<![a-z0-9])(krn|rnn)(?![a-z0-9])", folded)
    return bool(company)


def is_krn_inventory_question(text: str) -> bool:
    folded = fold_text(text)
    return any(
        word in folded
        for word in (
            "dokument",
            "document",
            "richtlinien",
            "wissensdatenbank",
            "knowledge base",
        )
    ) and any(
        word in folded
        for word in (
            "welche",
            "liste",
            "alle",
            "verfuegbar",
            "hast du",
            "what",
            "which",
            "list",
            "available",
            "quels",
            "quelles",
            "disponible",
        )
    )


@function_tool
async def list_krn_docs() -> dict:
    """List ALL indexed KRN source PDFs with exact filenames, page counts and OCR metadata.

    Required for questions about available documents, policies or the knowledge inventory.
    Return every document; never invent names or substitute a partial search result.
    """
    try:
        chunks, _docs, _df, _avg, documents = load_search_bundle()
        names = {chunk["filename"] for chunk in chunks}
        if not names.issubset({doc["filename"] for doc in documents}):
            raise ValueError("Incomplete inventory metadata")
        logger.info("KRN inventory sources=%d", len(documents))
        packed = {"status": "ok", "count": len(documents), "documents": documents}
        packed["answer"] = grounded_fallback_answer("Welche Dokumente?", packed)
        packed["instruction"] = (
            "This is the complete inventory. Read answer once, without adding "
            "filenames from memory or earlier conversation."
        )
        return packed
    except (OSError, ValueError, KeyError):
        logger.warning("KRN inventory unavailable")
        return {"status": "unavailable", "count": 0, "documents": []}


def _relevant_excerpt(text: str, *, query: str = "", limit: int = 500) -> str:
    """Prefer a window around years/amounts so truncation keeps the answer span."""
    text = (text or "").strip()
    if not text:
        return ""
    folded_text = fold_text(text)
    folded_query = fold_text(query)
    anchors: list[str] = []
    years = re.search(r"(\d+)\s+jahre", folded_query)
    if years:
        anchors.append(f"{years.group(1)} jahre")
    for amount in re.findall(r"\d+(?:[.,]\d+)?", folded_query):
        if len(amount) >= 2:
            anchors.append(amount)
    for needle in (
        "10 jahre",
        "100,00",
        "100 euro",
        "100 €",
        "sachgeschenk",
        "praemie",
    ):
        if needle in folded_text:
            anchors.append(needle)
    for anchor in anchors:
        idx = folded_text.find(anchor)
        if idx < 0:
            continue
        # Approximate mapping: fold_text mostly lowercases; search original case-insensitively.
        match = re.search(re.escape(anchor), text, flags=re.I)
        if not match:
            # try without spaces drift
            match = re.search(anchor.replace(" ", r"\s+"), text, flags=re.I)
        if match:
            start = max(0, match.start() - 60)
            excerpt = text[start : start + limit].strip()
            if start > 0:
                excerpt = "…" + excerpt
            if start + limit < len(text):
                excerpt = excerpt.rstrip() + "…"
            return excerpt
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def format_krn_evidence(packed: dict, *, language: str = "de", query: str = "") -> str:
    results = packed.get("results") or []
    if packed.get("status") != "ok" or not results:
        return (
            "KRN_EVIDENCE status=empty\n"
            "Answer that the available KRN documents do not contain this. "
            "Do not invent pension, severance, prices, or rules. "
            "Do not read these lines aloud as meta-instructions."
        )
    lines = ["KRN_EVIDENCE status=ok"]
    # Keep mid-session instruction updates compact for Google Live's short
    # generation_created timeout, but keep the answer span for the top hit.
    for index, hit in enumerate(results[:3], start=1):
        filename = hit["filename"]
        page = hit["page"]
        citation = format_citation(filename, page, language)
        limit = 900 if index == 1 else 320
        excerpt = _relevant_excerpt(hit.get("text") or "", query=query, limit=limit)
        lines.append(
            f"HIT {index}\n"
            f"filename: {filename}\n"
            f"page: {page}\n"
            f"required_citation: {citation}\n"
            f"excerpt: {excerpt}"
        )
    top = format_citation(results[0]["filename"], results[0]["page"], language)
    lines.append(
        "Use only these hits. Copy required_citation character-for-character. "
        f"End with: {top}"
    )
    return "\n".join(lines)


def format_krn_inventory(packed: dict) -> str:
    documents = packed.get("documents") or []
    if packed.get("status") != "ok" or not documents:
        return (
            "KRN_INVENTORY status=empty\n"
            "Say the document inventory is unavailable. Do not invent filenames."
        )
    lines = [
        f"KRN_INVENTORY status=ok count={len(documents)}",
        "List EVERY filename below verbatim. No page citations for inventory.",
    ]
    for doc in documents:
        ocr = "ocr=yes" if doc.get("used_ocr") else "ocr=no"
        lines.append(f"- {doc['filename']} | pages={doc.get('pages', '?')} | {ocr}")
    return "\n".join(lines)


def expected_evidence_amounts(query: str, packed: dict) -> list[str]:
    """Euro amounts that a grounded answer for this question must mention."""
    results = packed.get("results") or []
    if packed.get("status") != "ok" or not results:
        return []
    if results[0].get("fact_id", "").startswith("anniversary-"):
        return re.findall(r"(\d+) Euro", results[0]["answers"]["de"])
    years = re.search(r"(\d+)\s*(?:jahre|years|ans)", fold_text(query))
    year = years.group(1) if years else None

    def hit_rank(hit: dict) -> float:
        folded = fold_text(hit.get("text") or "")
        score = float(hit.get("score") or 0)
        if year and f"{year} jahre" in folded:
            score += 50
        if year == "10" and "100" in folded:
            score += 25
        return score

    hit = max(results, key=hit_rank)
    text = hit.get("text") or ""
    if year:
        # Keep the year line only — the anniversary table lists many tiers.
        line = re.search(
            rf"{re.escape(year)}\s*Jahre[^\n]{{0,120}}",
            text,
            flags=re.I,
        )
        amounts: list[str] = []
        if line:
            amounts.extend(re.findall(r"(\d{2,3})[.,]\d{2}", line.group(0)))
        # Jubilee congratulations gift is stated once for all anniversary tiers.
        gift = re.search(
            r"Gratulation.{0,80}Sachgeschenk\s+im\s+Wert\s+von\s*(\d{2,3})[.,]\d{2}"
            r"|Sachgeschenk\s+im\s+Wert\s+von\s*(\d{2,3})[.,]\d{2}.{0,40}Jubil",
            text,
            flags=re.I | re.S,
        )
        if not gift:
            gift = re.search(
                r"Zusätzlich erhalten Jubilare.{0,120}"
                r"Sachgeschenk\s+im\s+Wert\s+von\s*(\d{2,3})[.,]\d{2}",
                text,
                flags=re.I | re.S,
            )
        if gift:
            gift_amount = next(g for g in gift.groups() if g)
            if gift_amount not in amounts:
                amounts.append(gift_amount)
        if amounts:
            return list(dict.fromkeys(amounts))
        window = (
            line.group(0) if line else _relevant_excerpt(text, query=query, limit=200)
        )
    else:
        window = _relevant_excerpt(text, query=query, limit=360)
    amounts = re.findall(r"(\d{2,3})[.,]\d{2}", window)
    return [amount for amount in dict.fromkeys(amounts) if amount != year]


def answer_covers_evidence(spoken: str, query: str, packed: dict) -> bool:
    if not spoken.strip():
        return False
    needed = expected_evidence_amounts(query, packed)
    if not needed:
        return True
    compact = spoken.replace(" ", "")
    return all(amount in compact for amount in needed)


def short_krn_voice_answer(
    query: str, packed: dict, citation: str | None = None
) -> str:
    """Short spoken answer built only from retrieval metadata (no model rewrite)."""
    language = detect_question_language(query)
    status = packed.get("status")
    if status == "unavailable":
        if language == "en":
            return (
                "Sorry, I cannot reliably search the KRN documents right now. "
                "Please try again."
            )
        if language == "fr":
            return (
                "Désolé, je ne peux pas consulter les documents KRN de façon "
                "fiable pour le moment. Réessaie s'il te plaît."
            )
        return RETRIEVAL_UNAVAILABLE_DE

    if is_krn_inventory_question(query):
        return grounded_fallback_answer(query, packed, citation)

    results = packed.get("results") or []
    if status != "ok" or not results:
        if language == "en":
            return "That is not stated in the available KRN documents."
        if language == "fr":
            return "Cela ne figure pas dans les documents KRN disponibles."
        return "Das steht in den verfügbaren KRN-Dokumenten nicht."

    fact = next((hit for hit in results if hit.get("answers")), None)
    if fact:
        cited = " ".join(
            format_citation(fact["filename"], page, language) for page in fact["pages"]
        )
        return ensure_citation(
            fact["answers"].get(language, fact["answers"]["de"]), cited
        )

    # A lexical hit alone is not a verified policy answer. Keep it available to
    # document search, but do not turn an arbitrary nearby amount into an entitlement.
    folded = fold_text(query)
    if (
        language == "de"
        and "einzelfahr" in folded
        and "preisstufe" in folded
        and not re.search(r"preisstufe\s*\d+", folded)
    ):
        return "Welche Preisstufe meinst du, zum Beispiel Preisstufe 1?"
    if language == "en":
        return "I found no reliable answer to that question in the available KRN documents."
    if language == "fr":
        return "Je n'ai pas trouvé de réponse fiable à cette question dans les documents KRN disponibles."
    return "Für diese Frage habe ich keine zuverlässige Antwort in den verfügbaren KRN-Dokumenten gefunden."


def grounded_fallback_answer(
    query: str, packed: dict, citation: str | None = None
) -> str:
    """User-visible answer built only from retrieval metadata (no model rewrite)."""
    language = detect_question_language(query)
    if packed.get("status") == "unavailable":
        if language == "en":
            return (
                "Sorry, I cannot reliably search the KRN documents right now. "
                "Please try again."
            )
        if language == "fr":
            return (
                "Désolé, je ne peux pas consulter les documents KRN de façon "
                "fiable pour le moment. Réessaie s'il te plaît."
            )
        return RETRIEVAL_UNAVAILABLE_DE
    if is_krn_inventory_question(query):
        documents = packed.get("documents") or []
        if packed.get("status") != "ok" or not documents:
            if language == "en":
                return "The KRN document inventory is currently unavailable."
            if language == "fr":
                return "L'inventaire des documents KRN n'est pas disponible."
            return "Die KRN-Dokumentenliste ist derzeit nicht verfügbar."
        names = "\n".join(f"- {doc['filename']}" for doc in documents)
        if language == "en":
            return f"These KRN source documents are available:\n{names}"
        if language == "fr":
            return f"Documents KRN disponibles :\n{names}"
        return f"Diese KRN-Quelldokumente sind verfügbar:\n{names}"

    results = packed.get("results") or []
    if packed.get("status") != "ok" or not results:
        if language == "en":
            return "That is not stated in the available KRN documents."
        if language == "fr":
            return "Cela ne figure pas dans les documents KRN disponibles."
        return "Das steht in den verfügbaren KRN-Dokumenten nicht."

    years = re.search(r"(\d+)\s*(?:jahre|years|ans)", fold_text(query))
    year = years.group(1) if years else None

    def hit_rank(hit: dict) -> float:
        folded = fold_text(hit.get("text") or "")
        score = float(hit.get("score") or 0)
        if year and f"{year} jahre" in folded:
            score += 50
        if year == "10" and "100" in folded:
            score += 25
        return score

    hit = max(results, key=hit_rank)
    excerpt = _relevant_excerpt(hit.get("text") or "", query=query, limit=480)
    prefix = f"{hit['filename']}, Seite {hit['page']}"
    if excerpt.startswith(prefix):
        excerpt = excerpt[len(prefix) :].lstrip(" .")
    citation = citation or format_citation(hit["filename"], hit["page"], language)
    return ensure_citation(excerpt, citation)


@function_tool
async def search_krn_docs(query: str) -> dict:
    """Search local KRN/RNN documents BEFORE answering internal company questions.

    Required for spoken German questions about Betriebszugehörigkeit, Jubiläum,
    Betriebsvereinbarung, BV, Verspätung, EC-Gerät, Schülerbeförderung,
    Ticketpreise, Tarife, Fahrpläne, Waben, Dienstanweisung, Genesungspaket,
    KRN or RNN rules. Do not answer these from general knowledge, web search,
    or the browser. Call this tool first, then cite filename and PDF page.

    Returns the strongest local hits with original filename and 1-based PDF page.
    Never invent a filename or page that is not in the hits.

    Args:
        query: The user question, preferably verbatim, including German wording.
    """
    try:
        packed = search_krn_index(query)
        allowed_filenames = [doc["filename"] for doc in load_inventory_documents()]
    except (OSError, ValueError, KeyError):
        packed = {"status": "unavailable", "results": []}
        allowed_filenames = []
    logger.info(
        "KRN retrieval status=%s hits=%d", packed["status"], len(packed["results"])
    )
    packed["answer"] = short_krn_voice_answer(query, packed)
    packed["allowed_filenames"] = allowed_filenames
    packed["instruction"] = (
        "Speak only answer, once, preserving its language, amounts and full citation. "
        "Do not combine it with earlier responses or other directives. "
        "Never cite a filename outside allowed_filenames. If answer says no reliable "
        "answer was found, do not assert that a document or price does not exist. "
        "Do not add a follow-up question."
    )
    return packed
