"use client";

import { formatMoney } from "@/lib/api/portfolio";

type AllocationSlice = {
  currency_code: string;
  weight_percent: number;
  usd_value: number;
};

const COLORS: Record<string, string> = {
  USD: "#22c55e",
  EUR: "#60a5fa",
  JPY: "#f59e0b",
  GBP: "#f472b6",
  CNY: "#a78bfa",
  SGD: "#34d399",
};

function polarToCartesian(cx: number, cy: number, radius: number, angle: number) {
  return {
    x: cx + radius * Math.cos((angle - 90) * (Math.PI / 180)),
    y: cy + radius * Math.sin((angle - 90) * (Math.PI / 180)),
  };
}

function donutArcPath(
  cx: number,
  cy: number,
  outerRadius: number,
  innerRadius: number,
  startAngle: number,
  endAngle: number,
): string {
  const outerStart = polarToCartesian(cx, cy, outerRadius, startAngle);
  const outerEnd = polarToCartesian(cx, cy, outerRadius, endAngle);
  const innerStart = polarToCartesian(cx, cy, innerRadius, endAngle);
  const innerEnd = polarToCartesian(cx, cy, innerRadius, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerStart.x} ${innerStart.y}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerEnd.x} ${innerEnd.y}`,
    "Z",
  ].join(" ");
}

export function AllocationPieChart({
  title,
  totalUsd,
  slices,
  baseCurrency = "USD",
}: {
  title: string;
  totalUsd: number;
  slices: AllocationSlice[];
  baseCurrency?: string;
}) {
  const positiveSlices = slices.filter((slice) => slice.weight_percent > 0);
  let cursor = 0;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <p className="text-xs uppercase tracking-wider text-zinc-500">{title}</p>
      <div className="mt-4 flex flex-col items-center gap-3 lg:flex-row lg:items-start">
        <svg viewBox="0 0 220 220" className="h-56 w-56">
          {positiveSlices.map((slice) => {
            const sweep = (slice.weight_percent / 100) * 360;
            const path = donutArcPath(110, 110, 100, 60, cursor, cursor + sweep);
            cursor += sweep;
            return (
              <path key={slice.currency_code} d={path} fill={COLORS[slice.currency_code] ?? "#94a3b8"}>
                <title>
                  {slice.currency_code} · {slice.weight_percent.toFixed(1)}% ·{" "}
                  {formatMoney(slice.usd_value, baseCurrency)}
                </title>
              </path>
            );
          })}
          <circle cx="110" cy="110" r="52" fill="#09090b" />
          <text x="110" y="100" textAnchor="middle" className="fill-zinc-500 text-[10px]">
            Total
          </text>
          <text x="110" y="120" textAnchor="middle" className="fill-emerald-400 text-[12px] font-semibold">
            {formatMoney(totalUsd, baseCurrency)}
          </text>
        </svg>

        <div className="w-full space-y-1 text-sm">
          {positiveSlices.map((slice) => (
            <div key={slice.currency_code} className="flex items-center justify-between text-zinc-300">
              <span className="font-mono">{slice.currency_code}</span>
              <span>
                {slice.weight_percent.toFixed(1)}% · {formatMoney(slice.usd_value, baseCurrency)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
