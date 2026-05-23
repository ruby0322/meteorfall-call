import { apiFetch } from "./client";

export type LatestRatesResponse = {
  amount: number;
  base: string;
  date: string;
  rates: Record<string, number>;
};

export type HistoryRatesResponse = {
  base: string;
  rates: Record<string, Record<string, number>>;
  start_date?: string;
  end_date?: string;
};

export type UnsupportedCurrencyDetail = {
  unsupported: string[];
  message: string;
  supported_currencies_url: string;
};

export const TRACKED_SYMBOLS = ["EUR", "JPY", "GBP", "CNY", "SGD"] as const;

export async function fetchLatestRates(
  base = "USD",
  symbols = TRACKED_SYMBOLS.join(","),
): Promise<LatestRatesResponse> {
  const params = new URLSearchParams({ base, symbols });
  return apiFetch<LatestRatesResponse>(`/v1/rates/latest?${params.toString()}`);
}

export async function fetchHistoryRates(
  start: string,
  end: string,
  base = "USD",
  symbols = TRACKED_SYMBOLS.join(","),
): Promise<HistoryRatesResponse> {
  const params = new URLSearchParams({ start, end, base, symbols });
  return apiFetch<HistoryRatesResponse>(`/v1/rates/history?${params.toString()}`);
}

export async function fetchCurrencies(): Promise<Record<string, string>> {
  return apiFetch<Record<string, string>>("/v1/currencies");
}

export function formatRate(code: string, value: number): string {
  if (code === "JPY") {
    return value.toFixed(2);
  }
  return value.toFixed(4);
}

export function computeDayChange(
  history: HistoryRatesResponse,
  code: string,
): number | null {
  const dates = Object.keys(history.rates).sort();
  if (dates.length < 2) {
    return null;
  }
  const previousDate = dates[dates.length - 2];
  const currentDate = dates[dates.length - 1];
  const previous = history.rates[previousDate]?.[code];
  const current = history.rates[currentDate]?.[code];
  if (previous === undefined || current === undefined || previous === 0) {
    return null;
  }
  return ((current - previous) / previous) * 100;
}

export function historyWindow(days: number): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}
