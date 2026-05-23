import { apiFetch } from "./client";

export type Holding = {
  currency_code: string;
  weight_percent: number;
  quantity: number;
};

export type HoldingDetail = Holding & {
  usd_value: number;
  weight_actual_percent: number;
};

export type HoldingDelta = {
  currency_code: string;
  quantity_delta: number;
  usd_delta: number;
};

export type Portfolio = {
  id: string;
  base_currency: string;
  initial_cash_usd: number;
  total_value_usd: number;
  daily_pl_usd: number;
  rates_date: string | null;
  prior_rates_date: string | null;
  holdings: Holding[];
  holdings_detail: HoldingDetail[];
};

export type AllocationInput = {
  currency_code: string;
  weight_percent: number;
};

export type PreviewHoldingsResponse = {
  base_currency: string;
  total_value_usd: number;
  projected_holdings: HoldingDetail[];
  deltas: HoldingDelta[];
};

export type PortfolioHistoryPoint = {
  date: string;
  total_value_usd: number;
  daily_pl_usd: number;
};

export type PortfolioHistoryResponse = {
  base_currency: string;
  points: PortfolioHistoryPoint[];
  rebalance_markers: string[];
};

export type PortfolioSnapshotResponse = {
  base_currency: string;
  as_of: string | null;
  total_value_usd: number;
  daily_pl_usd: number;
  holdings: HoldingDetail[];
  disclaimer: string;
};

export type PortfolioTransactionHolding = {
  currency_code: string;
  weight_percent: number;
  quantity: number;
};

export type PortfolioTransaction = {
  id: number;
  event_type: "initial" | "rebalance";
  base_currency: string;
  effective_rates_date: string;
  total_value_usd: number;
  holdings: PortfolioTransactionHolding[];
  created_at: string;
};

export type PortfolioTransactionsResponse = {
  base_currency: string;
  transactions: PortfolioTransaction[];
};

const PORTFOLIO_STORAGE_KEY = "marketmage-portfolio-id";

export function getStoredPortfolioId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(PORTFOLIO_STORAGE_KEY);
}

export function storePortfolioId(id: string): void {
  window.localStorage.setItem(PORTFOLIO_STORAGE_KEY, id);
}

export async function createPortfolio(baseCurrency = "USD"): Promise<Portfolio> {
  return apiFetch<Portfolio>("/v1/portfolio", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_currency: baseCurrency }),
  });
}

export async function fetchPortfolio(portfolioId: string): Promise<Portfolio> {
  return apiFetch<Portfolio>(`/v1/portfolio/${portfolioId}`);
}

export async function updatePortfolioHoldings(
  portfolioId: string,
  holdings: AllocationInput[],
): Promise<Portfolio> {
  return apiFetch<Portfolio>(`/v1/portfolio/${portfolioId}/holdings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdings }),
  });
}

export async function previewPortfolioHoldings(
  portfolioId: string,
  holdings: AllocationInput[],
): Promise<PreviewHoldingsResponse> {
  return apiFetch<PreviewHoldingsResponse>(`/v1/portfolio/${portfolioId}/holdings/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ holdings }),
  });
}

export async function fetchPortfolioHistory(
  portfolioId: string,
  days = 30,
): Promise<PortfolioHistoryResponse> {
  return apiFetch<PortfolioHistoryResponse>(`/v1/portfolio/${portfolioId}/history?days=${days}`);
}

export async function fetchPortfolioSnapshot(portfolioId: string): Promise<PortfolioSnapshotResponse> {
  return apiFetch<PortfolioSnapshotResponse>(`/v1/portfolio/${portfolioId}/snapshot`);
}

export async function fetchPortfolioTransactions(
  portfolioId: string,
): Promise<PortfolioTransactionsResponse> {
  return apiFetch<PortfolioTransactionsResponse>(`/v1/portfolio/${portfolioId}/transactions`);
}

export async function switchPortfolioBaseCurrency(
  portfolioId: string,
  baseCurrency: string,
): Promise<Portfolio> {
  return apiFetch<Portfolio>(`/v1/portfolio/${portfolioId}/base-currency`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ base_currency: baseCurrency }),
  });
}

export function formatUsd(value: number): string {
  return formatMoney(value, "USD");
}

export function formatMoney(value: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export const ALLOCATABLE_CURRENCIES = ["USD", "EUR", "JPY", "GBP", "CNY", "SGD"] as const;
export const BASE_CURRENCY_OPTIONS = ALLOCATABLE_CURRENCIES;
