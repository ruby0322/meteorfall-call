export default function PortfolioPage() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold text-zinc-50">Paper Portfolio</h2>
        <p className="text-sm text-zinc-400">
          Virtual $10,000 · manual allocation · daily mark-to-market P/L (Phase 2+)
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Total value</p>
          <p className="mt-2 font-mono text-3xl text-emerald-400">$10,000.00</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4">
          <p className="text-xs uppercase tracking-wider text-zinc-500">Daily P/L</p>
          <p className="mt-2 font-mono text-3xl text-zinc-400">—</p>
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-zinc-700 p-6 text-sm text-zinc-500">
        Allocation editor and rebalance preview will land after portfolio API is wired.
      </div>
    </div>
  );
}
