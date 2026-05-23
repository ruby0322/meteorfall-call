import { apiFetch } from "./client";

export type Holding = {
  currency_code: string;
  weight_percent: number;
  quantity: number;
};

export type Portfolio = {
  id: string;
  initial_cash_usd: number;
  total_value_usd: number;
  daily_pl_usd: number;
  rates_date: string | null;
  holdings: Holding[];
};

export type AllocationInput = {
  currency_code: string;
  weight_percent: number;
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

export async function createPortfolio(): Promise<Portfolio> {
  return apiFetch<Portfolio>("/v1/portfolio", { method: "POST" });
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

export function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export const ALLOCATABLE_CURRENCIES = ["USD", "EUR", "JPY", "GBP", "CNY", "SGD"] as const;
