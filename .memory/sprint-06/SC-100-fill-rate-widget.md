# SC-100: Metadata Fill-Rate Widget

## What Changed

Created `frontend/src/components/MetadataFillRateWidget.tsx` — a reusable component that
renders origin, process, roast, and variety fill-rate rows as colored horizontal progress
bars with a 70% goal marker on the Origin row.

Refactored `frontend/src/components/dashboard/MetadataFillRate.tsx` to compose the new
widget, replacing the previous badge-only row layout.

## Why

The dashboard already computed metadata fill rates via the backend API but only displayed
them as inline percentage badges. After SC-97 expanded parser patterns, there was no at-a-
glance way to see coverage progress. The progress bar layout makes fill-rate trends
immediately readable and surfaces the 70% origin goal (a goal.yaml success criterion).

## Key Decisions

- **Reusable widget vs inline card**: Created `MetadataFillRateWidget` as a standalone
  composable component (per ticket spec) and wired it into the existing `MetadataFillRate`
  card. This lets the widget appear elsewhere (e.g. product detail) if needed later.
- **Color thresholds**: green ≥70%, amber ≥40%, red <40%. Amber band chosen as "working
  toward goal" rather than "bad" for process/roast/variety which naturally trail origin.
- **Goal marker**: Blue tick at 70% on origin row only (matches goal.yaml). Not applied to
  other fields since their targets aren't defined in the goal.
- **Fallback**: Dashboard card retains backward-compatible fallback to raw product counts
  when `metadata_fill_rates` is absent from the API response.
- **No new dependencies**: Pure Tailwind utility classes; no charting lib needed.

## Verification

- `npm run build` ✅ (4.08s, no errors)
- `npx tsc -b` ✅ (no output = clean)
- Grep confirms `metadata_fill_rates` wired in routes and components

## Follow-ups

- Historical fill-rate chart is scope-out; would need a time-series endpoint.
- Per-merchant fill-rate breakdown is a separate future ticket.
- SC-98 (deal baselines) is next — requires a running backend for `gen:api`.
