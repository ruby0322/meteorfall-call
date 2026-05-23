"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  ALLOCATABLE_CURRENCIES,
  createPortfolio,
  fetchPortfolio,
  formatUsd,
  getStoredPortfolioId,
  storePortfolioId,
  updatePortfolioHoldings,
  type AllocationInput,
  type Portfolio,
} from "@/lib/api/portfolio";

type DraftAllocation = Record<string, string>;

function holdingsToDraft(holdings: Portfolio["holdings"]): DraftAllocation {
  return Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => {
      const match = holdings.find((item) => item.currency_code === code);
      return [code, match ? String(match.weight_percent) : "0"];
    }),
  );
}

function draftToAllocations(draft: DraftAllocation): AllocationInput[] {
  return ALLOCATABLE_CURRENCIES.map((code) => ({
    currency_code: code,
    weight_percent: Number(draft[code] ?? 0),
  })).filter((item) => item.weight_percent > 0);
}

export function PortfolioDashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [draft, setDraft] = useState<DraftAllocation>(() =>
    Object.fromEntries(ALLOCATABLE_CURRENCIES.map((code) => [code, code === "USD" ? "100" : "0"])),
  );
  const [showCalc, setShowCalc] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const draftTotal = useMemo(() => {
    return ALLOCATABLE_CURRENCIES.reduce(
      (sum, code) => sum + Number(draft[code] ?? 0),
      0,
    );
  }, [draft]);

  useEffect(() => {
    let cancelled = false;

    async function loadPortfolio() {
      setLoading(true);
      setError(null);
      try {
        const storedId = getStoredPortfolioId();
        const data = storedId ? await fetchPortfolio(storedId) : await createPortfolio();
        if (cancelled) {
          return;
        }
        storePortfolioId(data.id);
        setPortfolio(data);
        setDraft(holdingsToDraft(data.holdings));
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiError) {
          setError(`Portfolio unavailable (${err.status}). Is the backend running?`);
        } else {
          setError("Portfolio unavailable.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadPortfolio();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave() {
    if (!portfolio) {
      return;
    }
    if (Math.round(draftTotal * 100) / 100 !== 100) {
      setError("Allocations must sum to 100% before saving.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const updated = await updatePortfolioHoldings(portfolio.id, draftToAllocations(draft));
      setPortfolio(updated);
      setDraft(holdingsToDraft(updated.holdings));
    } catch (err) {
      if (err instanceof ApiError) {
        setError("Could not save allocation. Check weights sum to 100%.");
      } else {
        setError("Could not save allocation.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className="h-48 animate-pulse rounded-lg bg-zinc-900/60" />;
  }

  if (!portfolio) {
    return (
      <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">
        {error ?? "Portfolio unavailable."}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold text-zinc-50">Paper Portfolio</h2>
        <p className="text-sm text-zinc-400">
          Virtual {formatUsd(portfolio.initial_cash_usd)} · manual allocation · simulation only
        </p>
      </section>

      {error ? (
        <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Total value</p>
          <p className="mt-2 font-mono text-3xl text-emerald-400">
            {formatUsd(portfolio.total_value_usd)}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Rates date: {portfolio.rates_date ?? "USD cash only"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Daily P/L</p>
          <p
            className={`mt-2 font-mono text-3xl ${
              portfolio.daily_pl_usd >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {portfolio.daily_pl_usd >= 0 ? "+" : ""}
            {formatUsd(portfolio.daily_pl_usd)}
          </p>
          <button
            type="button"
            className="mt-2 text-xs text-emerald-400/80 underline-offset-2 hover:underline"
            onClick={() => setShowCalc((value) => !value)}
          >
            {showCalc ? "Hide" : "How is this calculated?"}
          </button>
        </div>
      </div>

      {showCalc ? (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-300">
          <p>
            Mark-to-market value = USD cash + Σ(foreign quantity ÷ latest rate). Daily P/L =
            current value − value at last rebalance snapshot ({formatUsd(portfolio.initial_cash_usd)}{" "}
            starting notional).
          </p>
          <p className="mt-2 text-zinc-500">
            No leverage, no auto-trading, no predictions — just math on daily reference rates.
          </p>
        </div>
      ) : null}

      <section className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-zinc-50">Manual rebalance</h3>
            <p className="text-sm text-zinc-400">
              Set target weights (must sum to 100%) — preview before save.
            </p>
          </div>
          <p
            className={`font-mono text-sm ${
              Math.round(draftTotal * 100) / 100 === 100 ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            Total: {draftTotal.toFixed(1)}%
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ALLOCATABLE_CURRENCIES.map((code) => (
            <label key={code} className="block text-sm text-zinc-300">
              <span className="text-xs uppercase tracking-wider text-zinc-500">{code} weight %</span>
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={draft[code] ?? "0"}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, [code]: event.target.value }))
                }
                className="mt-1 w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-zinc-100"
              />
            </label>
          ))}
        </div>

        <button
          type="button"
          disabled={saving || Math.round(draftTotal * 100) / 100 !== 100}
          onClick={() => void handleSave()}
          className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save allocation"}
        </button>
      </section>
    </div>
  );
}
