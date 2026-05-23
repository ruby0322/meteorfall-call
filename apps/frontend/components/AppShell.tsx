import Link from "next/link";
import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">
              FX Literacy Lab
            </p>
            <h1 className="text-lg font-semibold text-zinc-50">MarketMage</h1>
          </div>
          <nav className="flex gap-4 text-sm">
            <Link className="text-zinc-300 hover:text-emerald-400" href="/">
              Rates
            </Link>
            <Link className="text-zinc-300 hover:text-emerald-400" href="/portfolio">
              Portfolio
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      <footer className="border-t border-zinc-800 px-6 py-4 text-center text-xs text-zinc-500">
        Simulation only. Daily ECB reference rates — not real-time trading advice.
      </footer>
    </div>
  );
}
