"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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

  return (
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
  );
}
