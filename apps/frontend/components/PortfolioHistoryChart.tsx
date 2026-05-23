"use client";

import { formatMoney, type PortfolioHistoryPoint } from "@/lib/api/portfolio";

const WIDTH = 860;
const HEIGHT = 280;
const PADDING = 24;

function buildPath(points: PortfolioHistoryPoint[]): string {
  if (points.length === 0) {
    return "";
  }
  const values = points.map((point) => point.total_value_usd);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = points.length > 1 ? (WIDTH - 2 * PADDING) / (points.length - 1) : 0;

  return points
    .map((point, index) => {
      const x = PADDING + index * stepX;
      const y = PADDING + (1 - (point.total_value_usd - min) / range) * (HEIGHT - 2 * PADDING);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function PortfolioHistoryChart({
  points,
  markers,
  baseCurrency,
}: {
  points: PortfolioHistoryPoint[];
  markers: string[];
  baseCurrency: string;
}) {
  if (points.length === 0) {
    return (
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400">
        Portfolio history is not available yet.
      </section>
    );
  }

  const values = points.map((point) => point.total_value_usd);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const markerSet = new Set(markers);
  const stepX = points.length > 1 ? (WIDTH - 2 * PADDING) / (points.length - 1) : 0;
  const last = points[points.length - 1];

  return (
    <section className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-zinc-50">30-day portfolio value</h3>
        <p className="font-mono text-sm text-emerald-400">
          {formatMoney(last.total_value_usd, baseCurrency)}
        </p>
      </div>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-72 w-full">
        <rect x={0} y={0} width={WIDTH} height={HEIGHT} fill="#0a0a0a" />
        {points.map((point, index) => {
          if (!markerSet.has(point.date)) {
            return null;
          }
          const x = PADDING + index * stepX;
          return <line key={point.date} x1={x} y1={PADDING} x2={x} y2={HEIGHT - PADDING} stroke="#3f3f46" />;
        })}
        <path d={buildPath(points)} fill="none" stroke="#34d399" strokeWidth={2.5} />
        <text x={PADDING} y={PADDING - 4} className="fill-zinc-500 text-[10px]">
          {formatMoney(max, baseCurrency)}
        </text>
        <text x={PADDING} y={HEIGHT - 6} className="fill-zinc-500 text-[10px]">
          {formatMoney(min, baseCurrency)}
        </text>
      </svg>
      <p className="text-xs text-zinc-500">
        Vertical lines mark rebalance dates. Values are mark-to-market on Frankfurter business-day rates.
      </p>
      <div className="flex flex-wrap gap-4 text-xs text-zinc-400">
        <span>Latest daily P/L: {formatMoney(last.daily_pl_usd, baseCurrency)}</span>
      </div>
    </section>
  );
}
