import {
  ALLOCATABLE_CURRENCIES,
  type AllocationInput,
  type HoldingDetail,
} from "@/lib/api/portfolio";

export type DraftWeights = Record<string, number>;

export type TradeDraft = {
  side: "buy" | "sell";
  usd_amount: number;
};

export function emptyDraftWeights(): DraftWeights {
  return Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => [code, code === "USD" ? 100 : 0]),
  ) as DraftWeights;
}

export function holdingsToDraftWeights(holdings: HoldingDetail[]): DraftWeights {
  return Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => {
      const match = holdings.find((item) => item.currency_code === code);
      return [code, match?.weight_percent ?? 0];
    }),
  ) as DraftWeights;
}

export function sumWeights(draft: DraftWeights): number {
  return ALLOCATABLE_CURRENCIES.reduce((sum, code) => sum + (draft[code] ?? 0), 0);
}

export function normalizeWeights(draft: DraftWeights): DraftWeights {
  const total = sumWeights(draft);
  if (total <= 0) {
    return emptyDraftWeights();
  }
  return Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => [code, Number(((draft[code] / total) * 100).toFixed(4))]),
  ) as DraftWeights;
}

export function applySliderChange(
  current: DraftWeights,
  changedCode: string,
  nextPercent: number,
): DraftWeights {
  const clamped = Math.max(0, Math.min(100, nextPercent));
  const remainingCodes = ALLOCATABLE_CURRENCIES.filter((code) => code !== changedCode);
  const remainingTarget = 100 - clamped;
  const remainingCurrentTotal = remainingCodes.reduce((sum, code) => sum + (current[code] ?? 0), 0);

  if (remainingCurrentTotal <= 0) {
    const even = remainingCodes.length > 0 ? remainingTarget / remainingCodes.length : 0;
    const evenlyDistributed = Object.fromEntries(
      remainingCodes.map((code) => [code, Number(even.toFixed(4))]),
    );
    return {
      ...(current as DraftWeights),
      ...evenlyDistributed,
      [changedCode]: Number(clamped.toFixed(4)),
    };
  }

  const nextDraft: DraftWeights = { ...current };
  nextDraft[changedCode] = Number(clamped.toFixed(4));
  for (const code of remainingCodes) {
    const ratio = (current[code] ?? 0) / remainingCurrentTotal;
    nextDraft[code] = Number((remainingTarget * ratio).toFixed(4));
  }
  return normalizeWeights(nextDraft);
}

export function weightsToAllocations(draft: DraftWeights): AllocationInput[] {
  return ALLOCATABLE_CURRENCIES.map((code) => ({
    currency_code: code,
    weight_percent: Number((draft[code] ?? 0).toFixed(4)),
  })).filter((item) => item.weight_percent > 0);
}

export function buildTradeDraft(): Record<string, TradeDraft> {
  return Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => [code, { side: "buy", usd_amount: 0 }]),
  ) as Record<string, TradeDraft>;
}

export function tradesToTargetWeights(
  holdings: HoldingDetail[],
  trades: Record<string, TradeDraft>,
): DraftWeights {
  const currentUsdByCode = Object.fromEntries(
    ALLOCATABLE_CURRENCIES.map((code) => [
      code,
      holdings.find((item) => item.currency_code === code)?.usd_value ?? 0,
    ]),
  ) as Record<string, number>;
  const total = Object.values(currentUsdByCode).reduce((sum, value) => sum + value, 0);
  if (total <= 0) {
    return emptyDraftWeights();
  }

  const projectedUsdByCode: Record<string, number> = { ...currentUsdByCode };
  for (const code of ALLOCATABLE_CURRENCIES) {
    const trade = trades[code];
    if (!trade || trade.usd_amount <= 0) {
      continue;
    }
    const signed = trade.side === "buy" ? trade.usd_amount : -trade.usd_amount;
    projectedUsdByCode[code] = Math.max(0, projectedUsdByCode[code] + signed);
    projectedUsdByCode.USD = projectedUsdByCode.USD - signed;
  }

  return normalizeWeights(
    Object.fromEntries(
      ALLOCATABLE_CURRENCIES.map((code) => [
        code,
        Number(((projectedUsdByCode[code] / total) * 100).toFixed(4)),
      ]),
    ) as DraftWeights,
  );
}
