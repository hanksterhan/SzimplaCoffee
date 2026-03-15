# 2026-03-15 Ticket Batch Checkpoint

## Source

- `.plans/next-steps-march15.md`

## Epics Created

1. Stabilization and package hygiene
2. Catalog truth and normalized metadata foundation
3. Server-side catalog querying
4. Historical deal intelligence
5. Recurring crawl scheduling
6. Crawl strategy layering and quality scoring
7. Daily utility views
8. Merchant registry and top-500 rollout policy

## Ticket IDs Created

- SC-44
- SC-45
- SC-46
- SC-47
- SC-48
- SC-49
- SC-50
- SC-51
- SC-52
- SC-53

## Primary Dependency Chains

- SC-44 -> SC-45 -> SC-48 -> SC-52
- SC-44 -> SC-46 -> SC-47 -> SC-48 -> SC-49 -> SC-52
- SC-44 -> SC-50 -> SC-49 -> SC-52
- SC-50 -> SC-51 -> SC-52 -> SC-53
- SC-47 + SC-48 + SC-49 + SC-50 + SC-51 + SC-52 -> SC-53

## Coverage Gaps Still Open

- Exact implementation approach for materialized deal facts versus on-demand SQLite queries
- Whether normalized metadata should live directly on Product or in a companion table
- How much scheduler state should be surfaced in UI versus backend-only operational views
