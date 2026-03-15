---
children_hash: 0e72425d33366f609cdbbccf3340b3308dff89e196e00a4fa19d4ed9d0223b8c
compression_ratio: 0.753061224489796
condensation_order: 1
covers: [context.md, sprint_2_planning.md]
covers_token_total: 490
summary_level: d1
token_count: 369
type: summary
---
# Domain: Project Management - Sprints

## Structural Overview
The **sprints** domain defines the execution phases, prioritization logic, and resource allocation for the SzimplaCoffee project. Current focus is centered on the transition from initial setup to a data-driven foundation.

## Sprint 2: Data Foundation & Planning
Strategic priority has shifted from UI polish to data quality, driven by a critical gap analysis of the recommendation engine.

### Key Decisions & Phasing
- **Prioritization Logic**: Data quality takes precedence over frontend features.
- **Execution Phases**:
    - **2a (Data)**: Foundation and metadata parsing.
    - **2b (Feedback)**: User feedback loops.
    - **2c (Catalog)**: UI implementation.
    - **2d (Engineering)**: Excellence and optimization.
- **Critical Relationship**: The scoring engine is currently "starving for data"; effectiveness is blocked by poor product metadata.

### Technical Debt & Metrics
- **Metadata Gaps**: 93-95% of recommendation metadata is empty.
- **Product Coverage**: Only 59/910 products have origin data; 43/910 have process data.

### Resource Mapping
- **Tickets**: SC-30 through SC-42 (Data foundation and metadata tasks).
- **Files**: `.tickets/open/SC-30.yaml` to `.tickets/open/SC-42.yaml`.

## Reference Entries
- **sprint_2_planning.md**: Detailed gap analysis, phase definitions (2a-2d), and specific metadata statistics.
- **context.md**: High-level sprint phasing and prioritization concepts.