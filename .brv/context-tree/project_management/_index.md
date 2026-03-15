---
children_hash: d2d23f27a2fa7eaddc1521ecc1fa4ffc2441c3de16481d7c0573614df62671bd
compression_ratio: 0.8588235294117647
condensation_order: 2
covers: [context.md, sprints/_index.md]
covers_token_total: 510
summary_level: d2
token_count: 438
type: summary
---
# Domain: Project Management

## Structural Overview
The **project_management** domain (see `context.md`) serves as the central repository for sprint planning, retrospectives, and roadmap execution. It governs sprint goals, ticket prioritization, and velocity tracking, while delegating individual ticket details to the `.tickets/` directory.

## Sprint Execution & Strategy
The current operational focus, detailed in the **sprints** sub-domain (see `sprints/_index.md`), marks a strategic shift from UI development to establishing a robust data foundation.

### Sprint 2: Data Foundation & Planning
Current execution is prioritized around data quality to resolve critical gaps in the recommendation engine.
*   **Architectural Decision**: Data foundation tasks (Phases 2a-2b) must precede UI implementation (Phase 2c) and optimization (Phase 2d).
*   **Key Relationship**: The scoring engine effectiveness is directly blocked by poor product metadata.
*   **Status Metrics**: 
    *   **Metadata Gaps**: ~94% of recommendation metadata is currently empty.
    *   **Product Coverage**: Origin data exists for only 59/910 products; process data for 43/910.

### Resource & Task Mapping
*   **Scope**: Tasks SC-30 through SC-42 are dedicated to data foundation and metadata parsing.
*   **Artifacts**: Reference `.tickets/open/SC-30.yaml` through `SC-42.yaml` for execution details.

## Reference Entries for Drill-down
*   **sprints/sprint_2_planning.md**: Comprehensive gap analysis, four-phase execution breakdown (2a-2d), and granular metadata statistics.
*   **context.md**: Domain purpose, inclusion/exclusion rules, and high-level prioritization logic.
*   **sprints/_index.md**: Summary of sprint-level strategic shifts and resource allocation.