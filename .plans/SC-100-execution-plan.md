# SC-100 Execution Plan — Add metadata fill-rate widget to dashboard

## Goal

Add a compact fill-rate widget to the React SPA dashboard page. Display
origin_pct, process_pct, roast_pct, and variety_pct from the existing
`/api/v1/dashboard/metrics` response with progress bars. No backend changes.

## Context

- `DashboardMetrics.metadata_fill_rates` already returns `{ origin_pct, process_pct, roast_pct, variety_pct, coffee_product_count }`.
- Frontend `useDashboard` hook (or equivalent) already fetches this endpoint.
- The React dashboard route is at `frontend/src/routes/index.lazy.tsx`.
- Existing dashboard cards use Tailwind utility classes for layout.
- The `goal.yaml` success criterion for origin_pct is ≥ 70%; show a goal marker.

## Files Expected to Change

**Frontend:**
- `frontend/src/components/MetadataFillRateWidget.tsx` — new component
- `frontend/src/routes/index.lazy.tsx` — add widget to dashboard layout

**Read-only reference:**
- `frontend/src/hooks/useDashboard.ts` (or wherever the dashboard query lives)
- `frontend/src/api/schema.d.ts`
- `frontend/src/components/` (existing cards for style reference)

## Implementation Steps

### S1 — Create MetadataFillRateWidget

1. Read `frontend/src/api/schema.d.ts` to confirm `MetadataFillRates` type shape.
2. Read existing dashboard hook to understand how `metadata_fill_rates` is accessed.
3. Create `frontend/src/components/MetadataFillRateWidget.tsx`:
   - Accept `fillRates: MetadataFillRates | undefined` as prop.
   - Render 4 rows: Origin, Process, Roast, Variety.
   - Each row: label + percentage value + a simple horizontal progress bar.
   - Origin row: show a "Goal: 70%" tick mark or annotation.
   - If `fillRates` is undefined/loading, render a skeleton or "--".
   - No new dependencies; use Tailwind for layout and color.
4. Color coding suggestion:
   - ≥ 70%: green
   - 40–69%: amber
   - < 40%: red
5. Show `coffee_product_count` as a footnote: "Based on {n} coffee products".

### S2 — Add widget to dashboard

1. Open `frontend/src/routes/index.lazy.tsx`.
2. Find where to add the widget — after or alongside existing metric cards.
3. Import `MetadataFillRateWidget` and pass `data?.metadata_fill_rates`.
4. Build: `cd frontend && npm run build`.
5. Type-check: `npx tsc -b`.

## Risks / Notes

- Keep the widget visually lightweight — it should not dominate the dashboard.
- The progress bar can be a simple `<div>` with `width: {pct}%` inside a gray track;
  no charting library needed.
- Handle `pct > 100` gracefully (cap display bar at 100%).
- Ensure the "Goal" marker for origin doesn't overflow or look broken at low values.

## Verification

```bash
cd frontend && npm run build
cd frontend && npx tsc -b
grep -rn 'metadata_fill_rates\|MetadataFillRateWidget' frontend/src/routes/ frontend/src/components/
```

## Out of Scope

- Historical chart
- Backend API changes
- Per-merchant fill-rate breakdown
- Automated alerts
