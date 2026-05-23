# Scope Research — MarketMage / FX Literacy Lab

> Decision trace for Topic 1 scope. Written before `PLAN.md` and before any application code.
> See also: [PLAN.md](../PLAN.md), [topics/topic-1-marketmage.md](../topics/topic-1-marketmage.md).

## Problem space

Riley's brief wraps a real need in trading-theatre: **people who touch multiple currencies want to feel oriented** — travelers budgeting a trip, students receiving remittances, first-time investors curious about FX exposure — without being sold leverage or fake certainty.

The kernel is not "AI that trades FX while you sleep." It is **honest daily reference-rate literacy**: what is my money worth in other currencies today, and how has that changed recently?

## Competitive scan

| Pattern | Example | Failure mode for our slice |
|---|---|---|
| Retail FX apps | Revolut, Wise rate widgets | Optimized for conversion, not education; often imply freshness beyond daily reference |
| Trading terminals | TradingView, Bloomberg | Candlesticks and sub-second feeds set expectations our API cannot meet |
| Generic converters | Google "1 USD to TWD" | Silent on data source, update cadence, and unsupported codes |
| "AI trading" demos | Various fintech pitch decks | Fabricated accuracy claims; regulatory traps dressed as "educational" |

**Gap we can fill:** A small, transparent tool that labels data as **daily ECB reference rates**, surfaces unsupported currencies explicitly, and lets users explore exposure with **virtual money only** — no orders, no leverage, no predictions.

## Frankfurter API constraints (verified)

Base URL for this project: `https://api.frankfurter.app` (per topic spec).

Live check of `GET /currencies` (2026-05-23): **31 currency codes** returned. Riley's list includes **TWD**, which is **not** in the set.

| Riley currency | Frankfurter support | Notes |
|---|---|---|
| USD | Yes | Natural base currency |
| EUR | Yes | |
| JPY | Yes | |
| GBP | Yes | |
| CNY | Yes | |
| SGD | Yes | APAC relevance |
| TWD | **No** | Must surface in UI + PLAN — not silently drop |

Other binding facts from the topic file and API docs:

- Rates publish **once per business day** (~16:00 CET). No sub-second feed exists.
- Endpoints available: `/latest`, date ranges (`/start..end`), `/currencies`. **No** prediction, OHLC, or intraday endpoints.
- BE must proxy upstream; cache is appropriate because data is stable intra-day.

## Scope options evaluated

### Option A — APAC FX Pulse (minimal)

Daily rate board (USD → EUR/JPY/GBP/CNY/SGD), explicit TWD unsupported card, 30-day normalized trend chart, BE cache + rate-limit guard.

| Pros | Cons |
|---|---|
| Fastest to ship; lowest trap surface | Misses paper-portfolio kernel from brief |
| Strong triage signal | Less "product" for LP demo narrative |

### Option B — FX Literacy Lab (chosen)

Option A **plus** paper portfolio: virtual $10k, manual allocation across supported currencies, daily mark-to-market P/L from rate changes only, persisted in Postgres.

| Pros | Cons |
|---|---|
| Preserves "portfolio" intent without AI/leverage | Postgres + docker adds setup time |
| Justifies BE + DB in stack choice | Slightly wider than Option A |
| Strong counter-proposals for auto-rebalance and P/L curve | |
| Fits 3–7 day timeline with parallel FE/BE tracks | |

### Option C — LP Demo Terminal

Option B plus dark terminal UI polish, descriptive trend insight panel (7d/30d % change — **not** forecasts), shareable snapshot export.

| Pros | Cons |
|---|---|
| Highest product-judgement bonus potential | Polish risk if timeline slips |
| Closer to Riley's aesthetic ask | Export/snapshot is nice-to-have for v0 |

## Decision

**Ship Option B** for the take-home core. Defer Option C polish items (terminal theme, trend insight panel, snapshot export) to Phase 3–4 if time allows — they are bonus-tier, not hire-bar.

**Rationale:**

1. **Rubric:** Refusing traps scores higher than implementing them; Option B still ships a coherent vertical slice with counter-proposals.
2. **API fit:** Daily rates + historical range + portfolio MTM maps cleanly to Frankfurter; no lying about real-time or predictions.
3. **Stack:** Postgres persistence matches candidate's preferred stack ([pd-care-monorepo](https://github.com/ruby0322/pd-care-monorepo)) and demonstrates production thinking without over-building.
4. **Timeline:** Achievable in 3–7 days with parallel Phase 1A/1B and Phase 3 UI tracks.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Label UI "real-time" with polling | Data is daily; mislabeling is FTC UDAP / false advertising territory |
| LLM "24h prediction" with disclaimer | No defensible accuracy; disclaimer-laundering per REFUSAL_PATTERNS |
| 50x leverage paper trading | Unlicensed brokerage framing even if virtual |
| In-memory-only portfolio | Valid thin slice, but user chose Postgres; persistence is the learning goal |
| Frankfurter v2 / multi-provider for TWD | Out of scope for v0; document as future path in PLAN instead |

## AI stress-test notes (human decision retained)

Prompt used: *"What's a trap in Topic 1 I might miss?"*

Additional flag surfaced: **social portfolio leaderboard** — competitive comparison implies consent, auth, and PII handling we are not building. Counter-proposal: user can export **their own** snapshot only (deferred to Option C if time).

Prompt used: *"Is paper portfolio without leverage still a securities issue?"*

Response considered: Virtual manual allocation with no order execution is materially different from automated trading or margin; still requires clear "simulation only" copy in UI footer. Accepted for Option B with disclaimer.

---

**Next step:** [PLAN.md](../PLAN.md) — refuse-first triage and ship list derived from this research.
