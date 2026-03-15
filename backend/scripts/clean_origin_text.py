"""Clean up dirty origin_text values in the database."""
import sqlite3
import re

DB_PATH = "../data/szimplacoffee.db"

COUNTRIES = [
    "Ethiopia", "Kenya", "Colombia", "Guatemala", "Honduras", "Peru",
    "Brazil", "Costa Rica", "Panama", "Bolivia", "Mexico", "Indonesia",
    "Rwanda", "Burundi", "El Salvador", "Yemen", "Sumatra", "Java",
    "Hawaii", "PNG", "Tanzania", "Uganda", "Nicaragua", "Ecuador",
    "Dominican Republic", "Jamaica", "India", "Myanmar", "Laos", "Thailand",
    "Congo", "Malawi", "Zambia"
]

def clean_origin(text: str) -> str:
    if not text or text.strip() in (".", ":", ",", ""):
        return ""
    # If it's already clean (just a country/region name, <30 chars), keep it
    if len(text.strip()) < 30:
        cleaned = text.strip().strip(".,;: ")
        if cleaned:
            return cleaned
        return ""
    # Extract first country match from dirty text
    for country in COUNTRIES:
        if re.search(r'\b' + re.escape(country) + r'\b', text, re.IGNORECASE):
            return country
    # If no country found but text is long, it's garbage — clear it
    return ""

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT id, origin_text FROM products WHERE origin_text != ''")
rows = c.fetchall()

fixed = 0
cleared = 0
for row_id, origin in rows:
    cleaned = clean_origin(origin)
    if cleaned != origin:
        c.execute("UPDATE products SET origin_text = ? WHERE id = ?", (cleaned, row_id))
        if cleaned:
            fixed += 1
        else:
            cleared += 1

conn.commit()
print(f"Processed {len(rows)} products: {fixed} fixed, {cleared} cleared")
