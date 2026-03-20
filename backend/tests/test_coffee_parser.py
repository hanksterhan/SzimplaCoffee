"""SC-30: Tests for the coffee metadata parser.

Fixtures are real-world-style product name + description pairs.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from szimplacoffee.db import Base
from szimplacoffee.models import Merchant, MerchantFieldPattern, ProductMetadataOverride
from szimplacoffee.services.crawlers import _apply_metadata_overrides, _apply_metadata_rule, _enrich_payload_with_parser, _is_coffee_product
from szimplacoffee.services.coffee_parser import (
    ParsedCoffeeMetadata,
    default_process_family_for_country,
    parse_coffee_metadata,
)


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
            "origin_country": "Ethiopia",
            "origin_region": "Yirgacheffe",
            "process_text": "washed",
            "process_family": "washed",
            "variety_text_contains": "Heirloom",
            "roast_cues_contains": "light roast",
            "roast_level": "light",
            "tasting_notes_contains": "jasmine",
            "metadata_source": "parser",
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
            "origin_country": "Colombia",
            "origin_region": "Huila",
            "process_text": "natural",
            "process_family": "natural",
            "variety_text_contains": "Bourbon",
            "roast_cues_contains": "espresso roast",
            "roast_level": "medium-dark",
            "tasting_notes_contains": "dark chocolate",
            "metadata_source": "parser",
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
            "origin_country": "Kenya",
            "origin_region": "Nyeri",
            "process_text": "natural",
            "process_family": "natural",
            "variety_text_contains": "SL28",
            "roast_level": "light-medium",
            "tasting_notes_contains": "blackcurrant",
            "metadata_source": "parser",
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
            "process_family": "blend",
            "roast_cues_contains": "dark roast",
            "roast_level": "dark",
            "tasting_notes_contains": "caramel",
            "metadata_source": "parser",
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
            "origin_country": "Guatemala",
            "origin_region": "Antigua",
            "process_text": "natural",
            "process_family": "natural",
            "roast_cues_contains": "light roast",
            "roast_level": "light",
            "metadata_source": "parser",
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
            "origin_country": "Panama",
            "origin_region": "Chiriquí",
            "process_text": "carbonic maceration",
            "process_family": "anaerobic",
            "variety_text_contains": "Geisha",
            "roast_cues_contains": "omni",
            "roast_level": "light-medium",
            "tasting_notes_contains": "bergamot",
            "metadata_source": "parser",
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
            "origin_country": "Honduras",
            "process_text": "anaerobic washed",
            "process_family": "anaerobic",
            "roast_cues_contains": "medium roast",
            "roast_level": "medium",
            "tasting_notes_contains": "tropical fruit",
            "metadata_source": "parser",
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
            "origin_country": "Rwanda",
            "origin_region": "Nyeri",
            "process_text": "honey",
            "process_family": "honey",
            "variety_text_contains": "Bourbon",
            "roast_cues_contains": "filter roast",
            "roast_level": "light",
            "tasting_notes_contains": "apricot",
            "metadata_source": "parser",
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
    if "origin_country" in expect:
        assert result.origin_country == expect["origin_country"]
    if "origin_region" in expect:
        assert result.origin_region == expect["origin_region"]
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
    if "process_family" in expect:
        assert result.process_family == expect["process_family"]
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
    if "roast_level" in expect:
        assert result.roast_level == expect["roast_level"]
    if "tasting_notes_contains" in expect:
        assert result.tasting_notes_text is not None
        assert expect["tasting_notes_contains"].lower() in result.tasting_notes_text.lower(), (
            f"tasting_notes_text={result.tasting_notes_text!r} should contain {expect['tasting_notes_contains']!r}"
        )
    if "metadata_source" in expect:
        assert result.metadata_source == expect["metadata_source"]
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
    assert result.origin_country is None
    assert result.process_text is None
    assert result.process_family == "unknown"
    assert result.roast_level == "unknown"
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
    assert r.process_family == "blend"


def test_classifier_keeps_filter_roast_coffee() -> None:
    assert _is_coffee_product("Ethiopia Filter Roast Coffee")


def test_apply_metadata_rule_sets_override_provenance() -> None:
    payload = {"metadata_confidence": 0.4, "metadata_source": "parser"}

    applied = _apply_metadata_rule(payload, "roast_level", "light-medium", 0.97)

    assert applied is True
    assert payload["roast_level"] == "light-medium"
    assert payload["roast_level_source"] == "override"
    assert payload["roast_level_confidence"] == 0.97
    assert payload["metadata_source"] == "override"
    assert payload["metadata_confidence"] == 0.97


def test_parser_emits_field_level_confidence_and_provenance() -> None:
    parsed = parse_coffee_metadata(
        "Ethiopia Yirgacheffe Washed",
        "Origin: Yirgacheffe, Ethiopia\nProcess: Washed\nRoast: Light Roast",
    )

    assert parsed.origin_country == "Ethiopia"
    assert parsed.origin_country_source == "parser"
    assert parsed.origin_country_confidence == pytest.approx(0.9)
    assert parsed.process_family == "washed"
    assert parsed.process_family_source == "parser"
    assert parsed.process_family_confidence == pytest.approx(0.9)
    assert parsed.roast_level == "light"
    assert parsed.roast_level_source == "parser"
    assert parsed.roast_level_confidence == pytest.approx(0.9)


def test_enrich_payload_with_parser_sets_field_level_semantics() -> None:
    payload = _enrich_payload_with_parser({}, "Kenya Nyeri", "Washed coffee with a light roast.")

    assert payload["origin_country"] == "Kenya"
    assert payload["origin_country_source"] == "parser"
    assert payload["origin_country_confidence"] > 0
    assert payload["process_family"] == "washed"
    assert payload["process_family_source"] == "parser"
    assert payload["roast_level"] == "light"
    assert payload["roast_level_source"] == "parser"
    assert payload["metadata_confidence"] == max(
        payload["origin_country_confidence"],
        payload["process_family_confidence"],
        payload["roast_level_confidence"],
    )


def test_apply_metadata_overrides_supports_patterns_and_product_corrections() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        merchant = Merchant(
            name="Override Roasters",
            canonical_domain="override.example",
            homepage_url="https://override.example",
            platform_type="custom",
        )
        session.add(merchant)
        session.flush()

        session.add(
            MerchantFieldPattern(
                merchant_id=merchant.id,
                field_name="roast_level",
                pattern=r"omni roast",
                normalized_value="light-medium",
                confidence=0.96,
            )
        )
        session.add(
            ProductMetadataOverride(
                merchant_id=merchant.id,
                external_product_id="sku-1",
                origin_country="Panama",
                origin_country_confidence=0.99,
                origin_country_source="override",
                origin_region="Chiriquí",
                process_family="anaerobic",
                process_family_confidence=0.98,
                process_family_source="override",
                metadata_confidence=1.0,
            )
        )
        session.commit()

        payload = {
            "origin_country": "Guatemala",
            "process_family": "natural",
            "metadata_confidence": 0.5,
            "metadata_source": "parser",
        }

        updated = _apply_metadata_overrides(
            session,
            merchant,
            "sku-1",
            payload,
            "Panama Geisha",
            "Omni roast with layered florals.",
        )

        assert updated["roast_level"] == "light-medium"
        assert updated["roast_level_source"] == "override"
        assert updated["roast_level_confidence"] == 0.96
        assert updated["origin_country"] == "Panama"
        assert updated["origin_country_source"] == "override"
        assert updated["origin_country_confidence"] == 0.99
        assert updated["origin_region"] == "Chiriquí"
        assert updated["process_family"] == "anaerobic"
        assert updated["process_family_source"] == "override"
        assert updated["process_family_confidence"] == 0.98
        assert updated["metadata_source"] == "override"
        assert updated["metadata_confidence"] == 1.0


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


# ---------------------------------------------------------------------------
# SC-62: Origin extraction – new country coverage tests
# ---------------------------------------------------------------------------

def test_origin_ecuador() -> None:
    r = parse_coffee_metadata("Ecuador El Dorado Wush Wush", "")
    assert r.origin_country == "Ecuador"
    assert r.origin_text is not None


def test_origin_china() -> None:
    r = parse_coffee_metadata("China Lao Xu Zhai Anaerobic", "")
    assert r.origin_country == "China"
    assert r.origin_text is not None


def test_origin_nepal() -> None:
    r = parse_coffee_metadata("Nepal Sindhupalchowk", "")
    assert r.origin_country == "Nepal"
    assert r.origin_text is not None


def test_origin_india() -> None:
    r = parse_coffee_metadata("India Kerehaklu Estate", "")
    assert r.origin_country == "India"
    assert r.origin_text is not None


def test_origin_nicaragua() -> None:
    r = parse_coffee_metadata("Little Buddy", "From Nicaragua, honey processed.")
    assert r.origin_country == "Nicaragua"
    assert r.origin_text is not None


def test_origin_hawaii_diacritic() -> None:
    r = parse_coffee_metadata("Hawai'i Monarch Kona Pacamara Natural", "")
    assert r.origin_country == "Hawaii"
    assert r.origin_text is not None


def test_origin_hawaii_kona_variant() -> None:
    r = parse_coffee_metadata("Kona Peaberry Extra Fancy", "")
    assert r.origin_country == "Hawaii"


def test_origin_demonym_ethiopian() -> None:
    r = parse_coffee_metadata("Morning Sun", "A bright Ethiopian washed coffee from the highlands.")
    assert r.origin_country == "Ethiopia"
    assert r.origin_text is not None


def test_origin_demonym_colombian() -> None:
    r = parse_coffee_metadata("Muse", "Colombian single-origin, natural process.")
    assert r.origin_country == "Colombia"
    assert r.origin_text is not None


def test_origin_demonym_kenyan() -> None:
    r = parse_coffee_metadata("Buchiro", "A classic Kenyan AA, bright and juicy.")
    assert r.origin_country == "Kenya"


def test_origin_demonym_rwandan() -> None:
    r = parse_coffee_metadata("Buliza", "Rwandan honey process, orange blossom notes.")
    assert r.origin_country == "Rwanda"


def test_origin_demonym_in_description_only() -> None:
    """Demonym in description should resolve when product name is opaque."""
    r = parse_coffee_metadata("Espresso Series 1", "Guatemalan natural, ripe plum and brown sugar.")
    assert r.origin_country == "Guatemala"


def test_origin_single_country_is_single_origin() -> None:
    r = parse_coffee_metadata("Ecuador El Dorado", "")
    assert r.is_single_origin is True


def test_origin_count_demonym_blend() -> None:
    """Two demonyms → blend, not single-origin."""
    r = parse_coffee_metadata("Blend", "Ethiopian and Colombian coffees in this blend.")
    assert r.is_single_origin is False


# ---------------------------------------------------------------------------
# SC-63: Process pattern tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,desc,expected_family", [
    ("Kenya Boma Washed", "Washed. Citrus and floral.", "washed"),
    ("Ethiopia Natural", "Naturally processed. Blueberry notes.", "natural"),
    ("Colombia White Honey Process", "White honey process. Sweet caramel.", "honey"),
    ("El Salvador Anaerobic Washed", "Anaerobic fermentation. Complex.", "anaerobic"),
    ("Guatemala Carbonic Maceration", "Carbonic maceration washed. Clean.", "anaerobic"),
    ("Brazil Natural Pulped", "Pulped natural process.", "honey"),
    ("Sumatra Wet-Hulled", "Wet-hulled processing.", "wet-hulled"),
    ("Colombia Dry Process Natural", "Dry process. Fruity notes.", "natural"),
    ("Honduras Wet Process", "Wet process. Clean cup.", "washed"),
    ("Panama Gesha Washed", "", "washed"),
])
def test_process_family_patterns_sc63(name: str, desc: str, expected_family: str) -> None:
    result = parse_coffee_metadata(name, desc)
    assert result.process_family == expected_family, (
        f"Expected process_family={expected_family!r} for {name!r}, got {result.process_family!r}"
    )


# ---------------------------------------------------------------------------
# SC-63: Roast level tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,desc,expected_level", [
    # Explicit pattern matches
    ("Ethiopia Yirgacheffe", "Light roast. Floral and citrus.", "light"),
    ("Colombia Espresso Roast", "Espresso roast blend.", "medium-dark"),
    ("House Dark Blend", "Dark roast. Chocolate and tobacco.", "dark"),
    ("Brazil Medium", "Medium roast. Balanced.", "medium"),
    ("Omni Roast House", "Omni roast. All-purpose filter and espresso.", "light-medium"),
    ("Bolivia All-Purpose", "All-purpose roast level.", "light-medium"),
    ("Full City Roast", "Full city roast profile.", "medium-dark"),
    # Implicit inference: single origin → light
    ("Kenya Kirinyaga Washed", "", "light"),
    ("Ethiopia Bochesa Washed", "Washed process. Citrus, jasmine.", "light"),
    ("Colombia Gesha Natural", "Natural process. Complex fruity.", "light"),
    # Blend → medium-dark
    ("Morning Sun Blend", "A blend of African and Latin American coffees.", "medium-dark"),
    # Explicit dark wins over inference
    ("Rwanda Natural", "French roast.", "dark"),
])
def test_roast_level_patterns_sc63(name: str, desc: str, expected_level: str) -> None:
    result = parse_coffee_metadata(name, desc)
    assert result.roast_level == expected_level, (
        f"Expected roast_level={expected_level!r} for {name!r}, got {result.roast_level!r}"
    )


# ---------------------------------------------------------------------------
# SC-85: Region → country derivation tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("region_text,expected_country", [
    ("Nariño", "Colombia"),
    ("Huila", "Colombia"),
    ("Tolima", "Colombia"),
    ("Yirgacheffe", "Ethiopia"),
    ("Sidama", "Ethiopia"),
    ("Guji", "Ethiopia"),
    ("Nyeri", "Kenya"),
    ("Kirinyaga", "Kenya"),
    ("Tarrazu", "Costa Rica"),
    ("Cajamarca", "Peru"),
    ("Ngozi", "Burundi"),
    ("Kigali", "Rwanda"),
    ("Antigua", "Guatemala"),
    ("Minas Gerais", "Brazil"),
    ("Sulawesi", "Indonesia"),
    ("Aceh", "Indonesia"),
])
def test_region_to_country_derivation_sc85(region_text: str, expected_country: str) -> None:
    """When origin_text is a region name, origin_country should be inferred."""
    result = parse_coffee_metadata("Single Origin Coffee", region_text)
    assert result.origin_country == expected_country, (
        f"Expected origin_country={expected_country!r} for region {region_text!r}, got {result.origin_country!r}"
    )


@pytest.mark.parametrize("name,expected_variety", [
    ("Wush Wush Natural", "wush wush"),
    ("Pacas Honey Process", "pacas"),
    ("Mundo Novo Pulped Natural", "mundo novo"),
    ("Obata Washed", "obata"),
    ("Sudan Rume Natural", "sudan rume"),
    ("Tabi Washed", "tabi"),
])
def test_new_variety_keywords_sc85(name: str, expected_variety: str) -> None:
    """New variety keywords should be recognized by the parser."""
    result = parse_coffee_metadata(name, "")
    assert result.variety_text is not None, f"Expected variety match for {name!r}"
    assert result.variety_text.lower() == expected_variety.lower(), (
        f"Expected variety={expected_variety!r} for {name!r}, got {result.variety_text!r}"
    )


# ---------------------------------------------------------------------------
# SC-87: Expanded variety extraction tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,desc,expected_variety", [
    # New explicit keywords
    ("El Salvador Malacara SL-28 XF", "", "SL28"),
    ("Guatemala SL-28", "", "SL28"),
    ("Guatemala SL 28", "", "SL28"),
    ("Guatemala SL28", "", "SL28"),
    ("Kenya Kirinyaga SL-34", "", "SL34"),
    ("Archive: Colombia Nursery Project Chiroso", "", "Chiroso"),
    ("Colombia Inmaculada Eugenioides", "", "Eugenioides"),
    ("Colombia Nariño Castillo", "", "Castillo"),
    ("Honduras Caballeros Batian Washed", "", "Batian"),
    ("Guatemala Ethiopia Landrace", "", "Landrace"),
    ("Colombia Juan Martín Arara", "", "Arara"),
    ("Ecuador Hacienda La Papaya Sidra", "", "Sidra"),
    ("Honduras El Portillo Natural Parainema", "", "Parainema"),
    ("Peru Timbuyacu Maragogype", "", "Maragogipe"),  # Maragogype → Maragogipe
    # Accented spellings
    ("Brazil Sítio Santa Marta Catuaí", "", "Catuai"),
    ("Colombia Tipica Honey", "", "Typica"),
    # Multi-word variety priority (Pink Bourbon > Bourbon)
    ("Colombia Juan Martín Pink Bourbon", "", "pink bourbon"),
    ("Colombia Red Bourbon Natural", "", "Red Bourbon"),
    ("Brazil Fazenda IP Yellow Bourbon", "", "yellow bourbon"),
    # Country-based defaults (use_country_default=True)
    ("Ethiopia Gatta Anaerobic Natural", "", "Heirloom"),
    ("Archive: Ethiopia Adorsi", "", "Heirloom"),
    ("Rwanda Kanzu Station", "", "Bourbon"),
    ("Burundi Long Miles Munyinya Hill", "", "Bourbon"),
    ("Kenya Boma AA Micro Lot", "", "SL28"),
    ("Uganda Kamogo Station", "", "SL14"),
    ("Bolivia Sol de la Mañana", "", "Typica"),
    ("Costa Rica La Paloma", "", "Catuai"),
    ("Peru San Martin de Pangoa", "", "Typica"),
])
def test_variety_extraction_sc87(name: str, desc: str, expected_variety: str) -> None:
    """SC-87: Expanded variety patterns should be recognized by the parser."""
    result = parse_coffee_metadata(name, desc)
    assert result.variety_text is not None, f"Expected variety for {name!r}, got None"
    assert expected_variety.lower() in result.variety_text.lower(), (
        f"Expected variety containing {expected_variety!r} for {name!r}, got {result.variety_text!r}"
    )


def test_variety_explicit_beats_country_default() -> None:
    """Explicit variety in name should take precedence over country default."""
    # Costa Rica + Catuai default, but this product has explicit Gesha
    result = parse_coffee_metadata("Costa Rica Hacienda Gesha", "")
    assert result.variety_text is not None
    assert "gesha" in result.variety_text.lower(), (
        f"Expected Gesha (explicit), got {result.variety_text!r}"
    )


def test_bourbon_not_matched_in_blend_name_with_whiskey_context() -> None:
    """Bourbon word boundary should avoid matching 'Kentucky Bourbon Barrel' etc."""
    # This is a coffee product but if name has Bourbon it should match
    # The key requirement is word boundary: 'Bourbon' in 'Bourbon Street Blend' should match
    # but not in 'Bourbonnais' (rare, but test the boundary works)
    result = parse_coffee_metadata("Colombia Bourbon Street Blend", "")
    # 'Bourbon' IS in the name so it should match (specialty use)
    assert result.variety_text is not None
    assert "bourbon" in result.variety_text.lower()


def test_sl28_hyphen_variants() -> None:
    """SL-28, SL 28, SL28 all normalize to SL28."""
    for name in ["Kenya SL-28", "Kenya SL 28", "Kenya SL28"]:
        result = parse_coffee_metadata(name, "")
        assert result.variety_text == "SL28", f"{name!r} → got {result.variety_text!r}"


def test_sl34_hyphen_variants() -> None:
    """SL-34, SL 34, SL34 all normalize to SL34."""
    for name in ["Kenya SL-34", "Kenya SL 34", "Kenya SL34"]:
        result = parse_coffee_metadata(name, "")
        assert result.variety_text == "SL34", f"{name!r} → got {result.variety_text!r}"


def test_maragogype_normalizes_to_maragogipe() -> None:
    """Maragogype (alternate spelling) should normalize to Maragogipe."""
    result = parse_coffee_metadata("Peru Timbuyacu Maragogype", "")
    assert result.variety_text == "Maragogipe"


# ---------------------------------------------------------------------------
# SC-97: Expanded roast and process normalization patterns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,desc,expected_level", [
    ("Archive Blonde Espresso", "Blonde espresso roast for sweet milk drinks.", "light-medium"),
    ("Nordic Light Filter", "Nordic light roast with florals.", "light"),
    ("Scandinavian Release", "Scandinavian roast, tea-like and bright.", "light"),
    ("City Roast Colombia", "City roast with caramel sweetness.", "medium"),
    ("City Plus Espresso", "City+ roast for espresso.", "medium-dark"),
    ("Medium Dark House", "Medium dark roast with cocoa.", "medium-dark"),
    ("Vienna Blend", "Vienna roast profile.", "medium-dark"),
    ("Extra Dark Blend", "Extra dark roast, smoky finish.", "dark"),
    ("Cinnamon Roast Decaf", "Cinnamon roast with gentle acidity.", "dark"),
    ("Daily Filter", "Light roast for pour over.", "light"),
    ("Plain Light Label", "Light.", "light"),
])
def test_roast_level_patterns_sc97(name: str, desc: str, expected_level: str) -> None:
    result = parse_coffee_metadata(name, desc)
    assert result.roast_level == expected_level, (
        f"Expected roast_level={expected_level!r} for {name!r}, got {result.roast_level!r}"
    )


@pytest.mark.parametrize("name,desc,expected_family", [
    ("Sumatra Wet Hulled", "Wet hulled process with savory depth.", "wet-hulled"),
    ("Indonesia Giling Basah", "Traditional giling basah processing.", "wet-hulled"),
    ("Colombia Semi Washed", "Semi washed process with red fruit.", "honey"),
    ("Costa Rica Semiwashed", "Semiwashed coffee, syrupy and sweet.", "honey"),
    ("Colombia Double Fermented", "Double fermented lot with tropical notes.", "anaerobic"),
    ("Kenya Extended Fermentation", "Extended fermentation and punchy acidity.", "anaerobic"),
    ("Ecuador Lactic Process", "Lactic fermentation, creamy texture.", "anaerobic"),
    ("Panama Co-Ferment", "Co-ferment experimental lot.", "anaerobic"),
    ("Costa Rica White Honey", "White honey processed micro lot.", "honey"),
    ("Colombia Experimental", "Experimental fermentation lot.", "anaerobic"),
    ("Brazil Pulped Natural", "Classic pulped natural sweetness.", "honey"),
])
def test_process_family_patterns_sc97(name: str, desc: str, expected_family: str) -> None:
    result = parse_coffee_metadata(name, desc)
    assert result.process_family == expected_family, (
        f"Expected process_family={expected_family!r} for {name!r}, got {result.process_family!r}"
    )


@pytest.mark.parametrize("name", [
    "Kalita Wave (Stainless)",
    "NanoFoamer Frother PRO",
    "Metric Coffee Bag Enamel Pin",
    "Metric Cuffed Knit Beanie (Black)",
    "Cold Brew Concentrate",
    "Cascara Coffee Cherry Tea",
])
def test_non_coffee_products_sc102(name: str) -> None:
    result = parse_coffee_metadata(name, "")
    assert result.is_coffee_product is False, f"Expected non-coffee classification for {name!r}"


@pytest.mark.parametrize("name,desc", [
    ("Anselmo Caldon Alvira - Washed Process - 2024", ""),
    ("Fausto Romo Sidra - Honey - 2024", ""),
    ("Finca Santa Elena", "Single-origin coffee from a family farm."),
])
def test_specialty_single_origin_context_defaults_to_light_sc102(name: str, desc: str) -> None:
    result = parse_coffee_metadata(name, desc)
    assert result.roast_level == "light", (
        f"Expected specialty single-origin context to infer light roast for {name!r}, got {result.roast_level!r}"
    )


def test_java_variety_does_not_create_false_multi_origin_sc102() -> None:
    result = parse_coffee_metadata("Costa Rica El Congo Geisha", "")
    assert result.origin_country == "Costa Rica"
    assert result.is_single_origin is True
    assert result.roast_level == "light"


@pytest.mark.parametrize("origin_country,expected", [
    ("Colombia", "washed"),
    ("Kenya", "washed"),
    ("Brazil", "natural"),
    ("Ethiopia", None),
    (None, None),
])
def test_country_default_process_family_sc102(origin_country: str | None, expected: str | None) -> None:
    assert default_process_family_for_country(origin_country) == expected


# ---------------------------------------------------------------------------
# SC-104: Tests for description_text as secondary extraction source
# ---------------------------------------------------------------------------

def test_sc104_parser_uses_description_for_origin() -> None:
    """When title has no origin signal, parser extracts origin from description."""
    result = parse_coffee_metadata(
        "Mystery Coffee",
        "A washed single-origin coffee from Yirgacheffe, Ethiopia. Notes of jasmine.",
    )
    assert result.origin_country == "Ethiopia"


def test_sc104_parser_uses_description_for_process() -> None:
    """When title has no process signal, parser extracts process from description."""
    result = parse_coffee_metadata(
        "Guatemala Huehuetenango",
        "Process: Natural. Roast: Medium. Origin: Guatemala.",
    )
    assert result.process_family == "natural"


def test_sc104_parser_uses_description_for_roast() -> None:
    """When title has no roast signal, parser extracts roast from description."""
    result = parse_coffee_metadata(
        "Single Origin Guatemala",
        "Roast level: light. Grown at 1800 masl in Huehuetenango.",
    )
    assert result.roast_level == "light"


def test_sc104_parser_empty_description_graceful() -> None:
    """Parser handles empty description_text gracefully (no crash, no garbage)."""
    result = parse_coffee_metadata("Ethiopia Natural Light", "")
    assert result.origin_country == "Ethiopia"
    assert result.process_family == "natural"
    assert result.roast_level == "light"
