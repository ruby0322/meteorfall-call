import { apiFetch } from "./client";

export type LatestRatesResponse = {
  amount: number;
  base: string;
  date: string;
  rates: Record<string, number>;
};

export type UnsupportedCurrencyDetail = {
  unsupported: string[];
  message: string;
  supported_currencies_url: string;
};

export async function fetchLatestRates(
  base = "USD",
  symbols = "EUR,JPY,GBP,CNY,SGD",
): Promise<LatestRatesResponse> {
  const params = new URLSearchParams({ base, symbols });
  return apiFetch<LatestRatesResponse>(`/v1/rates/latest?${params.toString()}`);
}

export async function fetchCurrencies(): Promise<Record<string, string>> {
  return apiFetch<Record<string, string>>("/v1/currencies");
}
