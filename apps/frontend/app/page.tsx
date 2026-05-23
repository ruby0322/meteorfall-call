const PLACEHOLDER_PAIRS = ["EUR", "JPY", "GBP", "CNY", "SGD"];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold text-zinc-50">Daily Rate Board</h2>
        <p className="text-sm text-zinc-400">
          USD base · Frankfurter ECB reference rates · wiring to BE in Phase 3
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {PLACEHOLDER_PAIRS.map((code) => (
          <div
            key={code}
            className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-4"
          >
            <p className="text-xs uppercase tracking-wider text-zinc-500">USD/{code}</p>
            <p className="mt-2 font-mono text-2xl text-emerald-400">—</p>
            <p className="mt-1 text-xs text-zinc-500">Awaiting /v1/rates/latest</p>
          </div>
        ))}
        <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4">
          <p className="text-xs uppercase tracking-wider text-amber-500">USD/TWD</p>
          <p className="mt-2 text-sm font-medium text-amber-300">Not supported</p>
          <p className="mt-1 text-xs text-amber-200/70">
            TWD is outside Frankfurter ECB set — surfaced explicitly in Phase 3.
          </p>
        </div>
      </div>

      <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
        <p className="text-xs uppercase tracking-wider text-zinc-500">Last updated</p>
        <p className="mt-1 font-mono text-sm text-zinc-300">—</p>
      </section>
    </div>
  );
}
