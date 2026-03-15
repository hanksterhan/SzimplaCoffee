"""SC-30: Tests for the coffee metadata parser.

Fixtures are real-world-style product name + description pairs.
"""
from __future__ import annotations

import pytest

from szimplacoffee.services.coffee_parser import ParsedCoffeeMetadata, parse_coffee_metadata


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES = [
    # 0 – Rich Shopify-style product with structured fields
    {
        "name": "Ethiopia Yirgacheffe Washed",
        "description": (
            "Origin: Yirgacheffe, Ethiopia\n"
            "Process: Washed\n"
            "Variety: Heirloom\n"
            "Roast: Light Roast\n"
            "Tasting Notes: Jasmine, lemon verbena, peach iced tea\n"
            "Grown at altitude 1950–2200 masl, this delicate filter coffee shines brightest as a pour-over."
        ),
        "expect": {
            "origin_text_contains": "Ethiopia",
            "process_text": "washed",
            "variety_text_contains": "Heirloom",
            "roast_cues_contains": "light roast",
            "tasting_notes_contains": "jasmine",
            "is_single_origin": True,
            "is_espresso_recommended": False,
            "confidence_gte": 1.0,
        },
    },
    # 1 – Colombian natural espresso, pipes-style description
    {
        "name": "Colombia Huila Natural Espresso Roast",
        "description": (
            "Colombia | Huila | Natural | Bourbon\n"
            "We taste: dark chocolate, dried cherry, molasses.\n"
            "Espresso roast — medium-dark body with a sweet finish. "
            "Excellent for milk-based drinks. Not a blend."
        ),
        "expect": {
            "origin_text_contains": "Colombia",
            "process_text": "natural",
            "variety_text_contains": "Bourbon",
            "roast_cues_contains": "espresso roast",
            "tasting_notes_contains": "dark chocolate",
            "is_single_origin": True,
            "is_espresso_recommended": True,
            "confidence_gte": 1.0,
        },
    },
    # 2 – Kenyan SL28 with HTML markup
    {
        "name": "Kenya Nyeri SL28 Natural",
        "description": (
            "<p><strong>Origin:</strong> Nyeri, Kenya</p>"
            "<p><strong>Variety:</strong> SL28</p>"
            "<p><strong>Process:</strong> Natural</p>"
            "<p>Tasting notes: blackcurrant, red grape, brown sugar.</p>"
            "<p>Best enjoyed as filter — light to medium roast.</p>"
        ),
        "expect": {
            "origin_text_contains": "Kenya",
            "process_text": "natural",
            "variety_text_contains": "SL28",
            "tasting_notes_contains": "blackcurrant",
            "is_single_origin": True,
            "is_espresso_recommended": False,
            "confidence_gte": 1.0,
        },
    },
    # 3 – Blend with two origins — should NOT be single-origin
    {
        "name": "House Espresso Blend",
        "description": (
            "A balanced espresso blend combining Brazil and Ethiopia. "
            "Dark roast. Notes of caramel, milk chocolate, and toasted almond. "
            "Ideal for flat whites and long blacks."
        ),
        "expect": {
            "origin_text_contains": "Brazil",
            "process_text": None,
            "roast_cues_contains": "dark roast",
            "tasting_notes_contains": "caramel",
            "is_single_origin": False,
            "is_espresso_recommended": True,
            "confidence_gte": 0.7,
        },
    },
    # 4 – Sparse name-only product (no description)
    {
        "name": "Guatemala Antigua Natural Light Roast",
        "description": "",
        "expect": {
            "origin_text_contains": "Guatemala",
            "process_text": "natural",
            "roast_cues_contains": "light roast",
            "is_single_origin": True,
            "confidence_gte": 0.3,
        },
    },
    # 5 – Panama Geisha with carbonic maceration + omni roast
    # Omni roast = suitable for filter AND espresso → espresso recommended = True
    {
        "name": "Panama Chiriquí Geisha Carbonic Maceration",
        "description": (
            "Farm: Hacienda La Esmeralda, Boquete (Chiriquí province)\n"
            "Variety: Geisha\n"
            "Process: Carbonic maceration\n"
            "Roast: Omni roast — suitable for both filter and espresso.\n"
            "Flavors of: bergamot, white peach, jasmine, mandarin."
        ),
        "expect": {
            "origin_text_contains": "Panama",
            "process_text": "carbonic maceration",
            "variety_text_contains": "Geisha",
            "roast_cues_contains": "omni",
            "tasting_notes_contains": "bergamot",
            "is_single_origin": True,
            "is_espresso_recommended": True,  # "suitable for...espresso" detected
            "confidence_gte": 1.0,
        },
    },
    # 6 – Honduras anaerobic washed
    {
        "name": "Honduras Anaerobic Washed",
        "description": (
            "Origin: Honduras\n"
            "Processing: Anaerobic washed\n"
            "Cup notes: tropical fruit, hibiscus, grape candy\n"
            "Roast level: medium roast"
        ),
        "expect": {
            "origin_text_contains": "Honduras",
            "process_text": "anaerobic washed",
            "roast_cues_contains": "medium roast",
            "tasting_notes_contains": "tropical fruit",
            "is_single_origin": True,
            "is_espresso_recommended": False,
            "confidence_gte": 1.0,
        },
    },
    # 7 – Rwanda Bourbon honey process
    {
        "name": "Rwanda Nyeri Bourbon Honey",
        "description": (
            "A sweet honey-processed coffee from Rwanda.\n"
            "Variety: Bourbon\n"
            "Tasting notes of: brown sugar, apricot, raisin.\n"
            "Filter roast."
        ),
        "expect": {
            "origin_text_contains": "Rwanda",
            "process_text": "honey",
            "variety_text_contains": "Bourbon",
            "roast_cues_contains": "filter roast",
            "tasting_notes_contains": "apricot",
            "is_single_origin": True,
            "is_espresso_recommended": False,
            "confidence_gte": 1.0,
        },
    },
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check(result: ParsedCoffeeMetadata, expect: dict) -> None:
    if "origin_text_contains" in expect:
        assert result.origin_text is not None, "Expected origin_text to be set"
        assert expect["origin_text_contains"].lower() in result.origin_text.lower(), (
            f"origin_text={result.origin_text!r} should contain {expect['origin_text_contains']!r}"
        )
    if "process_text" in expect:
        if expect["process_text"] is None:
            assert result.process_text is None or result.process_text == "", (
                f"Expected process_text=None, got {result.process_text!r}"
            )
        else:
            assert result.process_text is not None
            assert result.process_text.lower() == expect["process_text"].lower(), (
                f"process_text={result.process_text!r} != {expect['process_text']!r}"
            )
    if "variety_text_contains" in expect:
        assert result.variety_text is not None
        assert expect["variety_text_contains"].lower() in result.variety_text.lower(), (
            f"variety_text={result.variety_text!r} should contain {expect['variety_text_contains']!r}"
        )
    if "roast_cues_contains" in expect:
        assert result.roast_cues is not None
        assert expect["roast_cues_contains"].lower() in result.roast_cues.lower(), (
            f"roast_cues={result.roast_cues!r} should contain {expect['roast_cues_contains']!r}"
        )
    if "tasting_notes_contains" in expect:
        assert result.tasting_notes_text is not None
        assert expect["tasting_notes_contains"].lower() in result.tasting_notes_text.lower(), (
            f"tasting_notes_text={result.tasting_notes_text!r} should contain {expect['tasting_notes_contains']!r}"
        )
    if "is_single_origin" in expect:
        assert result.is_single_origin == expect["is_single_origin"], (
            f"is_single_origin={result.is_single_origin} != {expect['is_single_origin']}"
        )
    if "is_espresso_recommended" in expect:
        assert result.is_espresso_recommended == expect["is_espresso_recommended"], (
            f"is_espresso_recommended={result.is_espresso_recommended} != {expect['is_espresso_recommended']}"
        )
    if "confidence_gte" in expect:
        assert result.confidence >= expect["confidence_gte"], (
            f"confidence={result.confidence} < {expect['confidence_gte']}"
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
def test_parse_fixture(fixture: dict) -> None:
    result = parse_coffee_metadata(fixture["name"], fixture["description"])
    _check(result, fixture["expect"])


def test_returns_dataclass() -> None:
    result = parse_coffee_metadata("Ethiopia Natural", "")
    assert isinstance(result, ParsedCoffeeMetadata)


def test_empty_inputs_return_defaults() -> None:
    result = parse_coffee_metadata("", "")
    assert result.origin_text is None
    assert result.process_text is None
    assert result.confidence == 0.1


def test_confidence_levels() -> None:
    # 3+ fields → 1.0 with description
    r = parse_coffee_metadata(
        "Ethiopia",
        "Process: Washed\nVariety: Heirloom\nTasting notes: peach, citrus",
    )
    assert r.confidence == 1.0

    # 1 field only
    r1 = parse_coffee_metadata("Coffee", "Process: Natural")
    assert r1.confidence == 0.4


def test_blend_not_single_origin() -> None:
    r = parse_coffee_metadata("House Blend", "Ethiopia and Colombia blend, dark roast.")
    assert not r.is_single_origin


def test_espresso_roast_flag() -> None:
    r = parse_coffee_metadata("Espresso Blend", "Espresso roast, dark and bold.")
    assert r.is_espresso_recommended


def test_light_roast_not_espresso() -> None:
    r = parse_coffee_metadata("Ethiopia Filter", "Light roast. Notes of jasmine and lemon.")
    assert not r.is_espresso_recommended


def test_html_description_stripped() -> None:
    r = parse_coffee_metadata(
        "Kenya SL28",
        "<h2>Kenya</h2><p>Process: <strong>Washed</strong></p><p>Notes of: citrus, florals.</p>",
    )
    assert r.origin_text is not None
    assert "Kenya" in r.origin_text
    assert r.process_text == "washed"


def test_tasting_notes_deduplication() -> None:
    r = parse_coffee_metadata(
        "Colombia",
        "Tasting notes: chocolate, caramel, chocolate",
    )
    assert r.tasting_notes_text is not None
    notes_list = [n.strip() for n in r.tasting_notes_text.split(",")]
    assert notes_list.count("chocolate") == 1


def test_carbonic_maceration_normalizes() -> None:
    r = parse_coffee_metadata("Panama", "Process: carbonic maceration")
    assert r.process_text == "carbonic maceration"


def test_wet_process_normalizes_to_washed() -> None:
    r = parse_coffee_metadata("Ethiopia", "Wet process coffee from the highlands.")
    assert r.process_text == "washed"


def test_dry_process_normalizes_to_natural() -> None:
    r = parse_coffee_metadata("Brazil", "Dry process, low altitude.")
    assert r.process_text == "natural"
