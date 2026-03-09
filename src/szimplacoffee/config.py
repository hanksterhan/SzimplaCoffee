from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src" / "szimplacoffee"
TEMPLATES_DIR = SRC_DIR / "templates"
STATIC_DIR = SRC_DIR / "static"
DB_PATH = ROOT_DIR / "szimplacoffee.db"
DEFAULT_USER_NAME = "Henry"

