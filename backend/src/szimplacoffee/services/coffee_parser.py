"""SC-30: Coffee metadata parser.

Pure-function module that extracts structured coffee metadata from product
names and description text (plain text or HTML).
"""
from __future__ import annotations

import re
import string
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ParsedCoffeeMetadata:
    origin_text: str | None
    origin_country: str | None
    origin_region: str | None
    process_text: str | None
    process_family: str
    variety_text: str | None
    roast_cues: str | None
    roast_level: str
    tasting_notes_text: str | None
    metadata_source: str
    is_single_origin: bool
    is_espresso_recommended: bool
    confidence: float

    # Internal: field-level matched counts used by callers who want details
    _matched_fields: int = field(default=0, repr=False, compare=False)


# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

_COUNTRIES: list[str] = [
    "Ethiopia", "Kenya", "Colombia", "Guatemala", "Honduras", "Peru",
    "Brazil", "Costa Rica", "Panama", "Bolivia", "Mexico", "Indonesia",
    "Rwanda", "Burundi", "El Salvador", "Yemen", "PNG", "Hawaii",
    "Sumatra", "Java",
    # Additional producing countries
    "Ecuador", "Nicaragua", "Tanzania", "Uganda", "China", "Nepal",
    "Vietnam", "Myanmar", "Laos", "Thailand", "India", "Papua New Guinea",
    "Malawi", "Zambia", "Zimbabwe", "Cameroon", "Congo", "Madagascar",
    "Cuba", "Dominican Republic", "Haiti", "Jamaica",
]

# Demonyms → canonical country name
_DEMONYMS: dict[str, str] = {
    "Ethiopian": "Ethiopia",
    "Kenyan": "Kenya",
    "Colombian": "Colombia",
    "Guatemalan": "Guatemala",
    "Honduran": "Honduras",
    "Peruvian": "Peru",
    "Brazilian": "Brazil",
    "Rwandan": "Rwanda",
    "Burundian": "Burundi",
    "Indonesian": "Indonesia",
    "Bolivian": "Bolivia",
    "Mexican": "Mexico",
    "Yemeni": "Yemen",
    "Ecuadorian": "Ecuador",
    "Nicaraguan": "Nicaragua",
    "Tanzanian": "Tanzania",
    "Ugandan": "Uganda",
    "Salvadoran": "El Salvador",
    "Panamanian": "Panama",
    "Indian": "India",
    "Nepali": "Nepal",
    "Vietnamese": "Vietnam",
    "Jamaican": "Jamaica",
}

# Hawaii variants (diacritics / abbreviations)
_HAWAII_VARIANTS: list[str] = ["Hawai'i", "Hawaiʻi", "Kona", "Maui", "Kauai"]

_REGIONS: list[str] = [
    "Yirgacheffe", "Sidama", "Guji", "Gedeo", "Harrar", "Harrar",
    "Huila", "Antioquia", "Antigua", "Nariño", "Chiriquí",
    "Kintamani", "Nyeri", "Kirinyaga", "Murang'a", "Embu",
    "Tarrazu", "Tres Rios",
    "Cajamarca", "Puno",
    "Minas Gerais", "Cerrado", "Mogiana",
    "Aceh", "Flores", "Sulawesi",
    "Kigali", "Ngozi",
]

_PROCESS_KEYWORDS: list[tuple[str, str]] = [
    # (pattern, normalized)
    (r"\bwet\s+process\b", "washed"),
    (r"\bdry\s+process\b", "natural"),
    (r"\bcarbonic\s+maceration\b", "carbonic maceration"),
    (r"\bpulped\s+natural\b", "pulped natural"),
    (r"\bsemi[-\s]washed\b", "semi-washed"),
    (r"\bwet[-\s]hulled\b", "wet-hulled"),
    (r"\banaerobic\s+natural\b", "anaerobic natural"),
    (r"\banaerobic\s+washed\b", "anaerobic washed"),
    (r"\banaerobic\b", "anaerobic"),
    (r"\bhoney\b", "honey"),
    (r"\bnatural\b", "natural"),
    (r"\bwashed\b", "washed"),
    (r"\bexperimental\b", "experimental"),
]

_VARIETY_KEYWORDS: list[str] = [
    "pink bourbon", "pacamara", "maragogipe",
    "typica", "bourbon", "caturra", "catuai",
    "geisha", "gesha", "SL28", "SL34", "heirloom",
    "74110", "74112", "catimor", "java",
]

_ROAST_LIGHT: list[str] = [
    "light roast", "filter roast", "omni roast", "nordic roast", "nordic", "omni",
    "lightly roasted", "pour over roast", "pourover roast", "pour-over roast",
    "light filter",
]
_ROAST_MEDIUM: list[str] = [
    "medium roast", "all-purpose", "all purpose", "balanced roast",
    "medium-light", "medium light", "all-rounder", "everyday coffee",
]
_ROAST_DARK_ESPRESSO: list[str] = [
    "espresso roast", "dark roast", "dark-roast",
    "french roast", "italian roast", "bold roast",
    "full city", "full-city", "vienna roast",
]

_TASTING_PATTERNS: list[str] = [
    r"(?:notes?\s+of|tasting\s+notes?:?|flavou?rs?\s+of|cup\s+notes?:?|we\s+taste)\s*(.+?)(?:\.|$)",
    r"(?:tastes?\s+like)\s*(.+?)(?:\.|$)",
]

_BLEND_RE = re.compile(r"\bblend\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_html(markup: str) -> str:
    if not markup:
        return ""
    return BeautifulSoup(markup, "lxml").get_text("\n", strip=True)


def _haystack(name: str, description: str) -> str:
    """Combine name + description into one searchable string."""
    clean = _strip_html(description)
    return f"{name}\n{clean}"


def _extract_origin(text: str) -> str | None:
    """Return 'Country' or 'Country, Region' string, case-preserving.

    Finds the first country/region *by position in text* so "Brazil and Ethiopia"
    picks Brazil, not Ethiopia.  Also resolves demonyms and Hawaii variants.
    """
    country_matches: list[tuple[int, str]] = []

    # 1. Direct country name matches
    for country in _COUNTRIES:
        m = re.search(rf"\b{re.escape(country)}\b", text, re.IGNORECASE)
        if m:
            country_matches.append((m.start(), country))

    # 2. Hawaii variants (diacritics, island names)
    for variant in _HAWAII_VARIANTS:
        m = re.search(rf"\b{re.escape(variant)}\b", text, re.IGNORECASE)
        if m:
            country_matches.append((m.start(), "Hawaii"))

    # 3. Demonym resolution (e.g. "Ethiopian" → "Ethiopia")
    for demonym, canonical in _DEMONYMS.items():
        m = re.search(rf"\b{re.escape(demonym)}\b", text, re.IGNORECASE)
        if m:
            country_matches.append((m.start(), canonical))

    found_country: str | None = None
    if country_matches:
        # Pick the one that appears earliest in the text
        country_matches.sort(key=lambda x: x[0])
        found_country = country_matches[0][1]

    found_region: str | None = None
    for region in _REGIONS:
        if re.search(rf"\b{re.escape(region)}\b", text, re.IGNORECASE):
            found_region = region
            break

    if found_country and found_region:
        return f"{found_country}, {found_region}"
    if found_country:
        return found_country
    if found_region:
        return found_region
    return None


def _find_earliest_match(candidates: list[str], text: str) -> str | None:
    matches: list[tuple[int, str]] = []
    for candidate in candidates:
        match = re.search(rf"\b{re.escape(candidate)}\b", text, re.IGNORECASE)
        if match:
            matches.append((match.start(), candidate))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[0][1]


def _normalize_origin_parts(origin_text: str | None, text: str) -> tuple[str | None, str | None]:
    source = origin_text or text
    country = _find_earliest_match(_COUNTRIES, source)
    # Also check demonyms when direct country match fails
    if not country:
        for demonym, canonical in _DEMONYMS.items():
            if re.search(rf"\b{re.escape(demonym)}\b", source, re.IGNORECASE):
                country = canonical
                break
    # Also check Hawaii variants
    if not country:
        for variant in _HAWAII_VARIANTS:
            if re.search(rf"\b{re.escape(variant)}\b", source, re.IGNORECASE):
                country = "Hawaii"
                break
    region = _find_earliest_match(_REGIONS, source)
    return country, region


def _count_countries(text: str) -> int:
    found: set[str] = set()
    for c in _COUNTRIES:
        if re.search(rf"\b{re.escape(c)}\b", text, re.IGNORECASE):
            found.add(c)
    for variant in _HAWAII_VARIANTS:
        if re.search(rf"\b{re.escape(variant)}\b", text, re.IGNORECASE):
            found.add("Hawaii")
    for demonym, canonical in _DEMONYMS.items():
        if re.search(rf"\b{re.escape(demonym)}\b", text, re.IGNORECASE):
            found.add(canonical)
    return len(found)


def _extract_process(text: str) -> str | None:
    for pattern, normalized in _PROCESS_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return normalized
    return None


def _normalize_process_family(process_text: str | None, text: str, is_blend: bool) -> str:
    if is_blend:
        return "blend"

    haystack = " ".join(part for part in [process_text or "", text] if part).lower()
    if any(term in haystack for term in ["carbonic maceration", "anaerobic"]):
        return "anaerobic"
    if "wet hulled" in haystack or "wet-hulled" in haystack:
        return "wet-hulled"
    if any(term in haystack for term in ["honey", "pulped natural"]):
        return "honey"
    if any(term in haystack for term in ["natural", "dry process"]):
        return "natural"
    if any(term in haystack for term in ["washed", "wet process", "semi-washed"]):
        return "washed"
    return "unknown"


def _extract_variety(text: str) -> str | None:
    for keyword in _VARIETY_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
            # Preserve original capitalization from keyword list
            m = re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE)
            if m:
                return m.group(0)
    return None


def _extract_roast_cues(text: str) -> str | None:
    lowered = text.lower()
    found: list[str] = []
    for cue in _ROAST_DARK_ESPRESSO:
        if cue.lower() in lowered:
            found.append(cue)
    for cue in _ROAST_MEDIUM:
        if cue.lower() in lowered:
            found.append(cue)
    for cue in _ROAST_LIGHT:
        if cue.lower() in lowered:
            found.append(cue)
    if not found:
        return None
    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for c in found:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return ", ".join(deduped)


# Implicit dark / espresso signals used for roast inference
_DARK_ROAST_IMPLICIT_SIGNALS: list[str] = [
    "espresso", "dark chocolate", "dark cocoa", "bittersweet",
    "full city",
]


def _infer_roast_from_context(
    is_single_origin: bool,
    is_blend: bool,
    text: str,
) -> str:
    """Infer roast level when explicit cue patterns return nothing.

    Rules (ordered by confidence):
    1. Dark/espresso implicit signals in text → medium-dark
    2. Blend (not single origin) → medium-dark
    3. Single origin specialty → light (specialty roasters default)
    4. Otherwise → unknown
    """
    haystack = text.lower()
    if any(sig in haystack for sig in _DARK_ROAST_IMPLICIT_SIGNALS):
        return "medium-dark"
    if is_blend:
        return "medium-dark"
    if is_single_origin:
        return "light"
    return "unknown"


def _normalize_roast_level(
    roast_cues: str | None,
    text: str,
    *,
    is_single_origin: bool = False,
    is_blend: bool = False,
) -> str:
    haystack = " ".join(part for part in [roast_cues or "", text] if part).lower()
    if any(term in haystack for term in ["french roast", "italian roast", "dark roast", "dark-roast"]):
        return "dark"
    if any(term in haystack for term in ["espresso roast", "bold roast", "medium-dark", "full city", "full-city", "vienna roast"]):
        return "medium-dark"
    if any(term in haystack for term in ["omni roast", "all-purpose", "all purpose", "light to medium", "light-medium", "medium-light", "all-rounder"]):
        return "light-medium"
    if any(term in haystack for term in ["medium roast", "balanced roast", "everyday coffee"]):
        return "medium"
    if any(term in haystack for term in ["light roast", "filter roast", "nordic roast", "nordic", "lightly roasted", "pour over roast", "pourover roast", "pour-over roast", "omni"]):
        return "light"
    # Implicit inference from specialty coffee context
    return _infer_roast_from_context(is_single_origin, is_blend, text)


def _normalize_note(note: str) -> str:
    return note.lower().strip().strip(string.punctuation).strip()


def _extract_tasting_notes(text: str) -> str | None:
    """Extract and normalize tasting notes."""
    for pattern in _TASTING_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            raw = m.group(1).strip()
            notes = [_normalize_note(n) for n in re.split(r"[,&+]|\band\b", raw)]
            notes = [n for n in notes if n and len(n) > 1]
            if notes:
                return ", ".join(dict.fromkeys(notes))  # deduplicate, preserve order

    # Fallback: look for labelled notes line
    label_match = re.search(
        r"(?:tasting\s+notes?|flavor\s+notes?|notes?|cup\s+profile)\s*[:\-]\s*(.+)",
        text,
        re.IGNORECASE,
    )
    if label_match:
        raw = label_match.group(1).strip()
        notes = [_normalize_note(n) for n in re.split(r"[,&+]|\band\b", raw)]
        notes = [n for n in notes if n and len(n) > 1]
        if notes:
            return ", ".join(dict.fromkeys(notes))

    return None


def _is_espresso_recommended(roast_cues: str | None, process_text: str | None, text: str) -> bool:
    if roast_cues and any(kw in roast_cues.lower() for kw in ["espresso", "dark roast", "dark-roast", "french", "italian", "bold"]):
        return True
    if re.search(r"\bespresso\b", text, re.IGNORECASE):
        return True
    # Light/filter-only → NOT espresso recommended
    if roast_cues:
        rc_lower = roast_cues.lower()
        if any(kw in rc_lower for kw in ["light roast", "filter roast", "nordic"]):
            return False
    return False


def _compute_confidence(
    origin: str | None,
    process: str | None,
    variety: str | None,
    roast_cues: str | None,
    tasting_notes: str | None,
    from_name_only: bool,
) -> float:
    filled = sum(1 for v in [origin, process, variety, roast_cues, tasting_notes] if v)
    if from_name_only:
        # All data came from name alone — lower confidence ceiling
        if filled >= 3:
            return 0.7
        if filled == 2:
            return 0.5
        if filled == 1:
            return 0.3
        return 0.1
    if filled >= 3:
        return 1.0
    if filled == 2:
        return 0.7
    if filled == 1:
        return 0.4
    return 0.1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_coffee_metadata(name: str, description: str) -> ParsedCoffeeMetadata:
    """Extract structured coffee metadata from product name + description.

    Parameters
    ----------
    name:        Product name (plain text).
    description: Product description — may contain HTML; will be stripped.

    Returns
    -------
    ParsedCoffeeMetadata dataclass.
    """
    # Prefer description for parsing, fall back to name only
    clean_desc = _strip_html(description)
    full_text = _haystack(name, description)
    from_name_only = not clean_desc.strip()

    # -- Origin --
    origin = _extract_origin(full_text)
    if not origin:
        # Try structured label patterns first
        label_match = re.search(
            r"(?:origin|country|farm|region)\s*[:\-]\s*([^\n,\.]+)",
            full_text,
            re.IGNORECASE,
        )
        if label_match:
            origin = label_match.group(1).strip()

    # -- Process --
    process = _extract_process(full_text)
    if not process:
        label_match = re.search(
            r"(?:process(?:ing)?)\s*[:\-]\s*([^\n,\.]+)",
            full_text,
            re.IGNORECASE,
        )
        if label_match:
            process = label_match.group(1).strip()

    # -- Variety --
    variety = _extract_variety(full_text)
    if not variety:
        label_match = re.search(
            r"(?:variet(?:y|al|als?)|cultivar)\s*[:\-]\s*([^\n,\.]+)",
            full_text,
            re.IGNORECASE,
        )
        if label_match:
            variety = label_match.group(1).strip()

    # -- Roast cues --
    roast_cues = _extract_roast_cues(full_text)

    # -- Tasting notes --
    tasting_notes = _extract_tasting_notes(full_text)

    # -- Flags --
    n_countries = _count_countries(full_text)
    # "Not a blend" / "not a blend" → negative assertion, don't penalise
    _blend_negated = re.search(r"\bnot\s+a\s+blend\b", full_text, re.IGNORECASE)
    is_blend = bool(_BLEND_RE.search(full_text) and not _blend_negated)
    is_single_origin = (
        n_countries == 1
        and not is_blend
    )

    espresso_rec = _is_espresso_recommended(roast_cues, process, full_text)
    origin_country, origin_region = _normalize_origin_parts(origin, full_text)
    process_family = _normalize_process_family(process, full_text, is_blend)
    roast_level = _normalize_roast_level(roast_cues, full_text, is_single_origin=is_single_origin, is_blend=is_blend)

    # -- Confidence --
    filled_count = sum(1 for v in [origin, process, variety, roast_cues, tasting_notes] if v)
    confidence = _compute_confidence(origin, process, variety, roast_cues, tasting_notes, from_name_only)

    return ParsedCoffeeMetadata(
        origin_text=origin,
        origin_country=origin_country,
        origin_region=origin_region,
        process_text=process,
        process_family=process_family,
        variety_text=variety,
        roast_cues=roast_cues,
        roast_level=roast_level,
        tasting_notes_text=tasting_notes,
        metadata_source="parser",
        is_single_origin=is_single_origin,
        is_espresso_recommended=espresso_rec,
        confidence=confidence,
        _matched_fields=filled_count,
    )
