# Project Instructions for Claude Code (and any AI assistant)

> Adapted for Topic 1 — MarketMage / FX Literacy Lab. Every rule has a **`> Why:`** line.

## What this project is

A fullstack take-home: thin vertical slice for **Topic 1 (MarketMage)**. Product name: **FX Literacy Lab** — honest daily FX reference rates + paper portfolio simulation. Built for grading, not production traffic.

> Why: Prevents over-building (auth providers, multi-tenancy, observability stacks). Riley's brief contains traps; we ship the defensible kernel documented in `PLAN.md` and `docs/SCOPE_RESEARCH.md`.

## Stack

- **FE**: Next.js (App Router) + TypeScript + Tailwind CSS — `apps/frontend/` — port `:3000`
- **BE**: FastAPI + SQLAlchemy + httpx — `apps/backend/` — port `:8000`
- **DB**: PostgreSQL 16 — paper portfolio persistence only; rates cache stays in-memory on BE
- **Tests**: pytest + httpx TestClient — `apps/backend/tests/`
- **Run**: `docker compose up --build` (grader primary) or `npm run dev` (local FE+BE concurrently)

> Why: Pins library choices so AI does not mix patterns (e.g. Express in a FastAPI project). Matches candidate's pd-care-monorepo conventions.

## Architecture rules

- **FE never calls Frankfurter directly.** All upstream traffic goes FE → BE → `https://api.frankfurter.app`.
- **BE caches** Frankfurter responses (TTL until next business-day refresh) and **rate-limits** per client IP on proxy routes.
- **TWD is unsupported** by Frankfurter — return structured error / UI card; never silently drop or fabricate.

> Why: README and topic spec require BE-as-proxy. TWD mismatch is a graded positive signal.

## Conventions

- **File names**: `kebab-case` (Python modules may use snake_case per PEP 8).
- **React components**: `PascalCase`, one component per file, file matches name.
- **Commits**: `intention(scope): subject — detail` (matches upstream repo style). Examples: `feat(rates):`, `test(portfolio):`, `docs(plan):`. Imperative subject, ≤72 chars.
- **Atomic commits**: one logical change per commit. `test(scope):` before matching `feat(scope):` with verified red→green cycle.

> Why: Grader reads `git log`. TDD level 3 requires test commit SHA to fail before impl lands.

## What to do when in doubt

- **Don't add features outside PLAN.md ship list** without asking the candidate.
- **Don't add dependencies without asking.** Justify in PR description if added.
- **Don't implement Riley's traps** (leverage, AI predictions, real-time labels, social leaderboard, candlesticks).
- **Don't write tests after impl is green.**

> Why: Triage grades cutting scope. Trap implementation is instant negative signal.

## What NOT to do

- **No `.env` files committed.** gitleaks scans full git history.
- **No `node_modules/`, `dist/`, `.next/` committed.**
- **No force-push over published history.**
- **No fake "real-time" or "99% accurate" UI copy.**

> Why: CI auto-fail and rubric negative signals.

## Reading the diff

Before every commit, read every changed line. If you cannot explain a line to a grader, delete it.

> Why: Unedited AI dead code is the most common failure mode on candidate PRs.

## Key docs (read order)

1. `PLAN.md` — refuse-first scope
2. `docs/SCOPE_RESEARCH.md` — market/API decision trace
3. `topics/topic-1-marketmage.md` — Riley's brief + API facts
4. `GRADING.md` — rubric
