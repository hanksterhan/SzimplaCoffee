/**
 * De1ShotChart.tsx
 * Beautiful shot profile visualizer for Decent DE1 espresso machine data.
 * Renders pressure, flow, weight, and temperature curves from a Visualizer shot.
 */

import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export interface De1ShotData {
  id: string;
  profile_title: string;
  bean_brand: string | null;
  bean_type: string | null;
  roast_level: string | null;
  roast_date: string | null;
  grinder_model: string | null;
  grinder_setting: string | null;
  bean_weight: string | null;
  drink_weight: string | null;
  duration: number;
  espresso_enjoyment?: number;
  start_time?: string;
  timeframe: string[];
  data: {
    espresso_pressure: string[];
    espresso_pressure_goal?: string[];
    espresso_flow: string[];
    espresso_flow_goal?: string[];
    espresso_weight: string[];
    espresso_temperature_mix: string[];
    espresso_temperature_goal?: string[];
    espresso_temperature_basket?: string[];
  };
}

interface ChartPoint {
  t: number;
  pressure: number | null;
  pressureGoal: number | null;
  flow: number | null;
  flowGoal: number | null;
  weight: number | null;
  tempMix: number | null;
  tempBasket: number | null;
}

function buildChartData(shot: De1ShotData): ChartPoint[] {
  const tf = shot.timeframe.map(Number);
  const p = shot.data.espresso_pressure.map(Number);
  const pg = shot.data.espresso_pressure_goal?.map(Number) ?? [];
  const f = shot.data.espresso_flow.map(Number);
  const fg = shot.data.espresso_flow_goal?.map(Number) ?? [];
  const w = shot.data.espresso_weight.map(Number);
  const tm = shot.data.espresso_temperature_mix.map(Number);
  const tb = shot.data.espresso_temperature_basket?.map(Number) ?? [];

  return tf.map((t, i) => ({
    t: Math.round(t * 10) / 10,
    pressure: p[i] ?? null,
    pressureGoal: pg[i] !== undefined && pg[i] > -1 ? pg[i] : null,
    flow: f[i] ?? null,
    flowGoal: fg[i] !== undefined && fg[i] > -1 ? fg[i] : null,
    weight: w[i] ?? null,
    tempMix: tm[i] ?? null,
    tempBasket: tb[i] ?? null,
  }));
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-xs text-zinc-400 uppercase tracking-wide font-medium">{label}</span>
      <span className="text-sm font-semibold text-zinc-100">{value}</span>
    </div>
  );
}

const COLORS = {
  pressure: "#e07b39",
  pressureGoal: "#e07b3955",
  flow: "#5b9bd5",
  flowGoal: "#5b9bd533",
  weight: "#6fcf97",
  tempMix: "#f2c94c",
  tempBasket: "#f2c94c55",
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: number;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-zinc-900/95 border border-zinc-700 rounded-lg p-3 text-xs shadow-xl min-w-32">
      <div className="text-zinc-400 mb-2 font-medium">{label?.toFixed(1)}s</div>
      {payload.map((p) => (
        <div key={p.name} className="flex justify-between gap-4 mb-0.5">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="text-zinc-200 font-mono tabular-nums">
            {p.value?.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  );
};

interface De1ShotChartProps {
  shot: De1ShotData;
  className?: string;
}

export function De1ShotChart({ shot, className = "" }: De1ShotChartProps) {
  const chartData = buildChartData(shot);

  const dose = shot.bean_weight ? `${parseFloat(shot.bean_weight).toFixed(1)}g` : "—";
  const yield_ = shot.drink_weight ? `${parseFloat(shot.drink_weight).toFixed(1)}g` : "—";
  const ratio =
    shot.bean_weight && shot.drink_weight
      ? `1:${(parseFloat(shot.drink_weight) / parseFloat(shot.bean_weight)).toFixed(1)}`
      : "—";
  const duration = `${shot.duration.toFixed(1)}s`;
  const peakPressure = Math.max(...chartData.map((d) => d.pressure ?? 0)).toFixed(1);

  const shotDate = shot.start_time
    ? new Date(shot.start_time).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div className={`bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 pt-6 pb-4 border-b border-zinc-800">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
                {shot.profile_title}
              </span>
              {shotDate && (
                <span className="text-xs text-zinc-600">· {shotDate}</span>
              )}
            </div>
            <h2 className="text-xl font-semibold text-white leading-tight">
              {shot.bean_brand ?? "Unknown Roaster"}
            </h2>
            {shot.bean_type && (
              <p className="text-sm text-zinc-400 mt-0.5">{shot.bean_type}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            {shot.roast_level && (
              <span className="text-xs bg-amber-900/40 text-amber-300 border border-amber-700/40 px-2 py-0.5 rounded-full capitalize">
                {shot.roast_level}
              </span>
            )}
            {shot.grinder_model && (
              <span className="text-xs text-zinc-500">
                {shot.grinder_model} @ {shot.grinder_setting}
              </span>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-zinc-800/60">
          <StatPill label="Dose" value={dose} />
          <div className="w-px h-8 bg-zinc-800" />
          <StatPill label="Yield" value={yield_} />
          <div className="w-px h-8 bg-zinc-800" />
          <StatPill label="Ratio" value={ratio} />
          <div className="w-px h-8 bg-zinc-800" />
          <StatPill label="Time" value={duration} />
          <div className="w-px h-8 bg-zinc-800" />
          <StatPill label="Peak Bar" value={`${peakPressure} bar`} />
        </div>
      </div>

      {/* Chart area */}
      <div className="px-2 py-6">
        {/* Pressure + Flow chart */}
        <div className="mb-1 px-4">
          <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
            Pressure & Flow
          </span>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={chartData} margin={{ top: 4, right: 24, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="t"
              type="number"
              domain={[0, "auto"]}
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickFormatter={(v) => `${v}s`}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="pressure"
              orientation="left"
              domain={[0, 12]}
              tick={{ fill: COLORS.pressure, fontSize: 11 }}
              tickFormatter={(v) => `${v}`}
              axisLine={false}
              tickLine={false}
              width={28}
            />
            <YAxis
              yAxisId="flow"
              orientation="right"
              domain={[0, 12]}
              tick={{ fill: COLORS.flow, fontSize: 11 }}
              tickFormatter={(v) => `${v}`}
              axisLine={false}
              tickLine={false}
              width={28}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              iconType="plainline"
              iconSize={16}
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
            />
            {/* Pressure goal */}
            <Area
              yAxisId="pressure"
              dataKey="pressureGoal"
              name="Pressure Goal"
              stroke={COLORS.pressureGoal}
              fill={COLORS.pressureGoal}
              dot={false}
              activeDot={false}
              strokeWidth={0}
              connectNulls
              legendType="none"
            />
            {/* Flow goal */}
            <Area
              yAxisId="flow"
              dataKey="flowGoal"
              name="Flow Goal"
              stroke={COLORS.flowGoal}
              fill={COLORS.flowGoal}
              dot={false}
              activeDot={false}
              strokeWidth={0}
              connectNulls
              legendType="none"
            />
            {/* Actual pressure */}
            <Line
              yAxisId="pressure"
              dataKey="pressure"
              name="Pressure (bar)"
              stroke={COLORS.pressure}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              connectNulls
            />
            {/* Actual flow */}
            <Line
              yAxisId="flow"
              dataKey="flow"
              name="Flow (ml/s)"
              stroke={COLORS.flow}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Weight + Temperature chart */}
        <div className="mt-4 mb-1 px-4">
          <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
            Weight & Temperature
          </span>
        </div>
        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart data={chartData} margin={{ top: 4, right: 24, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="t"
              type="number"
              domain={[0, "auto"]}
              tick={{ fill: "#71717a", fontSize: 11 }}
              tickFormatter={(v) => `${v}s`}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="weight"
              orientation="left"
              domain={[0, "auto"]}
              tick={{ fill: COLORS.weight, fontSize: 11 }}
              tickFormatter={(v) => `${v}g`}
              axisLine={false}
              tickLine={false}
              width={36}
            />
            <YAxis
              yAxisId="temp"
              orientation="right"
              domain={["auto", "auto"]}
              tick={{ fill: COLORS.tempMix, fontSize: 11 }}
              tickFormatter={(v) => `${v}°`}
              axisLine={false}
              tickLine={false}
              width={36}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              iconType="plainline"
              iconSize={16}
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
            />
            <Line
              yAxisId="weight"
              dataKey="weight"
              name="Weight (g)"
              stroke={COLORS.weight}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              connectNulls
            />
            <Line
              yAxisId="temp"
              dataKey="tempMix"
              name="Temp Mix (°C)"
              stroke={COLORS.tempMix}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              connectNulls
            />
            {shot.data.espresso_temperature_basket && (
              <Line
                yAxisId="temp"
                dataKey="tempBasket"
                name="Temp Basket (°C)"
                stroke={COLORS.tempBasket}
                strokeWidth={1.5}
                strokeDasharray="4 2"
                dot={false}
                activeDot={false}
                connectNulls
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Footer */}
      {shot.roast_date && (
        <div className="px-6 pb-4 flex items-center gap-1 text-xs text-zinc-600">
          <span>Roasted</span>
          <span className="text-zinc-500">{shot.roast_date}</span>
        </div>
      )}
    </div>
  );
}
