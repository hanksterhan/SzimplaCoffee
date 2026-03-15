# ☕ SzimplaCoffee

A local-first coffee sourcing and recommendation platform for home espresso enthusiasts.

SzimplaCoffee answers one question with high confidence: **"What coffee should I order right now, from which merchant, in what size, and why?"**

## What It Does

- 🏪 **Tracks 16+ specialty coffee merchants** (Shopify, WooCommerce, custom) with automated crawling
- 📦 **Catalogs 900+ products** with origin, process, variety, and tasting note extraction
- 🎯 **Personalized recommendations** based on your espresso setup, shot style, bag size, and purchase history
- 💰 **Price-aware** — tracks offers, promos, shipping thresholds, and subscription discounts
- 🔍 **Discovers new merchants** via search-result harvesting with promote/reject review flow
- 🛒 **Learning loop** — log purchases, rate brews, and recommendations improve over time

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TanStack Router, TanStack Query, Tailwind CSS v4 |
| UI | shadcn/ui with coffee-themed design tokens |
| Charts | Recharts |
| Backend | Python 3.12+, FastAPI |
| Data | SQLAlchemy 2, SQLite (WAL mode) |
| Crawling | Adapter-based (Shopify, WooCommerce, static HTML) |

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Node.js 20+** (22 recommended)
- **npm 10+**
- **uv** (optional, for faster Python package management): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## First Time Setup

```bash
# Clone the repo
git clone https://github.com/hanksterhan/SzimplaCoffee.git
cd SzimplaCoffee

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -e .
cd ..

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..
```

## Running the App

### Production Mode (single port)

```bash
source .venv/bin/activate
cd backend
uvicorn szimplacoffee.main:app --port 8000
```

Open **http://localhost:8000** — FastAPI serves the React frontend and API on one port.

### Development Mode (hot reload)

```bash
# Terminal 1: Backend with auto-reload
source .venv/bin/activate
cd backend
uvicorn szimplacoffee.main:app --reload --port 8000

# Terminal 2: Frontend with hot module replacement
cd frontend
npm run dev
```

Open **http://localhost:5173** — Vite dev server proxies `/api/*` to the backend.

### One-Command Dev (both servers)

```bash
bash scripts/dev.sh
```

## Project Structure

The canonical backend package root is `backend/src/szimplacoffee`. The repository-root `src/` directory is not part of the runtime package layout and should be treated as stray local artifact space only.

```
SzimplaCoffee/
├── backend/                 # Python FastAPI backend
│   ├── src/szimplacoffee/
│   │   ├── api/             # JSON API routes (/api/v1/*)
│   │   ├── schemas/         # Pydantic response models
│   │   ├── services/        # Crawlers, recommendations, discovery, parser
│   │   ├── models.py        # SQLAlchemy models (15 tables)
│   │   ├── main.py          # FastAPI app + SPA serving
│   │   └── config.py        # Configuration
│   └── pyproject.toml
│
├── frontend/                # React SPA
│   ├── src/
│   │   ├── routes/          # TanStack Router file-based routes
│   │   ├── components/      # UI components (shadcn/ui + domain)
│   │   ├── hooks/           # TanStack Query hooks
│   │   ├── api/             # Typed API client (generated from OpenAPI)
│   │   └── lib/             # Utilities
│   ├── package.json
│   └── vite.config.ts
│
├── data/                    # SQLite database
│   └── szimplacoffee.db
│
├── scripts/
│   ├── dev.sh               # Start both servers
│   ├── build.sh             # Production build
│   └── generate-api-types.sh # Regenerate TypeScript types from API
│
├── SzimplaCoffee/brain/     # Second brain (decisions, research, worklogs)
├── .tickets/                # Local ticket system (YAML-based)
├── .plans/                  # Execution plans per ticket
├── .memory/                 # Delivery memory and sprint notes
│
├── north-star.md            # Product vision
├── comprehensive-plan.md    # Architecture and execution plan
└── CLAUDE.md                # Agent instructions
```

## Pages

| Page | Path | Description |
|------|------|-------------|
| Dashboard | `/` | Metrics overview, merchant table, crawl status |
| Merchants | `/merchants` | Filterable merchant list with trust/tier badges |
| Merchant Detail | `/merchants/:id` | Products, crawl runs, promos (tabbed) |
| Add Merchant | `/merchants/new` | URL input with platform auto-detection |
| Products | `/products` | Searchable product catalog with cards |
| Product Detail | `/products/:id` | Variants, price chart, buy link |
| Recommendations | `/recommend` | Shot style + bag size → scored results |
| Discovery | `/discovery` | Candidate review with promote/reject |
| Purchases | `/purchases` | Purchase history + brew feedback |

**⌘K** (or Ctrl+K) opens the command palette for quick navigation.

## API

The backend exposes a full REST API at `/api/v1/`. Interactive docs available at:
- **http://localhost:8000/docs** (Swagger UI)
- **http://localhost:8000/redoc** (ReDoc)

### Regenerate TypeScript Types

When the API changes, regenerate the frontend types:

```bash
# Start the backend first, then:
bash scripts/generate-api-types.sh
```

## Data

The SQLite database ships with real data:
- **16 merchants** — Olympia Coffee, Camber, SEY, Counter Culture, Onyx, and more
- **910 products** with parsed origins, processes, and varieties
- **3,207 variants** across common sizes (12oz, 2lb, 5lb)
- **9,352 offer snapshots** with pricing history
- **Auto-generated quality profiles** for all merchants

## Espresso Context

SzimplaCoffee is built for a user with:
- Decent DE1 XL Pro
- Timemore Sculptor 078S grinder
- 58mm and 49mm baskets (sworksdesign)
- Interest in modern espresso, lever shots, turbo shots, and experimental techniques

Recommendations factor in shot style, equipment compatibility, and personal brewing history.

## Coffee Recommendation Engine

The recommendation engine uses weighted scoring across 8 dimensions:
- `merchant_trust_score` — trust tier + quality profile
- `personal_history_score` — prior purchases and brew feedback
- `coffee_fit_score` — origin/process/variety match to preferences
- `espresso_style_fit_score` — compatibility with selected shot style
- `freshness_confidence_score` — roast date signals and crawl recency
- `delivery_confidence_score` — shipping clarity and estimated delivery
- `deal_score` — current price vs. history, promos, bulk value
- `inventory_fit_score` — bag size match to requested quantity

## Contributing

This is a personal tool, but the architecture supports extension. Key conventions:
- Canonical backend package root: `backend/src/szimplacoffee`
- Backend lint: `cd backend && ruff check src/`
- Frontend typecheck: `cd frontend && npx tsc -b`
- Frontend build: `cd frontend && npm run build`
- Tickets: `.tickets/open/` (YAML schema-validated)
- Decisions: `SzimplaCoffee/brain/decisions/` (ADR format)

---

*Built with ❤️ and ☕ by [h6nk-bot](https://github.com/h6nk-bot) — an agentic engineering system powered by [OpenClaw](https://github.com/openclaw/openclaw)*
