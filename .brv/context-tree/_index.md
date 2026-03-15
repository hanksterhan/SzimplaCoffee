---
children_hash: f41195845ab2c5b70b1a23c5548343f571e28236fa77f613ec28805d8f113a37
compression_ratio: 0.8508946322067594
condensation_order: 3
covers: [project_management/_index.md]
covers_token_total: 503
summary_level: d3
token_count: 428
type: summary
---
# Project Management: Structural Summary (Level d3)

## Domain Overview
The **project_management** domain (see `context.md`) serves as the central repository for sprint planning, retrospectives, and roadmap execution. It governs sprint goals, ticket prioritization, and velocity tracking, while delegating individual ticket details to the `.tickets/` directory.

## Strategic Shift: Data Foundation
The current operational focus, detailed in the **sprints** sub-domain (see `sprints/_index.md`), marks a strategic shift from UI development to establishing a robust data foundation.

### Sprint 2: Data Quality & Execution
Current execution is prioritized around data quality to resolve critical gaps in the recommendation engine.
*   **Architectural Decision**: Data foundation tasks (Phases 2a-2b) must precede UI implementation (Phase 2c) and optimization (Phase 2d).
*   **Critical Dependency**: Scoring engine effectiveness is directly blocked by poor product metadata.
*   **Metadata Status**: ~94% of recommendation metadata is currently empty; origin data exists for 59/910 products, and process data for 43/910.

### Resource Allocation
*   **Task Mapping**: Tasks **SC-30** through **SC-42** are dedicated to data foundation and metadata parsing.
*   **Execution Details**: Reference `.tickets/open/SC-30.yaml` through `SC-42.yaml`.

## Reference Entries for Drill-down
*   **sprints/sprint_2_planning.md**: Comprehensive gap analysis, four-phase execution breakdown (2a-2d), and granular metadata statistics.
*   **context.md**: Domain purpose, inclusion/exclusion rules, and high-level prioritization logic.
*   **sprints/_index.md**: Summary of sprint-level strategic shifts and resource allocation.