"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BASE_CURRENCY_OPTIONS } from "@/lib/api/portfolio";
import { useBaseCurrency } from "@/lib/base-currency";

const NAV_ITEMS = [
  { href: "/", label: "Rates" },
  { href: "/portfolio", label: "Portfolio" },
] as const;

function navClass(isActive: boolean): string {
  return isActive
    ? "rounded-md bg-emerald-500/10 px-3 py-1.5 text-emerald-400"
    : "rounded-md px-3 py-1.5 text-zinc-300 hover:text-emerald-400";
}

export function AppNav() {
  const pathname = usePathname();
  const { baseCurrency, setBaseCurrency } = useBaseCurrency();

  return (
    <div className="flex items-center gap-3">
      <nav className="flex gap-1 text-sm">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className={navClass(isActive)}>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <label className="flex items-center gap-2 text-xs text-zinc-400">
        <span className="uppercase tracking-wider">Base</span>
        <select
          value={baseCurrency}
          onChange={(event) => setBaseCurrency(event.currentTarget.value)}
          className="rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1 text-zinc-100"
        >
          {BASE_CURRENCY_OPTIONS.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
