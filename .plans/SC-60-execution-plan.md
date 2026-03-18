# SC-60 Execution Plan

## Goal
After initial crawls, review crawl quality metrics and promote or demote merchants to appropriate tiers. Ensure high-quality merchants are in Tier A/B and poor performers are demoted to Tier D.

## Context
New merchants start at crawl_tier=B. After crawls, quality scorer can evaluate product richness, crawl success rate, and metadata fill. Tier A merchants get crawled every 6h; D are excluded from recommendations.

## Files / Areas Expected to Change
- `backend/src/szimplacoffee/services/quality_scorer.py` (may add auto-promote logic)

## Implementation Steps
1. Run quality scorer:
   ```bash
   cd backend && . .venv/bin/activate && szimpla score-merchants
   ```
2. Inspect merchant_quality_profiles table:
   ```bash
   cd backend && python -c "
   from szimplacoffee.db import engine
   from sqlalchemy import text
   rows = engine.connect().execute(text('SELECT merchant_id, overall_score, product_count FROM merchant_quality_profiles ORDER BY overall_score DESC')).fetchall()
   for r in rows: print(r)
   "
   ```
3. Define promotion criteria:
   - crawl_tier=A: overall_score >= 0.7 AND product_count >= 20
   - crawl_tier=B: overall_score >= 0.4 AND product_count >= 5
   - crawl_tier=D: product_count = 0 after 2+ crawl attempts
4. Apply tier changes via DB update or CLI
5. Consider adding auto-promote logic to quality_scorer.py if promotion rules are stable
6. Verify tier distribution post-update

## Risks / Notes
- quality_scorer.py fields may differ from assumed schema — inspect first
- Promotion should be conservative; prefer B over A until trust is established
- D tier exclusion has immediate recommendation impact

## Verification
```bash
cd backend && python -c "
from szimplacoffee.db import engine
from sqlalchemy import text
rows = engine.connect().execute(text(\"SELECT crawl_tier, COUNT(*) FROM merchants GROUP BY crawl_tier\")).fetchall()
for r in rows: print(r)
"
cd backend && . .venv/bin/activate && szimpla score-merchants 2>&1 | tail -10
```

## Out of Scope
- Changing quality scoring algorithm
- Fixing broken crawl adapters
