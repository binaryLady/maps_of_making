# Contributing — git setup

## Fork topology

| Remote | Repository | Role |
|---|---|---|
| `upstream` | `touchthesun/maps_of_making` | **Canonical** project (source of truth). Working branch: `mom-demo`. |
| `origin` | your fork (e.g. `binaryLady/maps_of_making`) | Where you push; PRs to upstream come from here. |

> Note: `nicolasdb`'s copy is older history — do not target it. The canonical
> upstream is `touchthesun/maps_of_making`.

## One-time setup

```bash
git clone https://github.com/<you>/maps_of_making.git
cd maps_of_making
git remote add upstream https://github.com/touchthesun/maps_of_making.git
# safety: never push to upstream by accident — PRs only
git remote set-url --push upstream DISABLED-push-to-fork-instead
git config remote.pushdefault origin
git fetch upstream
```

## Everyday flow

```bash
# start a piece of work from the freshest canonical state
git fetch upstream
git checkout -b feat/my-change upstream/mom-demo

# ...work, commit...

git push -u origin feat/my-change
# open the PR against touchthesun/maps_of_making, base mom-demo
```

Keep your fork's `mom-demo` a fast-forward mirror of upstream when possible:

```bash
git checkout mom-demo
git pull --ff-only upstream mom-demo
git push origin mom-demo
```

If your fork's `mom-demo` carries experiments upstream doesn't have (this fork
currently does — theming, admin, Supabase stack), branch upstream-bound work
from `upstream/mom-demo`, **not** from your fork's `mom-demo`, so upstream PRs
stay free of fork-only commits.

## Before opening an upstream PR

- `node --test tests/web/freshness.test.mjs` — frontend logic suite must pass
- `python3 scripts/check_docs.py` — docs staleness tripwire, if you touched docs
- One topic per PR; small is welcome. Data files, secrets (`.env`,
  `infra/dendrite/config/`, `infra/nginx/.htpasswd`) and `data/` never belong
  in a commit — they are gitignored for a reason.

## Local development

- Containers: `.env` from `.env.example` (see `local_run/README.md` for the
  five extra required variables), then the compose files in `infra/`.
- No containers: `local_run/README.md` documents the full container-free
  bring-up (Oxigraph, link handler, nginx, Dendrite, Bernard).
- Static demo only: `bash build.sh` assembles `public/`; any static server
  can serve it.
