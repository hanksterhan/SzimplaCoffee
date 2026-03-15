# SzimplaCoffee Agent Instructions

## What This Is

SzimplaCoffee is a local-first coffee sourcing and recommendation platform. It answers: **"What coffee should I order right now, from which merchant, in what size, and why?"**

Read `north-star.md` for product vision. Read `comprehensive-plan.md` for architecture and execution plan.

Use this file as the primary instruction file for agentic coding work in this repository.

## Tech Stack

- **Backend:** Python 3.12+ / FastAPI / Jinja2 / HTMX
- **Data:** SQLite + WAL + FTS5 / SQLAlchemy 2 / Alembic
- **Crawling:** Crawlee for Python (BeautifulSoup → Adaptive Playwright → full browser fallback)
- **Scheduling:** APScheduler
- **Tooling:** uv, ruff, pytest
- **CLI:** `szimpla` entrypoint via `backend/src/szimplacoffee/cli.py`

## Project Layout

```
backend/                 # Python backend (FastAPI)
  pyproject.toml         # Python project config
  src/szimplacoffee/     # Application source
    main.py              # FastAPI app + routes
    cli.py               # CLI entrypoint
    config.py            # Configuration
    db.py                # SQLAlchemy engine/session
    models.py            # SQLAlchemy models
    bootstrap.py         # Seed data
    services/
      crawlers.py        # Adapter-based crawling
      discovery.py       # Merchant discovery
      platforms.py       # Platform detection
      recommendations.py # Scoring engine
    templates/           # Jinja2 templates
    static/              # CSS/JS
  tests/                 # pytest tests
frontend/                # Frontend scaffold / SPA
data/                    # Shared data (DB lives here)
  szimplacoffee.db       # SQLite database
scripts/
  dev.sh                 # Start dev environment
SzimplaCoffee/           # Second brain (see below)
north-star.md            # Product vision (read-only reference)
comprehensive-plan.md    # Architecture plan (read-only reference)
```

## Agent Working Rules

- Read this file first when starting work in the repo.
- Prefer small, reviewable changes over wide refactors.
- Preserve existing architecture unless the ticket or plan explicitly calls for a change.
- Keep backend, frontend, tickets, plans, and memory in sync when work crosses those boundaries.
- Do not invent workflows when the repo already defines one in `.tickets/`, `.plans/`, `.memory/`, or `SzimplaCoffee/brain/`.
- Before changing behavior, inspect the nearest related files, tests, and current patterns.
- When fixing bugs, prefer the smallest correct fix plus tests or explicit verification notes.
- When adding features, follow the current naming, typing, query, and folder conventions instead of introducing parallel patterns.
- Prefer extending existing hooks, schemas, routes, and services before creating new abstractions.
- Keep generated or derived artifacts in sync when API contracts change.

## Repo-Specific Implementation Guidance

### Backend

- Keep FastAPI route contracts, Pydantic schemas, and SQLAlchemy queries aligned.
- Prefer explicit response models and predictable query semantics.
- Treat `offer_snapshots` and historical pricing/promo data as append-only time-series.
- Avoid hidden behavior changes in recommendation logic; preserve quality-first ranking intent.

### Frontend

- Follow existing TanStack/React Query patterns for data fetching and caching.
- Reuse shared hooks before adding route-local fetch logic.
- Keep filter state, pagination/cursor state, and UI loading states explicit.
- When backend response shapes change, update affected frontend types and usage together.

### Tickets, Plans, and Memory

- Delivery work should map to a ticket when the change is non-trivial.
- Every implementation ticket should have a matching execution plan.
- Capture learnings that matter in delivery memory, not just in commit history.

## Conventions

- **Crawler order:** API → static HTML → adaptive browser → full browser. Never default to browser.
- **Snapshots over overwrites:** Price/promo data is append-only time-series. Don't mutate offer_snapshots.
- **Quality > price:** Recommendations optimize for best buy above a quality threshold, not lowest price.
- **Espresso-aware:** Shot style (58mm modern, 49mm lever, turbo, experimental) changes recommendation ranking.
- **Bag size matters:** 12-18oz vs 2lb vs 5lb is a first-class recommendation dimension.

## Commands

```bash
# Run the web app (from backend/)
cd backend && uvicorn szimplacoffee.main:app --reload

# Or use dev script
./scripts/dev.sh

# Run CLI (from backend/)
cd backend && szimpla merchant add <url>
cd backend && szimpla crawl merchant <id>
cd backend && szimpla recommend

# Tests (from backend/)
cd backend && pytest tests/

# Lint (from backend/)
cd backend && ruff check src/ tests/
```

## Agentic Engineering Pipeline

SzimplaCoffee uses a structured local ticketing + plans + memory system for all delivery work.

### /brainstorm → /create-tickets → /deliver

1. **Brainstorm:** Identify work from `brain/backlog/now-next-later.md` or new requirements. Think through scope, dependencies, and acceptance criteria.
2. **Create tickets:** Write YAML tickets to `.tickets/open/SC-N.yaml` following the schema at `.tickets/schema/ticket.schema.json`. Create matching execution plan at `.plans/SC-N-execution-plan.md`.
3. **Deliver:** Implement the ticket slice by slice. Transition status fields as work progresses. Write delivery memory to `.memory/sprint-NN/`.

### Local Ticketing (`.tickets/`)

```
.tickets/
├── open/        # Active tickets (SC-N.yaml)
├── closed/      # Done or cancelled tickets
├── events/      # Append-only transition log
├── schema/      # ticket.schema.json + state-machine.yaml
└── templates/   # ticket-template.yaml
```

**Ticket lifecycle:** `draft → ready → in_progress → verifying → done`

**To read a ticket:** `cat .tickets/open/SC-N.yaml`

**To create a ticket:**
1. Copy `.tickets/templates/ticket-template.yaml` to `.tickets/open/SC-N.yaml`
2. Fill all required fields (`id`, `title`, `type`, `priority`, `status`, `owner`, `problem`, `desired_outcome`, `scope_in`, `scope_out`, `acceptance_criteria`, `verification_required`, `slices`, `delivery`)
3. Create matching plan at `.plans/SC-N-execution-plan.md`

**To transition a ticket:**
1. Update `status` field in the YAML
2. Meet guards in `.tickets/schema/state-machine.yaml`
3. Append event to `.tickets/events/SC-N.log`: `2026-03-14T15:00:00Z  draft → ready  owner=h6nk-bot`

**To close a ticket:** Move YAML from `open/` to `closed/` after setting `status: done`.

**Ticket prefix:** `SC-` (e.g., SC-1, SC-12)

**Ticket owner:** `h6nk-bot`

## How to Write Tickets, Plans, and Delivery Memory

### Ticket Writing

- Write tickets as clear problem statements, not vague feature labels.
- Keep `scope_in` and `scope_out` explicit so changes do not sprawl.
- Make acceptance criteria observable and verifiable.
- Break work into slices that can be delivered incrementally.
- Reference related plans, memory, or architectural context in `context_refs`.

### Plan Writing

Create a matching plan at `.plans/SC-N-execution-plan.md`.

A good plan should:
- Restate the goal and constraints briefly.
- Name the files and systems expected to change.
- Break implementation into ordered steps.
- Call out risk areas, migrations, contract changes, or validation needs.
- Define how the work will be verified.

Recommended structure:

```md
# SC-N Execution Plan

## Goal

## Context

## Files / Areas Expected to Change

## Implementation Steps

## Risks / Notes

## Verification

## Out of Scope
```

### Delivery Memory Writing

After meaningful delivery work or an important discovery:
- Write `.memory/sprint-NN/SC-N-<slug>.md`
- Update `.memory/index.json`

Memory should capture:
- what changed
- why it changed
- surprises or failed approaches
- follow-ups or sharp edges
- anything future agents should know that git diff alone will not explain

## Execution Plans (`.plans/`)

Each ticket has a corresponding execution plan:

```
.plans/SC-N-execution-plan.md
```

Plans describe the *how* (implementation steps, files, checks) while tickets define the *what* and *why*. Reference the plan from the ticket's `context_refs` field.

See `.plans/README.md` for plan structure.

## Delivery Memory (`.memory/`)

After completing a ticket or discovering something important during implementation:
1. Write a memory file: `.memory/sprint-NN/SC-N-<slug>.md`
2. Update `.memory/index.json` to add the entry

Memory captures what was learned, what failed, and what to remember — beyond what git history shows.

See `.memory/README.md` for format and rules.

## Brain Protocol

After any meaningful work session:
1. Update `SzimplaCoffee/brain/worklog/YYYY-MM-DD-<slug>.md`
2. Update `SzimplaCoffee/brain/backlog/now-next-later.md`
3. If an architecture decision was made, create `SzimplaCoffee/brain/decisions/NNN-<title>.md`
4. If merchant-specific intel was gathered, update `SzimplaCoffee/brain/merchant-intel/<merchant>.md`

## Current State (as of 2026-03-08)

- 5 merchants, 111 products, 351 variants, 1451 offer snapshots
- Shopify + WooCommerce adapters working
- Recommendation engine functional with weighted scoring
- Web UI renders dashboard, merchant detail, discovery, recommendations
- Notion import is seeded, not fully integrated
- Browser fallback not wired up yet
- Promo false-positive suppression needs improvement
