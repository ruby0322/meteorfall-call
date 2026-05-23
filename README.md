# Fullstack Intern Vibe-Coding Screen (Take-Home)

> Welcome to the screen. Read this entire document **before** you start coding.

You are a fullstack engineer joining an early-stage startup. The startup is run by **Riley Vance**, a founder with strong opinions, weak technical instincts, and an Olympic-level capacity for sending dramatic messages at unhinged hours.

Riley is going to send you a brief. The brief will demand a startup-launching, investor-impressing, world-changing product. The brief will be partially impossible, partially illegal, partially incoherent.

Your job is **not** to ship Riley's vision. Your job is to:

1. Read carefully.
2. Identify the *real* good idea hiding inside the rant.
3. Push back on the impossible/risky/expensive parts — politely, with reasoning.
4. Ship a defensible thin slice that talks to a real public API.
5. Document everything in `PLAN.md`.

This is a screen for senior judgement under stakeholder pressure, not for raw coding speed.

> **About this screen, in plain language**: we hire one person from this round. If that's not you, we still want you to walk away with something — the rubric you read here, the [`examples/`](./examples) we ship with this repo, and the experience of building a real take-home with AI tooling. Treat it as a learning artifact, not just a filter.

---

## Mechanics

- **Format**: take-home. The HR interview invitation email tells you which topic you got.
- **Deadline**: open your PR **at least 24 hours before** your scheduled interview slot. We need time to grade it before we sit down with you.
- **Tools**: any tool, any method. Claude Code, Codex, Cursor, web research, pair programming with a friend — whatever you'd actually reach for. The whole point is to see how you work, not to handicap you.
- **Submission flow**: fork this repo to your own GitHub account, push `submission/<your-github-username>` to your fork, and open a PR from your fork against `CloudBater/meteorfall-call:main`. You don't have write access to the upstream repo — that's expected.
- **CI on your PR**: if this is your first PR to this repo, GitHub holds workflow runs for maintainer approval. Empty checks aren't a failure — the grader will release them when they pick up the PR. Don't force-push to "fix" it.
- **Stack**: free choice for FE and BE. Both are required.
- **BE proxies the upstream API**: even if the API you pick is keyless, the FE must call your BE, and your BE calls the upstream. Add caching / rate-limit handling on BE. This is a production-engineering signal.
- **No secrets in source**: even though most APIs in this screen don't need a key, treat the discipline as if they did. Use `.env`. Anything that looks key-shaped in git history triggers an auto-fail.
- **One-command local run**: `make dev`, `npm run dev`, `docker compose up`, your call. The grader must be able to start it without reading code.

## How a topic gets assigned

There are three topics in [`topics/`](./topics). They are publicly visible — read them all when you get the invite. The HR email tells you which one is yours. Different candidates may get different topics; sometimes the topic is randomized, sometimes intentional.

All three pick from [public-apis](https://github.com/public-apis/public-apis) — keyless, production-grade, real users would use them.

| | Topic | Upstream API | One-line pitch |
|---|---|---|---|
| 1 | [MarketMage](./topics/topic-1-marketmage.md) | [ExchangeRate.host](https://exchangerate.host) | Real-time FX dashboard with "AI" portfolio rebalancing |
| 2 | [Crumb](./topics/topic-2-crumb.md) | [TheMealDB](https://www.themealdb.com/api.php) | Mukbang-AI cooking app with auto-nutritionist |
| 3 | [DevScore](./topics/topic-3-devscore.md) | [GitHub REST API](https://docs.github.com/en/rest) | FICO-style developer ranking dashboard |

## What you submit

A pull request against `main` with:

1. A `PLAN.md` (copied from `PLAN.template.md` and filled in **first**)
2. A working thin slice that runs locally with one command and talks to the real upstream API through your BE
3. At least one test — committed *before* its impl earns the top TDD score (commit timestamps are graded)
4. A PR description that includes:
   - The list of features you cut and why
   - What you pushed back on (and what you proposed instead)
   - A loom, screenshot, or terminal paste showing it running locally (any visual proof — optional but earns the top "Runs locally" score)

## CI auto-fail (gates the human review)

If any of these red on your PR, a human won't even look:

- Any API-key-shaped string appears anywhere in git history (`gitleaks`)
- `node_modules/`, `dist/`, `.next/`, or build artifacts committed
- No `PLAN.md` at repo root
- Zero test files in the PR diff

## Setup

Fork `CloudBater/meteorfall-call` to your own GitHub account first (use the **Fork** button in the top-right of the repo page), then:

```bash
# clone YOUR fork, not the upstream
git clone https://github.com/<your-github-username>/meteorfall-call.git
cd meteorfall-call
cp .env.example .env
# .env stays empty unless your topic's API needs a key (most don't)
cp PLAN.template.md PLAN.md
# fill PLAN.md before you start coding
```

When you're ready to submit:

```bash
git checkout -b submission/<your-github-username>
# ... commit your work ...
git push -u origin submission/<your-github-username>
```

Then open a PR on GitHub from `<your-github-username>:submission/<your-github-username>` → `CloudBater/meteorfall-call:main`. The "Compare & pull request" banner appears on your fork after the push.

## On AI tools

Use them. Claude Code, Codex, Cursor — whatever you reach for daily. We want to see how you collaborate with AI, not avoid it. If your repo includes a `.claude/`, an `AGENTS.md`, or visible prompt iterations in your commit history, that is a positive signal.

What we are *not* looking for: unedited AI output dumped wholesale into a PR. Read the diff before you commit it.

See [`examples/`](./examples) for working `CLAUDE.md`, `AGENTS.md`, and skill files that demonstrate how we expect a thoughtful engineer to configure their AI tooling for a project this size. You can copy them as a starting point.

---

Read [`GRADING.md`](./GRADING.md) before you start. Then check out [`examples/`](./examples).

Good luck. Riley's about to send you a brief.

---

## MarketMage submission (Topic 1)

This fork implements **FX Literacy Lab** — a defensible slice of Topic 1 with full triage documented in [`PLAN.md`](./PLAN.md).

### One-command run (Docker — recommended for graders)

```bash
cp .env.example .env
npm run docker:up
```

Open [http://localhost:3000](http://localhost:3000). Backend health: [http://localhost:8000/healthz](http://localhost:8000/healthz).

Stop: `npm run docker:down`

### Local development (without Docker)

```bash
cp .env.example .env
npm install
npm --prefix apps/frontend install
npm run dev
```

Runs Next.js on `:3000` and FastAPI on `:8000` via the project venv.

### Tests

```bash
npm test
```
