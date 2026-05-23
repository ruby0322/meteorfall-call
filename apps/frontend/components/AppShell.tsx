import type { ReactNode } from "react";

import { AppNav } from "@/components/AppNav";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 terminal-grid">
      <header className="border-b border-zinc-800/80 bg-zinc-900/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-emerald-400/90">
              FX Literacy Lab
            </p>
            <h1 className="bg-gradient-to-r from-zinc-50 to-emerald-200 bg-clip-text text-lg font-semibold text-transparent">
              MarketMage
            </h1>
          </div>
          <AppNav />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      <footer className="border-t border-zinc-800 px-6 py-4 text-center text-xs text-zinc-500">
        Simulation only · Daily ECB reference rates · Not real-time trading advice
      </footer>
    </div>
  );
}
