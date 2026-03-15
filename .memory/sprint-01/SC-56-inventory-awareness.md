# SC-56 Delivery Memory: Personal Inventory Awareness

## What Changed

- Added `current_inventory_grams: int = 0` to `RecommendationRequest` dataclass
- Updated `_quantity_score()` with inventory-aware penalties:
  - >= 2lb on hand → down-score bags > 18oz to 0.15
  - >= 1lb on hand → down-score bags > 2.5lb to 0.25
- Updated `build_wait_assessment()` to return "you have ~Xlb on hand" when >= 2lb
- Updated `today_buying_brief` and `create_recommendation` to accept `current_inventory_grams` as input
- Updated `TodayBriefOptions` and `useTodayBrief` hook with `current_inventory_grams` parameter
- Added inventory oz input field to Today page UI

## Design Choices

- 450g (~1lb) and 900g (~2lb) as soft thresholds match real coffee buying patterns
- Inventory is optional — 0 means "unknown," system works fine without it
- The Today page shows oz input (not grams) since that's more familiar for US coffee buyers

## Follow-ups

- Persist last-known inventory to PersonalProfile or a UserPreferences table
- Auto-deduct from purchases (approximate based on consumption rate)
- More sophisticated: ask "when did you open this bag?" to estimate remaining freshness
