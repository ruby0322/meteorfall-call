"use client";

import { useState } from "react";

import {
  formatMoney,
  type PortfolioTransaction,
} from "@/lib/api/portfolio";

const EVENT_LABELS: Record<PortfolioTransaction["event_type"], string> = {
  initial: "Initial allocation",
  rebalance: "Rebalance",
};

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PortfolioTransactionHistory({
  transactions,
  baseCurrency,
}: {
  transactions: PortfolioTransaction[];
  baseCurrency: string;
}) {
  const [expandedId, setExpandedId] = useState<number | null>(
    transactions[0]?.id ?? null,
  );

  if (transactions.length === 0) {
    return (
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4 text-sm text-zinc-400">
        No transaction history yet.
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div>
        <h3 className="text-lg font-semibold text-zinc-50">Transaction history</h3>
        <p className="text-sm text-zinc-400">
          Rebalance events recorded for this paper portfolio.
        </p>
      </div>

      <div className="space-y-3">
        {transactions.map((transaction) => {
          const expanded = expandedId === transaction.id;
          return (
            <article
              key={transaction.id}
              className="rounded-md border border-zinc-800 bg-zinc-950/40"
            >
              <button
                type="button"
                onClick={() =>
                  setExpandedId((current) =>
                    current === transaction.id ? null : transaction.id,
                  )
                }
                className="flex w-full items-start justify-between gap-4 px-4 py-3 text-left"
              >
                <div className="space-y-1">
                  <p className="text-sm font-medium text-zinc-100">
                    {EVENT_LABELS[transaction.event_type]}
                  </p>
                  <p className="text-xs text-zinc-500">
                    Rates date {transaction.effective_rates_date} · recorded{" "}
                    {formatTimestamp(transaction.created_at)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm text-emerald-400">
                    {formatMoney(transaction.total_value_usd, baseCurrency)}
                  </p>
                  <p className="text-xs text-zinc-500">In {baseCurrency}</p>
                </div>
              </button>

              {expanded ? (
                <div className="border-t border-zinc-800 px-4 py-3">
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[420px] text-sm">
                      <thead className="text-left text-zinc-500">
                        <tr>
                          <th className="py-1 font-medium">Currency</th>
                          <th className="py-1 font-medium">Target %</th>
                          <th className="py-1 font-medium">Quantity</th>
                        </tr>
                      </thead>
                      <tbody className="text-zinc-200">
                        {transaction.holdings.map((holding) => (
                          <tr key={holding.currency_code} className="border-t border-zinc-900">
                            <td className="py-1 font-mono">{holding.currency_code}</td>
                            <td className="py-1">{holding.weight_percent.toFixed(2)}%</td>
                            <td className="py-1 font-mono">{holding.quantity.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-2 text-xs text-zinc-500">
                    Quantities at time of event; totals converted to current {baseCurrency} rates.
                  </p>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>

      <p className="text-xs text-zinc-500">
        Current display base: {baseCurrency}. Simulation only — not real trades.
      </p>
    </section>
  );
}
