---
name: triage-brief
description: Take a chaotic stakeholder brief (the Riley pattern) and produce a PLAN.md that scores well on the rubric.
---

# Triage a Chaotic Brief

Riley's pitches are the explicit test of this rubric dimension. They contain a kernel of a good idea wrapped in 80% impossible, illegal, or scope-theatre demands. Your job is the unwrapping.

## Artifacts for this project

1. **`docs/SCOPE_RESEARCH.md`** — market/API research and Option A/B/C decision trace (write first)
2. **`PLAN.md`** — refuse → counter-propose → ship (write second, cross-link research)
3. **Code** — only after both docs are committed

> Why: Phase 0 leaves auditable traces of scope decision-making for graders and agents.

## The four lists every brief produces

Read the topic file once. Then make four lists in `PLAN.md` *before* any code:

1. **The kernel** — actual interesting idea, one sentence
2. **What I'm shipping** — thin vertical slice
3. **Counter-proposals** — real need, impossible/wrong implementation → alternative preserving intent
4. **Outright cuts** — no defensible kernel

> Why: Triage level 3 requires at least one counter-proposal. "Ship or cut" only caps at level 2.

## Trap list (Topic 1 — MarketMage)

- Sub-second "real-time" (Frankfurter is daily)
- AI 24h prediction @ 99% accuracy
- 50x leverage / unlicensed "educational" trading
- Auto-YOLO rebalance on AI signal
- Social portfolio leaderboard
- Candlestick chart without OHLC data
- TWD silently dropped (not in Frankfurter `/currencies`)
- "Cousin is a lawyer" / disclaimer-laundering

> Why: Implementing traps is negative signal regardless of polish.

## How to apply with AI tooling

Don't ask AI to author `PLAN.md` or `SCOPE_RESEARCH.md`. Write yourself, then stress-test: "What trap did I miss?" Take or reject suggestions; edit your version.

> Why: Triage grades *your* thinking shape, not ChatGPT prose.
