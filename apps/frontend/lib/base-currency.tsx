"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

const STORAGE_KEY = "marketmage-base-currency";

type BaseCurrencyContextValue = {
  baseCurrency: string;
  setBaseCurrency: (currency: string) => void;
};

const BaseCurrencyContext = createContext<BaseCurrencyContextValue | null>(null);

export function BaseCurrencyProvider({ children }: { children: ReactNode }) {
  const [baseCurrency, setBaseCurrencyState] = useState("USD");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setBaseCurrencyState(stored);
    }
  }, []);

  const value = useMemo<BaseCurrencyContextValue>(
    () => ({
      baseCurrency,
      setBaseCurrency: (currency: string) => {
        const upper = currency.toUpperCase();
        setBaseCurrencyState(upper);
        window.localStorage.setItem(STORAGE_KEY, upper);
      },
    }),
    [baseCurrency],
  );

  return <BaseCurrencyContext.Provider value={value}>{children}</BaseCurrencyContext.Provider>;
}

export function useBaseCurrency(): BaseCurrencyContextValue {
  const context = useContext(BaseCurrencyContext);
  if (!context) {
    throw new Error("useBaseCurrency must be used within BaseCurrencyProvider");
  }
  return context;
}
