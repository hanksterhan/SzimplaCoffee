# SC-63: Improve coffee_parser process/roast patterns with implicit inference

**Date:** 2026-03-18
**Status:** Done

## What Changed

### coffee_parser.py
- Expanded `_ROAST_LIGHT` with: `lightly roasted`, `pour over roast`, `pourover roast`, `pour-over roast`, `light filter`
- Expanded `_ROAST_MEDIUM` with: `medium-light`, `medium light`, `all-rounder`, `everyday coffee`
- Expanded `_ROAST_DARK_ESPRESSO` with: `full city`, `full-city`, `vienna roast`
- Added `_DARK_ROAST_IMPLICIT_SIGNALS` constant list
- Added `_infer_roast_from_context(is_single_origin, is_blend, text)` — implicit inference function
- Updated `_normalize_roast_level` signature to accept `is_single_origin` and `is_blend` kwargs
- Updated `parse_coffee_metadata()` to pass those flags through

### Inference Logic (Key)
Single-origin specialty coffee → **light** (default for specialty roasters)
Blend → **medium-dark** (default for blends)
Dark/espresso implicit signals in text → **medium-dark**

### Tests
- Added 10 process family parametrized tests
- Added 12 roast level parametrized tests
- All 22 pass; full suite: 120 tests

## Fill Rates

| Metric | Before | After |
|--------|--------|-------|
| Roast fill | 11/597 (1.8%) | 367/597 (61.5%) |
| Process fill | 266/597 (44.6%) | 266/597 (44.6%) |

## Surprises

- Roast level was nearly empty (1.8%) because specialty coffee rarely writes "light roast" on product pages
- Implicit inference alone drove roast from 1.8% → ~60%
- Process 44.6% is a **data** limitation, not a parser gap — most products don't mention process in their copy
- 70% roast target not fully met (61.5%) — products without country/blend signals remain `unknown`

## Follow-ups
- SC-64: Dashboard fill rate metrics should reflect updated numbers
- Could further improve roast by scanning tasting notes for implicit cues (e.g., "blueberry, wine" → light; "chocolate, caramel" → medium)
- Process could be improved by sourcing from merchant metadata fields (separate from description)
