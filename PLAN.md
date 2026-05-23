# PLAN

> Filled in **before** coding. Section order: refuse → counter-propose → ship.
> Scope research trace: [docs/SCOPE_RESEARCH.md](docs/SCOPE_RESEARCH.md)

## Topic I was assigned

Topic 1 — **MarketMage** (FX dashboard brief; upstream: Frankfurter)

## Stack I picked

- FE: **Next.js** (App Router) + TypeScript + Tailwind CSS
- BE: **FastAPI** (Python) + SQLAlchemy + httpx
- DB: **PostgreSQL 16** (paper portfolio persistence)
- Why this stack (one sentence): Matches my production monorepo patterns ([pd-care-monorepo](https://github.com/ruby0322/pd-care-monorepo)), separates FE/BE cleanly for the proxy requirement, and Docker Compose gives graders a one-command run.

## Items in the brief that are red flags (legal, ethical, technical)

- **Sub-second "real-time" FX feed** — Frankfurter publishes daily ECB reference rates once per business day (~16:00 CET). Labeling the UI "real-time" would be false advertising (FTC UDAP / consumer protection).
- **"AI prediction engine" with 99% accuracy** — No prediction endpoint exists; the accuracy claim is fabricated. Marketing a false precision rate is misrepresentation regardless of disclaimers.
- **50x leverage + unlicensed FX trading ("educational" until $50M AUM)** — Retail FX with leverage requires CFTC/SEC/FINRA licensing (RFED in the US; ESMA leverage caps in EU). "Educational" relabeling without a license is disclaimer-laundering, not compliance.
- **One-click auto-rebalance YOLO on AI signal** — Automated allocation on financial signals is investment advice / brokerage-like behavior without registration.
- **Social portfolio leaderboard vs friends** — Competitive comparison of financial performance without consent infrastructure raises GDPR/privacy and social-comparison harm issues.
- **TradingView candlestick chart** — Frankfurter has no OHLC/intraday data; building fake candles would misrepresent the data source.
- **"Don't worry about the SEC, my cousin is a lawyer"** — Legal counsel does not override licensing requirements; the tell itself signals regulatory blind spot.

## What I'm explicitly **not** shipping (and why)

- **50x leveraged trading (even virtual)** — Categorically regulated; no educational wrapper makes it OK for v0.
- **AI-managed portfolio / auto-YOLO rebalance** — Removes user agency; crosses into automated financial action.
- **99% prediction accuracy landing page claim** — Cannot be true; will not ship false metrics.
- **Social friend comparison leaderboard** — Requires auth, consent, and moderation we are not building; cuts entirely for v0.
- **Candlestick / intraday chart** — API does not provide the data; faking candles would be dishonest.
- **TWD exchange rate from Frankfurter** — TWD is not in Frankfurter's `/currencies` list (verified 2026-05-23). We will not silently omit it or return fabricated rates.

## What I'm pushing back on (and proposing instead)

- Asked: **Sub-second real-time rates for USD/EUR/JPY/TWD/GBP/CNY/SGD** → I'm proposing: **Daily reference rate board** for supported codes (USD base → EUR, JPY, GBP, CNY, SGD) with an honest "Last updated {date}" badge and an explicit **TWD unsupported** card → Why: Preserves orientation intent without lying about data freshness; surfaces the API gap Riley's list hides.

- Asked: **AI 24h prediction engine @ 99% accuracy** → I'm proposing: **Trend insight panel** with computed 7d/30d % change and period high/low, labeled "historical — not a forecast" → Why: Helps users feel market direction from facts we actually have, without fabricated AI accuracy.

- Asked: **AI-managed portfolio with daily P/L curve** → I'm proposing: **Paper portfolio** ($10k virtual, manual allocation, daily mark-to-market P/L from rate changes only, user-initiated rebalance with preview) → Why: Teaches exposure math without automated trading or leverage.

- Asked: **One-click auto-rebalance YOLO** → I'm proposing: **Manual rebalance** with allocation % preview and confirm step → Why: Same "adjust my exposure" intent; user stays in control.

- Asked: **TradingView candlestick chart** → I'm proposing: **30-day normalized daily line chart** (% change from period start, shared scale) → Why: Only daily series exists; still answers "how did this pair move this month?"

- Asked: **Portfolio comparison vs friends** → I'm proposing: **Export/share your own portfolio snapshot** (deferred if time; no leaderboard) → Why: Preserves "show someone" intent without PII/social infra.

## What I'm shipping in this take-home

Thin slice: **Option B — FX Literacy Lab** (see [docs/SCOPE_RESEARCH.md](docs/SCOPE_RESEARCH.md) for market research and option tradeoffs).

### Scope decision trace

Research identified a gap: travelers and students need **honest daily FX orientation**, not a fake trading terminal. Options A (board only), B (+ paper portfolio), and C (+ terminal polish) were evaluated against Frankfurter constraints and a 3–7 day timeline. **Option B chosen** because it preserves Riley's portfolio intent without traps, justifies Postgres, and fits parallel FE/BE execution. Option C polish items are stretch goals.

### Ship list

1. **BE Frankfurter proxy** — `GET /v1/rates/latest`, `GET /v1/rates/history`, `GET /v1/currencies`; in-memory TTL cache; per-IP rate limit on proxy routes.
2. **Rate board UI** — USD → EUR, JPY, GBP, CNY, SGD with last-updated date; TWD shown as unsupported with explanation.
3. **30-day trend chart** — Normalized % change line chart; null/holiday gaps handled.
4. **Paper portfolio (Postgres)** — Create $10k virtual portfolio, manual holdings allocation, daily MTM P/L vs prior business day.
5. **Manual rebalance flow** — Edit allocations with validation (weights sum to 100%) and preview before save.
6. **One-command run** — `docker compose up --build` (postgres + backend + frontend); local alt `npm run dev`.
7. **Tests** — pytest on BE: rates cache behavior + portfolio MTM calculation; committed before impl (TDD).

### Stretch (Option C — if time remains)

- Dark terminal UI polish, trend insight panel, portfolio snapshot export.

## How to run locally

Command(s) a grader needs to run, in order (typically install + start):

```
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. Backend health: `http://localhost:8000/healthz`.

Local development (without Docker):

```
cp .env.example .env
npm install
npm run dev
```

What environment variables are needed (names only — no values):

- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `BACKEND_PORT`
- `FRONTEND_PORT`
- `NEXT_PUBLIC_API_BASE_URL`
- `BACKEND_INTERNAL_URL`
