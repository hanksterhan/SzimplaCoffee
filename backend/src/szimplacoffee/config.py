from __future__ import annotations

import os
from pathlib import Path


# backend/ dir (parents[2] = backend/, parents[3] = repo root)
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

SRC_DIR = BACKEND_DIR / "src" / "szimplacoffee"
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = SRC_DIR / "static"

# DB lives in data/ at repo root; override with DATABASE_URL env var
_default_db = REPO_ROOT / "data" / "szimplacoffee.db"
DB_PATH = Path(os.environ.get("DATABASE_PATH", str(_default_db)))

DEFAULT_USER_NAME = "Henry"

# DE1 Visualizer bridge (SC-79)
VISUALIZER_USERNAME: str = os.environ.get("VISUALIZER_USERNAME", "h6nk")
VISUALIZER_API_KEY: str = os.environ.get("VISUALIZER_API_KEY", "")
DE1_AUTO_MATCH: bool = os.environ.get("DE1_AUTO_MATCH", "true").lower() == "true"
DE1_DEFAULT_DOSE_GRAMS: int = int(os.environ.get("DE1_DEFAULT_DOSE_GRAMS", "18"))
