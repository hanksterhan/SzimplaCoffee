# SC-82 — Watch-page crawl status badges

## What changed
- Added local crawl-status classification to `frontend/src/routes/watch.lazy.tsx` using the existing `last_crawl_at`, `crawl_success`, and `crawl_tier` merchant fields already returned by the API.
- Rendered row-level badges for the three operator-facing states in scope: never crawled, last crawl failed, and stale.
- Added short helper copy in the merchant metadata row so stale and failed states are explainable at a glance without opening merchant detail.

## Why it changed
SC-74 exposed crawl health data, but the Watch page still made operators interpret timestamps manually. This ticket turns those fields into explicit review signals so the queue is easier to triage.

## Verification
- `cd frontend && npm run build`

## Notes / sharp edges
- Stale thresholds mirror the backend scheduler tiers locally in the route (`A=6h`, `B=24h`, `C=168h`, `D=manual/no stale badge`) to avoid backend changes.
- Failed status takes precedence over stale so a merchant with a recent failed crawl is still clearly called out as failed.
