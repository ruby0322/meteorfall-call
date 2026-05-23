---
name: commit-discipline
description: Structure commits so the git log itself becomes a TDD + scope-discipline artifact.
---

# Commit Discipline

The grader reads `git log` before reading the code. The shape of that log is itself a signal.

## Message format

**`intention(scope): subject — detail`**

| intention | scope examples |
|---|---|
| `docs` | `plan`, `scope`, `agents`, `submission` |
| `feat` | `rates`, `portfolio`, `ui`, `docker` |
| `test` | `rates`, `portfolio` |
| `chore` | `scaffold`, `deps` |
| `refactor` | `rates`, `portfolio` |

Matches upstream `CloudBater/meteorfall-call` commits like `docs(topic-1): flag the ECB-reference-set currency mismatch`.

## The TDD pattern

For every shippable unit of behavior:

1. `test(scope): <behavior>` — commit failing test alone. pytest must fail at this SHA.
2. `feat(scope): <minimal impl>` — just enough to pass. No bonus features.
3. `refactor(scope): <cleanup>` — optional, only after green.

> Why: Only path to TDD rubric level 3. Test+feat in one commit caps at 2.

## Phase 0 commit sequence (this project)

1. `docs(scope): add market research briefing for FX Literacy Lab niche`
2. `docs(plan): triage Riley brief and commit to Option B FX Literacy Lab`
3. `docs(agents): adapt CLAUDE.md and AGENTS.md for monorepo stack`

Then code phases begin with `chore(scaffold): …`.

## Atomic commits

One logical concern per commit. If the diff spans unrelated areas, split it.

- ✅ `feat(rates): add /v1/rates/latest with Frankfurter proxy`
- ❌ `WIP` or single "submission dump" with 47 files

## PR description (Git hygiene level 3)

- Features cut from Riley's brief and why
- Pushback items with alternatives proposed
- Pointer to `PLAN.md` and `docs/SCOPE_RESEARCH.md`
- Screenshot or terminal paste of local run

> Why: Description + atomic commits both required for level 3; neither substitutes for the other.

## Before every commit

1. `git diff --cached`
2. One thing per commit?
3. Read the message — strip AI adjectives
4. For `test(scope):` commits, run pytest and confirm RED

Use `/usr/bin/git commit` if older git on PATH errors on hooks.
