"use client";

import { useEffect, useMemo, useState } from "react";

import { TwdUnsupportedCard } from "@/components/TwdUnsupportedCard";
import {
  computeDayChange,
  fetchHistoryRates,
  fetchLatestRates,
  formatRate,
  historyWindow,
  type LatestRatesResponse,
} from "@/lib/api/rates";
import { BASE_CURRENCY_OPTIONS } from "@/lib/api/portfolio";
import { useBaseCurrency } from "@/lib/base-currency";
import { ApiError } from "@/lib/api/client";

type RateCardProps = {
  baseCurrency: string;
  code: string;
  rate: number;
  dayChange: number | null;
};

function RateCard({ baseCurrency, code, rate, dayChange }: RateCardProps) {
  const changeLabel =
    dayChange === null
      ? "—"
      : `${dayChange >= 0 ? "+" : ""}${dayChange.toFixed(2)}% vs prior day`;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
      <p className="text-xs uppercase tracking-wider text-zinc-500">
        {baseCurrency}/{code}
      </p>
      <p className="mt-2 font-mono text-2xl text-emerald-400">{formatRate(code, rate)}</p>
      <p
        className={`mt-1 text-xs ${
          dayChange === null
            ? "text-zinc-500"
            : dayChange >= 0
              ? "text-emerald-500/80"
              : "text-rose-400/80"
        }`}
      >
        {changeLabel}
      </p>
    </div>
  );
}

export function RateBoard() {
  const { baseCurrency } = useBaseCurrency();
  const [latest, setLatest] = useState<LatestRatesResponse | null>(null);
  const [dayChanges, setDayChanges] = useState<Record<string, number | null>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const symbols = useMemo(
    () => BASE_CURRENCY_OPTIONS.filter((code) => code !== baseCurrency),
    [baseCurrency],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadRates() {
      setLoading(true);
      setError(null);
      try {
        const { start, end } = historyWindow(14);
        const [latestRates, history] = await Promise.all([
          fetchLatestRates(baseCurrency, symbols.join(",")),
          fetchHistoryRates(start, end, baseCurrency, symbols.join(",")),
        ]);
        if (cancelled) {
          return;
        }
        setLatest(latestRates);
        const changes = Object.fromEntries(
          symbols.map((code) => [code, computeDayChange(history, code)]),
        );
        setDayChanges(changes);
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiError) {
          setError(`Failed to load rates (${err.status}). Is the backend running on :8000?`);
        } else {
          setError("Failed to load rates.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadRates();
    return () => {
      cancelled = true;
    };
  }, [baseCurrency, symbols]);

  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold text-zinc-50">Daily Rate Board</h2>
        <p className="text-sm text-zinc-400">
          {baseCurrency} base · Frankfurter ECB reference rates · updated once per business day (~16:00 CET)
        </p>
      </section>

      {error ? (
        <div className="rounded-lg border border-rose-900/50 bg-rose-950/20 p-4 text-sm text-rose-200">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading
          ? symbols.map((code) => (
              <div
                key={code}
                className="animate-pulse rounded-lg border border-zinc-800 bg-zinc-900/60 p-4"
              >
                <div className="h-3 w-16 rounded bg-zinc-800" />
                <div className="mt-4 h-8 w-24 rounded bg-zinc-800" />
              </div>
            ))
          : symbols.map((code) => (
              <RateCard
                key={code}
                baseCurrency={baseCurrency}
                code={code}
                rate={latest?.rates[code] ?? 0}
                dayChange={dayChanges[code] ?? null}
              />
            ))}
        <TwdUnsupportedCard />
      </div>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <p className="text-xs uppercase tracking-wider text-zinc-500">Last updated</p>
        <p className="mt-1 font-mono text-sm text-zinc-300">
          {loading ? "Loading…" : latest?.date ?? "—"}
        </p>
        <p className="mt-1 text-xs text-zinc-500">
          Daily reference — not a live trading feed.
        </p>
      </section>
    </div>
  );
}
