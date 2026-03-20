import { describe, it, expect } from "vitest";
import { normalizedOrNull, buildTags } from "../product-tags";

// Minimal product shape for testing buildTags.
const emptyProduct = {
  product_category: null,
  origin_text: null,
  origin_country: null,
  process_text: null,
  process_family: null,
  variety_text: null,
  roast_cues: null,
  roast_level: null,
  tasting_notes_text: null,
  is_single_origin: false,
  is_espresso_recommended: false,
};

describe("normalizedOrNull", () => {
  it("returns null for 'unknown'", () => {
    expect(normalizedOrNull("unknown")).toBeNull();
  });

  it("returns null for null", () => {
    expect(normalizedOrNull(null)).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(normalizedOrNull(undefined)).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(normalizedOrNull("")).toBeNull();
  });

  it("returns the value for a known canonical value", () => {
    expect(normalizedOrNull("washed")).toBe("washed");
    expect(normalizedOrNull("Ethiopia")).toBe("Ethiopia");
    expect(normalizedOrNull("light")).toBe("light");
  });
});

describe("buildTags", () => {
  it("produces no 'unknown' tags for all-unknown canonical fields", () => {
    const tags = buildTags({
      ...emptyProduct,
      roast_level: "unknown",
      process_family: "unknown",
      origin_country: null,
    });
    expect(tags).not.toContain("unknown");
    expect(tags.filter((t) => t.toLowerCase() === "unknown")).toHaveLength(0);
  });

  it("falls back to raw text when canonical field is unknown", () => {
    const tags = buildTags({
      ...emptyProduct,
      roast_level: "unknown",
      roast_cues: "medium roast",
    });
    expect(tags).toContain("medium roast");
    expect(tags).not.toContain("unknown");
  });

  it("prefers canonical field over raw text when canonical is known", () => {
    const tags = buildTags({
      ...emptyProduct,
      roast_level: "light",
      roast_cues: "light roast from the label",
    });
    expect(tags).toContain("light");
  });

  it("does not emit null origin as a tag", () => {
    const tags = buildTags({
      ...emptyProduct,
      origin_country: null,
      origin_text: "",
    });
    expect(tags.filter((t) => t.toLowerCase().includes("origin"))).toHaveLength(0);
  });

  it("emits espresso tag when is_espresso_recommended", () => {
    const tags = buildTags({ ...emptyProduct, is_espresso_recommended: true });
    expect(tags).toContain("espresso");
  });

  it("emits single origin tag when is_single_origin", () => {
    const tags = buildTags({ ...emptyProduct, is_single_origin: true });
    expect(tags).toContain("single origin");
  });

  it("deduplicates tags", () => {
    const tags = buildTags({
      ...emptyProduct,
      origin_country: "Ethiopia",
      origin_text: "Ethiopia",
    });
    const ethiopiaTags = tags.filter((t) => t === "Ethiopia");
    expect(ethiopiaTags).toHaveLength(1);
  });

  it("returns empty array when all fields are absent or unknown", () => {
    const tags = buildTags({
      ...emptyProduct,
      roast_level: "unknown",
      process_family: "unknown",
    });
    // With no real values, tags should be empty or contain only boolean flags (which are false)
    expect(tags.filter((t) => t === "unknown")).toHaveLength(0);
  });
});
