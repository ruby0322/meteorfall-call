# Working Agreement — You and Your AI Tools

> Adapted for MarketMage / FX Literacy Lab take-home. Rules encode habits that produce better-graded PRs.

## When to use the AI

- **Scaffolding** — monorepo layout, Docker Compose, FastAPI router wiring, Next.js pages.
- **Writing tests for a known contract** — "given this `/v1/rates/latest` response schema, write cache + TWD edge-case tests."
- **Reformatting / refactoring** — rename, extract service, switch patterns across files (read the diff).
- **Drafting docs** — README run sections, PR descriptions, prose polish on `PLAN.md` (candidate owns decisions).
- **Looking up shapes** — Frankfurter API response formats, Next.js rewrite config.

> Why: AI is highest-leverage when intent is clear and constraints are mechanical.

## When to NOT use the AI

- **Product decisions** — what to cut from Riley's brief, counter-proposals, Option B vs C scope. Rubric grades *your* taste.
- **Risk decisions** — leveraged FX, fabricated accuracy, disclaimer-laundering. Ownership is yours.
- **First-pass on bugs** — read the code 5 minutes before asking.
- **Anything you wouldn't sign your name to.**

> Why: Senior judgement is the screen; code generation is commodity.

## Reading the diff — non-negotiable

After every AI-assisted change, before `git add`:

1. `git diff` staged + unstaged together
2. Read every changed line
3. If a line confuses you, ask for explanation, then decide
4. If you cannot justify a line to a grader, delete it

> Why: AI-generated dead code survives only when diffs are skipped.

## Commit messages

Format: **`intention(scope): subject`** — matches upstream `CloudBater/meteorfall-call` history.

- ✅ `feat(rates): add Frankfurter proxy with daily TTL cache`
- ✅ `test(portfolio): assert mtm pl from rate change`
- ✅ `docs(scope): add market research briefing for FX Literacy Lab niche`
- ❌ `feat: implement comprehensive currency exchange rate fetching with advanced caching`

Body paragraphs encouraged for `docs` commits — explain *why*, not just *what*.

> Why: Grader reads `git log --oneline`. Scoped prefixes show discipline; adjectives hide scope.

## TDD commit order

For each behavior unit:

1. `test(scope): …` — commit failing test alone; pytest must fail at this SHA
2. `feat(scope): …` — minimal impl to green
3. `refactor(scope): …` — optional cleanup after green

> Why: Only path to TDD rubric level 3.

## Boundaries

- **Don't auto-commit.** Review before every commit.
- **New package → pause.** Is there a 3-line vanilla version?
- **Don't implement traps** even if the brief says to. See `PLAN.md`.

> Why: Operational habits that scale from take-home to production.

## Project-specific reminders

- Scope locked in `PLAN.md` + `docs/SCOPE_RESEARCH.md`. Ask before expanding.
- Use `/usr/bin/git` for commits if `/usr/local/bin/git` (2.15) errors on hooks.
- Phase gates: candidate approves scope before each major phase.
