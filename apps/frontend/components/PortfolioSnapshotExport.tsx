"use client";

import { useMemo, useState } from "react";

import { formatMoney, type PortfolioSnapshotResponse } from "@/lib/api/portfolio";

function snapshotToMarkdown(snapshot: PortfolioSnapshotResponse, baseCurrency: string): string {
  const lines = [
    `# MarketMage Portfolio Snapshot (${snapshot.as_of ?? "N/A"})`,
    "",
    `- Base currency: ${baseCurrency}`,
    `- Total value: ${formatMoney(snapshot.total_value_usd, baseCurrency)}`,
    `- Daily P/L: ${formatMoney(snapshot.daily_pl_usd, baseCurrency)}`,
    "",
    "| Currency | Weight | Base Value | Quantity |",
    "| --- | ---: | ---: | ---: |",
    ...snapshot.holdings.map(
      (holding) =>
        `| ${holding.currency_code} | ${holding.weight_actual_percent.toFixed(2)}% | ${formatMoney(holding.usd_value, baseCurrency)} | ${holding.quantity.toFixed(4)} |`,
    ),
    "",
    `> ${snapshot.disclaimer}`,
  ];
  return lines.join("\n");
}

export function PortfolioSnapshotExport({
  snapshot,
  baseCurrency,
}: {
  snapshot: PortfolioSnapshotResponse | null;
  baseCurrency: string;
}) {
  const [copied, setCopied] = useState<"json" | "markdown" | null>(null);
  const markdown = useMemo(
    () => (snapshot ? snapshotToMarkdown(snapshot, baseCurrency) : ""),
    [snapshot, baseCurrency],
  );

  async function copyText(content: string, kind: "json" | "markdown") {
    await navigator.clipboard.writeText(content);
    setCopied(kind);
    window.setTimeout(() => setCopied(null), 1400);
  }

  return (
    <section className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-zinc-50">Snapshot export</h3>
        {snapshot ? <span className="text-xs text-zinc-500">As of {snapshot.as_of ?? "N/A"}</span> : null}
      </div>
      <p className="text-sm text-zinc-400">
        Export your current simulation state as JSON or markdown summary.
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!snapshot}
          onClick={() => snapshot && void copyText(JSON.stringify(snapshot, null, 2), "json")}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 disabled:opacity-40"
        >
          {copied === "json" ? "Copied JSON" : "Copy JSON"}
        </button>
        <button
          type="button"
          disabled={!snapshot}
          onClick={() => snapshot && void copyText(markdown, "markdown")}
          className="rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 disabled:opacity-40"
        >
          {copied === "markdown" ? "Copied markdown" : "Copy markdown"}
        </button>
      </div>
      {snapshot ? <p className="text-xs text-zinc-500">{snapshot.disclaimer}</p> : null}
    </section>
  );
}
