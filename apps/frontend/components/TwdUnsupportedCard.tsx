export function TwdUnsupportedCard() {
  return (
    <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-4">
      <p className="text-xs uppercase tracking-wider text-amber-500">USD/TWD</p>
      <p className="mt-2 text-sm font-medium text-amber-300">Not supported by Frankfurter</p>
      <p className="mt-1 text-xs text-amber-200/70">
        TWD is not in the ECB reference set. Riley&apos;s brief lists it, but the upstream
        API does not publish it — we surface the gap instead of faking a rate.
      </p>
      <p className="mt-2 text-xs text-amber-200/50">
        See supported codes via <code className="text-amber-200/80">GET /v1/currencies</code>
      </p>
    </div>
  );
}
