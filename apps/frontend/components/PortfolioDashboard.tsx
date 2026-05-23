"use client";

import { useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { AllocationPieChart } from "@/components/AllocationPieChart";
import { PortfolioHistoryChart } from "@/components/PortfolioHistoryChart";
import { PortfolioSnapshotExport } from "@/components/PortfolioSnapshotExport";
import { PortfolioTransactionHistory } from "@/components/PortfolioTransactionHistory";
import {
  ALLOCATABLE_CURRENCIES,
  createPortfolio,
  fetchPortfolio,
  fetchPortfolioHistory,
  fetchPortfolioSnapshot,
  fetchPortfolioTransactions,
  formatMoney,
  previewPortfolioHoldings,
  getStoredPortfolioId,
  storePortfolioId,
  switchPortfolioBaseCurrency,
  updatePortfolioHoldings,
  type HoldingDetail,
  type Portfolio,
} from "@/lib/api/portfolio";
import { useBaseCurrency } from "@/lib/base-currency";
import {
  applySliderChange,
  buildTradeDraft,
  emptyDraftWeights,
  holdingsToDraftWeights,
  sumWeights,
  tradesToTargetWeights,
  weightsToAllocations,
  type DraftWeights,
} from "@/lib/portfolio-rebalance";

type Mode = "sliders" | "trades";

function draftToPieSlices(draft: DraftWeights, totalUsd: number) {
  return ALLOCATABLE_CURRENCIES.map((code) => {
    const weight = draft[code] ?? 0;
    return {
      currency_code: code,
      weight_percent: weight,
      usd_value: Number(((totalUsd * weight) / 100).toFixed(2)),
    };
  }).filter((slice) => slice.weight_percent > 0);
}

function holdingsToPieSlices(holdings: HoldingDetail[]) {
  return holdings
    .map((holding) => ({
      currency_code: holding.currency_code,
      weight_percent: holding.weight_actual_percent,
      usd_value: holding.usd_value,
    }))
    .filter((slice) => slice.weight_percent > 0);
}

export function PortfolioDashboard() {
  const { baseCurrency } = useBaseCurrency();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [draft, setDraft] = useState<DraftWeights>(() => emptyDraftWeights());
  const [tradeDraft, setTradeDraft] = useState(buildTradeDraft);
  const [mode, setMode] = useState<Mode>("sliders");
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [previewResult, setPreviewResult] = useState<Awaited<
    ReturnType<typeof previewPortfolioHoldings>
  > | null>(null);
  const [showCalc, setShowCalc] = useState(false);
  const [history, setHistory] = useState<Awaited<ReturnType<typeof fetchPortfolioHistory>> | null>(null);
  const [transactions, setTransactions] = useState<
    Awaited<ReturnType<typeof fetchPortfolioTransactions>> | null
  >(null);
  const [snapshot, setSnapshot] = useState<Awaited<ReturnType<typeof fetchPortfolioSnapshot>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const draftTotal = useMemo(() => {
    return sumWeights(draft);
  }, [draft]);

  useEffect(() => {
    let cancelled = false;

    async function loadPortfolio() {
      setLoading(true);
      setError(null);
      try {
        const storedId = getStoredPortfolioId();
        let data = storedId ? await fetchPortfolio(storedId) : await createPortfolio(baseCurrency);
        if (storedId && data.base_currency !== baseCurrency) {
          data = await switchPortfolioBaseCurrency(storedId, baseCurrency);
        }
        if (cancelled) {
          return;
        }
        storePortfolioId(data.id);
        setPortfolio(data);
        setDraft(holdingsToDraftWeights(data.holdings_detail));
        const chart = await fetchPortfolioHistory(data.id, 30);
        const exportSnapshot = await fetchPortfolioSnapshot(data.id);
        const ledger = await fetchPortfolioTransactions(data.id);
        if (!cancelled) {
          setHistory(chart);
          setSnapshot(exportSnapshot);
          setTransactions(ledger);
        }
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
  }, [baseCurrency]);

  async function handleReview() {
    if (!portfolio) {
      return;
    }
    setPreviewing(true);
    setError(null);
    try {
      const result = await previewPortfolioHoldings(portfolio.id, weightsToAllocations(draft));
      setPreviewResult(result);
      setPreviewOpen(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Could not preview allocation (${err.status}).`);
      } else {
        setError("Could not preview allocation.");
      }
    } finally {
      setPreviewing(false);
    }
  }

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
      const updated = await updatePortfolioHoldings(portfolio.id, weightsToAllocations(draft));
      setPortfolio(updated);
      setDraft(holdingsToDraftWeights(updated.holdings_detail));
      setTradeDraft(buildTradeDraft());
      setPreviewOpen(false);
      setPreviewResult(null);
      setHistory(await fetchPortfolioHistory(updated.id, 30));
      setSnapshot(await fetchPortfolioSnapshot(updated.id));
      setTransactions(await fetchPortfolioTransactions(updated.id));
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

  const currentPieSlices = holdingsToPieSlices(portfolio.holdings_detail);
  const previewPieSlices = draftToPieSlices(draft, portfolio.total_value_usd);

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold text-zinc-50">Paper Portfolio</h2>
        <p className="text-sm text-zinc-400">
          Virtual {formatMoney(portfolio.initial_cash_usd, portfolio.base_currency)} · manual allocation ·
          simulation only
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
            {formatMoney(portfolio.total_value_usd, portfolio.base_currency)}
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Rates date: {portfolio.rates_date ?? "USD cash only"}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Daily P/L (prior business day)</p>
          <p
            className={`mt-2 font-mono text-3xl ${
              portfolio.daily_pl_usd >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {portfolio.daily_pl_usd >= 0 ? "+" : ""}
            {formatMoney(portfolio.daily_pl_usd, portfolio.base_currency)}
          </p>
          <p className="mt-1 text-xs text-zinc-500">Prior date: {portfolio.prior_rates_date ?? "N/A"}</p>
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
            Mark-to-market value = {portfolio.base_currency} cash + Σ(foreign quantity ÷ latest rate). Daily
            P/L = mark-to-market at latest rates − mark-to-market at prior business-day rates (same
            quantities).
          </p>
          <p className="mt-2 text-zinc-500">
            No leverage, no auto-trading, no predictions — just math on daily reference rates.
          </p>
        </div>
      ) : null}

      <AllocationPieChart
        title="Current allocation"
        totalUsd={portfolio.total_value_usd}
        slices={currentPieSlices}
        baseCurrency={portfolio.base_currency}
      />

      <section className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <h3 className="text-lg font-semibold text-zinc-50">Holdings detail</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[540px] text-sm">
            <thead className="text-left text-zinc-500">
              <tr>
                <th className="py-2 font-medium">Currency</th>
                <th className="py-2 font-medium">Target %</th>
                <th className="py-2 font-medium">Actual %</th>
                <th className="py-2 font-medium">Quantity</th>
                <th className="py-2 font-medium">{portfolio.base_currency} value</th>
              </tr>
            </thead>
            <tbody className="text-zinc-200">
              {portfolio.holdings_detail.map((holding) => (
                <tr key={holding.currency_code} className="border-t border-zinc-800">
                  <td className="py-2 font-mono">{holding.currency_code}</td>
                  <td className="py-2">{holding.weight_percent.toFixed(2)}%</td>
                  <td className="py-2">{holding.weight_actual_percent.toFixed(2)}%</td>
                  <td className="py-2 font-mono">{holding.quantity.toFixed(4)}</td>
                  <td className="py-2">{formatMoney(holding.usd_value, portfolio.base_currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-zinc-50">Manual rebalance</h3>
            <p className="text-sm text-zinc-400">
              Use sliders or trade tickets, then review changes before saving.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMode("sliders")}
              className={`rounded-md px-3 py-1.5 text-xs ${
                mode === "sliders" ? "bg-emerald-500/20 text-emerald-300" : "bg-zinc-800 text-zinc-300"
              }`}
            >
              Sliders
            </button>
            <button
              type="button"
              onClick={() => setMode("trades")}
              className={`rounded-md px-3 py-1.5 text-xs ${
                mode === "trades" ? "bg-emerald-500/20 text-emerald-300" : "bg-zinc-800 text-zinc-300"
              }`}
            >
              Trade amounts
            </button>
          </div>
        </div>

        {mode === "sliders" ? (
          <div className="space-y-3">
            {ALLOCATABLE_CURRENCIES.map((code) => (
              <div key={code} className="rounded-md border border-zinc-800 p-3">
                <div className="mb-2 flex items-center justify-between text-xs text-zinc-400">
                  <span className="font-mono">{code}</span>
                  <span>{(draft[code] ?? 0).toFixed(2)}%</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={0.1}
                  value={draft[code] ?? 0}
                  onChange={(event) => {
                    const nextPercent = Number(event.currentTarget.value);
                    setDraft((current) => applySliderChange(current, code, nextPercent));
                  }}
                  className="w-full accent-emerald-400"
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {ALLOCATABLE_CURRENCIES.map((code) => (
              <div key={code} className="rounded-md border border-zinc-800 p-3">
                <p className="mb-2 text-xs uppercase tracking-wider text-zinc-500">{code}</p>
                <div className="grid grid-cols-2 gap-2">
                  <select
                    value={tradeDraft[code].side}
                    onChange={(event) => {
                      const side = event.currentTarget.value as "buy" | "sell";
                      setTradeDraft((current) => {
                        const next = { ...current, [code]: { ...current[code], side } };
                        setDraft(tradesToTargetWeights(portfolio.holdings_detail, next));
                        return next;
                      });
                    }}
                    className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2 text-sm text-zinc-100"
                  >
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                  </select>
                  <input
                    type="number"
                    min={0}
                    step={10}
                    value={tradeDraft[code].usd_amount}
                    onChange={(event) => {
                      const usd_amount = Number(event.currentTarget.value || 0);
                      setTradeDraft((current) => {
                        const next = { ...current, [code]: { ...current[code], usd_amount } };
                        setDraft(tradesToTargetWeights(portfolio.holdings_detail, next));
                        return next;
                      });
                    }}
                    className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-2 text-sm text-zinc-100"
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        <AllocationPieChart
          title="Preview allocation"
          totalUsd={portfolio.total_value_usd}
          slices={previewPieSlices}
          baseCurrency={portfolio.base_currency}
        />

        <div className="flex flex-wrap items-center gap-3">
          <p
            className={`font-mono text-sm ${
              Math.round(draftTotal * 100) / 100 === 100 ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            Total: {draftTotal.toFixed(2)}%
          </p>
          <button
            type="button"
            onClick={() => setDraft(holdingsToDraftWeights(portfolio.holdings_detail))}
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300"
          >
            Reset to current holdings
          </button>
        </div>

        <button
          type="button"
          disabled={previewing || Math.round(draftTotal * 100) / 100 !== 100}
          onClick={() => void handleReview()}
          className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {previewing ? "Reviewing…" : "Review changes"}
        </button>
      </section>

      {previewOpen && previewResult ? (
        <section className="space-y-4 rounded-lg border border-zinc-700 bg-zinc-900/70 p-4">
          <h3 className="text-lg font-semibold text-zinc-50">Confirm rebalance</h3>
          <div className="grid gap-4 lg:grid-cols-2">
            <AllocationPieChart
              title="Current"
              totalUsd={portfolio.total_value_usd}
              slices={currentPieSlices}
              baseCurrency={portfolio.base_currency}
            />
            <AllocationPieChart
              title="After rebalance"
              totalUsd={previewResult.total_value_usd}
              slices={previewResult.projected_holdings.map((holding) => ({
                currency_code: holding.currency_code,
                weight_percent: holding.weight_actual_percent,
                usd_value: holding.usd_value,
              }))}
              baseCurrency={portfolio.base_currency}
            />
          </div>
          <div className="space-y-1 text-sm">
            {previewResult.deltas.map((delta) => (
              <div key={delta.currency_code} className="flex justify-between text-zinc-300">
                <span className="font-mono">{delta.currency_code}</span>
                <span>
                  {delta.usd_delta >= 0 ? "+" : ""}
                  {formatMoney(delta.usd_delta, portfolio.base_currency)}
                </span>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={() => void handleSave()}
              className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-medium text-zinc-950 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Confirm save"}
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => setPreviewOpen(false)}
              className="rounded-md border border-zinc-700 px-4 py-2 text-sm text-zinc-300"
            >
              Cancel
            </button>
          </div>
        </section>
      ) : null}

      {history ? (
        <PortfolioHistoryChart
          points={history.points}
          markers={history.rebalance_markers}
          baseCurrency={portfolio.base_currency}
        />
      ) : (
        <div className="h-48 animate-pulse rounded-lg bg-zinc-900/40" />
      )}

      {transactions ? (
        <PortfolioTransactionHistory
          transactions={transactions.transactions}
          baseCurrency={portfolio.base_currency}
        />
      ) : (
        <div className="h-32 animate-pulse rounded-lg bg-zinc-900/40" />
      )}

      <PortfolioSnapshotExport snapshot={snapshot} baseCurrency={portfolio.base_currency} />
    </div>
  );
}
