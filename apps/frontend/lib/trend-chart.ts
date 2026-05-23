import {
  TRACKED_SYMBOLS,
  fetchHistoryRates,
  historyWindow,
  type HistoryRatesResponse,
} from "@/lib/api/rates";

export type ChartSeries = {
  code: string;
  color: string;
  points: Array<{ date: string; value: number }>;
};

const SERIES_COLORS: Record<string, string> = {
  EUR: "#34d399",
  JPY: "#60a5fa",
  GBP: "#f472b6",
  CNY: "#fbbf24",
  SGD: "#a78bfa",
};

export function pivotHistoryToSeries(
  history: HistoryRatesResponse,
  symbols: readonly string[] = TRACKED_SYMBOLS,
): ChartSeries[] {
  const dates = Object.keys(history.rates).sort();
  if (dates.length === 0) {
    return [];
  }

  return symbols.map((code) => {
    const rawPoints = dates
      .map((date) => {
        const rate = history.rates[date]?.[code];
        if (rate === undefined || !Number.isFinite(rate)) {
          return null;
        }
        return { date, rate };
      })
      .filter((point): point is { date: string; rate: number } => point !== null);

    if (rawPoints.length === 0) {
      return { code, color: SERIES_COLORS[code] ?? "#94a3b8", points: [] };
    }

    const baseRate = rawPoints[0].rate;
    const points = rawPoints.map(({ date, rate }) => ({
      date,
      value: baseRate === 0 ? 0 : ((rate - baseRate) / baseRate) * 100,
    }));

    return {
      code,
      color: SERIES_COLORS[code] ?? "#94a3b8",
      points,
    };
  }).filter((series) => series.points.length > 0);
}

export async function loadTrendSeries(days = 30): Promise<ChartSeries[]> {
  return loadTrendSeriesForBase("USD", days);
}

export async function loadTrendSeriesForBase(base: string, days = 30): Promise<ChartSeries[]> {
  const { start, end } = historyWindow(days);
  const symbols = TRACKED_SYMBOLS.filter((code) => code !== base);
  const history = await fetchHistoryRates(start, end, base, symbols.join(","));
  return pivotHistoryToSeries(history, symbols);
}

export function buildSvgPath(
  points: Array<{ date: string; value: number }>,
  width: number,
  height: number,
  padding: number,
  minY: number,
  maxY: number,
): string {
  if (points.length === 0) {
    return "";
  }

  const xStep = points.length === 1 ? 0 : (width - padding * 2) / (points.length - 1);
  const yRange = maxY - minY || 1;

  return points
    .map((point, index) => {
      const x = padding + index * xStep;
      const y = padding + (1 - (point.value - minY) / yRange) * (height - padding * 2);
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function computeYBounds(series: ChartSeries[]): { minY: number; maxY: number } {
  const values = series.flatMap((item) => item.points.map((point) => point.value));
  if (values.length === 0) {
    return { minY: -1, maxY: 1 };
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max(0.5, (max - min) * 0.1);
  return { minY: min - padding, maxY: max + padding };
}
