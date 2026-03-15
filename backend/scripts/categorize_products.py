"""Categorize all products based on name patterns."""
import sqlite3
import re

DB_PATH = "../data/szimplacoffee.db"

# First add the column if it doesn't exist
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
try:
    c.execute("ALTER TABLE products ADD COLUMN product_category TEXT DEFAULT 'coffee'")
    conn.commit()
    print("Added product_category column")
except:
    print("Column already exists")

RULES = [
    # (category, patterns) — order matters, first match wins
    ("gift", [r"gift", r"subscription", r"pre-?paid"]),
    ("instant", [r"instant"]),
    ("cold_brew", [r"cold.?brew", r"concentrate"]),
    ("merch", [
        r"\btee\b", r"\bshirt", r"hoodie", r"beanie", r"\bhat\b", r"tote",
        r"sticker", r"candle", r"\bpin\b", r"poster", r"mug\b", r"tumbler",
        r"\bbib\b", r"magnet", r"patch\b", r"keychain", r"apron",
        r"honey\b", r"syrup",
    ]),
    ("equipment", [
        r"dripper", r"grinder", r"brewer", r"kettle", r"scale", r"chemex",
        r"aeropress", r"filter paper", r"v60", r"espresso machine",
        r"glass straw", r"straw", r"coffee mill", r"mill\b", r"tamper",
        r"frother", r"frothing", r"funnel", r"disc\b", r"puck screen",
        r"espresso tool", r"scoop", r"dosing", r"wdt", r"distribution",
        r"portafilter", r"basket\b", r"shower screen", r"group head",
        r"knock box", r"milk pitcher", r"pitcher\b",
        r"mineral packet", r"mineral", r"water filter",
        r"extraction", r"espresso series",
    ]),
    ("tea", [r"\btea\b", r"\bchai\b", r"chocolate box", r"cocoa"]),
]

c.execute("SELECT id, name FROM products")
rows = c.fetchall()

stats = {}
for row_id, name in rows:
    category = "coffee"  # default
    name_lower = name.lower()
    for cat, patterns in RULES:
        if any(re.search(p, name_lower) for p in patterns):
            category = cat
            break
    c.execute("UPDATE products SET product_category = ? WHERE id = ?", (category, row_id))
    stats[category] = stats.get(category, 0) + 1

conn.commit()
print("Categorization complete:")
for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")
