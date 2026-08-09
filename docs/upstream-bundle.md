# Upstream contribution bundle

Prepared contributions for the canonical project, staged entirely inside this
fork. Nothing has been sent upstream; submitting is a deliberate, manual act
by the fork owner, on their timeline, using the drafts below.

## Contents

| Branch (this fork) | What it carries | Depends on |
|---|---|---|
| `contrib/frontend-test-suite` | First frontend tests: `web/freshness.js` extraction (call sites unchanged), `tests/web/` node suite (16/16), the Test Bench page, the `?mock=1` hook, an nginx `/test/` location | nothing |
| `contrib/optional-theming` | Opt-in theming/whitelabel mechanism: `--mom-*` tokens defaulting to the existing zine palette, one neutral dark theme, fail-soft `/site.config.json` loader for brand text + token overrides | nothing |

Both branches are cut from `upstream/mom-demo` and contain **no fork-specific
material** — no brand colors, no Supabase, no analytics, no gate. Each is one
topic, reviewable in one sitting.

## Rationale (the pitch, honestly made)

**Why the test suite.** The map's freshness logic — three axes and a
precedence rule — is the product's core claim ("the map tells you what's
alive"). It currently lives inside a 1,800-line IIFE with no tests. The
extraction moves it verbatim into a pure module consumed by the app, an
interactive bench, and a node test run; the suite pins the bucket boundaries,
the epoch-seconds parsing, and the precedence decisions (long silence beats an
"open" claim; a broken endpoint beats it too). Cost to upstream: two script
tags and thin aliases. Benefit: the core semantics can no longer regress
silently, and `node --test` needs no dependencies.

**Why optional theming.** Networks that deploy their own node will want their
own identity. Today that means forking the CSS. The layer offers a sanctioned
path: design tokens whose defaults reproduce the zine look byte-for-byte, an
optional config file for brand text and token overrides, and a hard rule that
the semantic pin vocabulary (green = alive, red = broken, cobalt = claimed) is
not themable. Off by default: no attribute + no config = upstream look,
unchanged. This converts future forks into configurations.

## How to submit (when ready)

1. Refresh against upstream first:
   `git fetch upstream && git rebase upstream/mom-demo contrib/<branch>`
   then rerun `node --test tests/web/freshness.test.mjs` (suite branch).
2. Push the rebased branch to this fork.
3. Open the pull request from the fork branch against
   `touchthesun/maps_of_making`, base `mom-demo` (GitHub → New pull request →
   compare across forks).
4. Paste the matching draft below. Submit the **test suite first** — it's the
   least invasive and builds reviewer trust for the theming PR.

## Draft PR #1 — frontend test suite

> **Title:** Frontend test suite for the freshness axes + interactive test bench
>
> The freshness lifecycle is the map's core promise, and its logic currently
> can't be tested in isolation. This PR extracts the three axes and the marker
> precedence rule verbatim into `web/freshness.js` (thin aliases keep every
> `app.js` call site unchanged) and adds:
>
> - `tests/web/freshness.test.mjs` — dependency-free `node --test` suite:
>   bucket boundaries, epoch-seconds `updated_at`, unparseable timestamps,
>   precedence rules, per-feature `thresholds_override`, missing-thresholds
>   fallback. 16/16.
> - `web/test/` — a test bench that generates mock FeatureCollections for all
>   eight states, asserts them against the shipped module in-browser, and can
>   open the real map on the mock via an explicit `?mock=1` hook
>   (localStorage, same-origin, falls through to real data).
> - an nginx `/test/` location following the `/genjson/` pattern.
>
> No behavior changes; happy to split the bench from the suite if preferred.

## Draft PR #2 — optional theming / whitelabel layer

> **Title:** Optional theming layer — tokens + site config, off by default
>
> Networks deploying their own node currently have to fork the CSS to carry
> their identity. This adds a sanctioned, opt-in path that changes nothing by
> default:
>
> - `web/theming/tokens.css` — `--mom-*` design tokens whose defaults mirror
>   the existing zine palette exactly, plus one neutral dark theme. With no
>   `data-mom-theme` attribute the page renders as today.
> - `web/theming/theme.js` — fail-soft loader for an optional
>   `/site.config.json` (brand name/tagline/title, default theme, token
>   overrides); a 404 means the upstream look, by design.
> - The semantic pin colors are explicitly out of theming scope (README).
>
> Two inert includes in `maps-of-making.html`; no dependencies, no services.
> Motivation: turn future visual forks into configurations.

## Etiquette checklist before either submission

- [ ] Rebased on current `upstream/mom-demo`; tests green
- [ ] `python3 scripts/check_docs.py` clean if docs were touched
- [ ] PR body states behavior-neutrality and offers to split/adjust
- [ ] No fork branding, keys, data files, or generated artifacts in the diff
