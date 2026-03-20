/**
 * Utility functions for product metadata display.
 * Canonical fields (origin_country, process_family, roast_level) are preferred
 * over raw free-text fields; "unknown" values are treated as absent (null).
 */

/** Minimal product shape accepted by buildTags. */
export interface ProductTagInput {
  product_category?: string | null;
  origin_text?: string | null;
  origin_country?: string | null;
  process_text?: string | null;
  process_family?: string | null;
  variety_text?: string | null;
  roast_cues?: string | null;
  roast_level?: string | null;
  tasting_notes_text?: string | null;
  is_single_origin?: boolean | null;
  is_espresso_recommended?: boolean | null;
}

/**
 * Convert a metadata string value to null if it is absent or the sentinel "unknown".
 * This prevents "unknown" from appearing as a visible tag or filter option.
 */
export function normalizedOrNull(value: string | null | undefined): string | null {
  if (!value || value === "unknown") return null;
  return value;
}

/**
 * Build a deduplicated array of visible metadata tags for a product.
 * - Prefers canonical normalized fields (origin_country, process_family, roast_level)
 *   over raw free-text fields (origin_text, process_text, roast_cues).
 * - Suppresses "unknown" values: no tag is emitted for unknown canonical fields.
 * - Never emits a tag for null, undefined, or empty strings.
 */
export function buildTags(product: ProductTagInput): string[] {
  const tags = [
    product.product_category,
    product.is_single_origin ? "single origin" : null,
    product.is_espresso_recommended ? "espresso" : null,
    // Prefer normalized canonical fields; fall back to raw text; suppress "unknown"
    normalizedOrNull(product.origin_country) ?? (product.origin_text || null),
    normalizedOrNull(product.process_family) ?? (product.process_text || null),
    product.variety_text || null,
    normalizedOrNull(product.roast_level) ?? (product.roast_cues || null),
  ].filter(Boolean) as string[];

  return Array.from(new Set(tags));
}
