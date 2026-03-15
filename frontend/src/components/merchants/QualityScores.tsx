import type { components } from "@/api/schema";

type QualityProfile = components["schemas"]["MerchantQualityProfileSchema"];

interface QualityScoresProps {
  profile: QualityProfile;
}

const SCORE_FIELDS: { key: keyof QualityProfile; label: string }[] = [
  { key: "overall_quality_score", label: "Overall" },
  { key: "freshness_transparency_score", label: "Freshness" },
  { key: "shipping_clarity_score", label: "Shipping" },
  { key: "metadata_quality_score", label: "Metadata" },
  { key: "espresso_relevance_score", label: "Espresso" },
  { key: "service_confidence_score", label: "Service" },
];

function scoreColor(value: number): string {
  if (value >= 0.7) return "bg-green-500";
  if (value >= 0.4) return "bg-amber-500";
  return "bg-red-400";
}

export function QualityScores({ profile }: QualityScoresProps) {
  return (
    <div className="space-y-2">
      {SCORE_FIELDS.map(({ key, label }) => {
        const raw = profile[key];
        const value = typeof raw === "number" ? raw : 0;
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-20 shrink-0">
              {label}
            </span>
            <div className="flex-1 bg-muted rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${scoreColor(value)}`}
                style={{ width: `${Math.round(value * 100)}%` }}
              />
            </div>
            <span className="text-xs font-mono w-8 text-right">
              {Math.round(value * 100)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
