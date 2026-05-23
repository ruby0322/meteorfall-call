"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { useBaseCurrency } from "@/lib/base-currency";
import {
  buildSvgPath,
  computeYBounds,
  loadTrendSeriesForBase,
  type ChartSeries,
} from "@/lib/trend-chart";

const WIDTH = 720;
const HEIGHT = 280;
const PADDING = 28;

export function TrendChart() {
  const { baseCurrency } = useBaseCurrency();
  const [series, setSeries] = useState<ChartSeries[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadChart() {
      setLoading(true);
      setError(null);
      try {
        const data = await loadTrendSeriesForBase(baseCurrency, 30);
        if (!cancelled) {
          setSeries(data);
        }
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiError) {
          setError(`Trend data unavailable (${err.status}).`);
        } else {
          setError("Trend data unavailable.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadChart();
    return () => {
      cancelled = true;
    };
  }, [baseCurrency]);

  const bounds = computeYBounds(series);

  return (
    <section className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div>
        <h3 className="text-lg font-semibold text-zinc-50">30-day trend (% change)</h3>
        <p className="text-sm text-zinc-400">
          {baseCurrency} base, normalized from period start — historical context, not a forecast.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-rose-300">{error}</p>
      ) : loading ? (
        <div className="h-[280px] animate-pulse rounded bg-zinc-900/80" />
      ) : (
        <>
          <svg
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            className="h-auto w-full"
            role="img"
            aria-label="30-day normalized FX trend chart"
          >
            <rect x="0" y="0" width={WIDTH} height={HEIGHT} fill="transparent" />
            <line
              x1={PADDING}
              y1={HEIGHT - PADDING}
              x2={WIDTH - PADDING}
              y2={HEIGHT - PADDING}
              stroke="#3f3f46"
              strokeWidth="1"
            />
            {series.map((item) => (
              <path
                key={item.code}
                d={buildSvgPath(item.points, WIDTH, HEIGHT, PADDING, bounds.minY, bounds.maxY)}
                fill="none"
                stroke={item.color}
                strokeWidth="2"
              />
            ))}
          </svg>
          <div className="flex flex-wrap gap-4 text-xs">
            {series.map((item) => {
              const last = item.points[item.points.length - 1]?.value ?? 0;
              return (
                <div key={item.code} className="flex items-center gap-2 text-zinc-300">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="font-mono">
                    {item.code} {last >= 0 ? "+" : ""}
                    {last.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
