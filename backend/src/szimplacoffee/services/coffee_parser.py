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
    process_text: str | None
    variety_text: str | None
    roast_cues: str | None
    tasting_notes_text: str | None
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
]

_REGIONS: list[str] = [
    "Yirgacheffe", "Sidama", "Guji", "Gedeo",
    "Huila", "Antioquia", "Antigua", "Nariño", "Chiriquí",
    "Kintamani", "Nyeri",
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

_ROAST_LIGHT: list[str] = ["light roast", "filter roast", "omni roast", "nordic roast", "nordic", "omni"]
_ROAST_MEDIUM: list[str] = ["medium roast", "all-purpose", "all purpose", "balanced roast"]
_ROAST_DARK_ESPRESSO: list[str] = [
    "espresso roast", "dark roast", "dark-roast",
    "french roast", "italian roast", "bold roast",
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
    picks Brazil, not Ethiopia.
    """
    # Scan all countries, record their earliest match position
    country_matches: list[tuple[int, str]] = []
    for country in _COUNTRIES:
        m = re.search(rf"\b{re.escape(country)}\b", text, re.IGNORECASE)
        if m:
            country_matches.append((m.start(), country))

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


def _count_countries(text: str) -> int:
    return sum(
        1 for c in _COUNTRIES
        if re.search(rf"\b{re.escape(c)}\b", text, re.IGNORECASE)
    )


def _extract_process(text: str) -> str | None:
    for pattern, normalized in _PROCESS_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return normalized
    return None


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
    is_single_origin = (
        n_countries == 1
        and (not _BLEND_RE.search(full_text) or bool(_blend_negated))
    )

    espresso_rec = _is_espresso_recommended(roast_cues, process, full_text)

    # -- Confidence --
    filled_count = sum(1 for v in [origin, process, variety, roast_cues, tasting_notes] if v)
    confidence = _compute_confidence(origin, process, variety, roast_cues, tasting_notes, from_name_only)

    return ParsedCoffeeMetadata(
        origin_text=origin,
        process_text=process,
        variety_text=variety,
        roast_cues=roast_cues,
        tasting_notes_text=tasting_notes,
        is_single_origin=is_single_origin,
        is_espresso_recommended=espresso_rec,
        confidence=confidence,
        _matched_fields=filled_count,
    )
