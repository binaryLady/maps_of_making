# Supabase setup

Connects the deployed site's gate, telemetry, and whitelabel to a Supabase
project. The code ships with empty placeholders and runs **local-only** until
an instance is wired in — instance specifics (URL, key) live in deployment
environment variables, never in this repository.

## 1 · Create the tables

In the Supabase dashboard → SQL editor, run both files from this directory:

1. `schema.sql` — `maps_visitors` (gate sign-ins) + `maps_telemetry_events`
2. `whitelabel.sql` — `maps_site_config` (brand / theme / gate copy) with
   seeded starter rows

3. `rls.sql` — member/super-admin tiers and the hardened policies (run last;
   edit the placeholder super-admin email first)

### Naming rule — this database may be shared

Every object this project creates is **prefixed**, so several apps can live in
one Supabase project without collision:

| prefix | belongs to | objects |
|---|---|---|
| `maps_` | Maps of Making | tables `maps_visitors`, `maps_telemetry_events`, `maps_site_config`; indexes `maps_telemetry_events_ts_idx`, `maps_telemetry_events_event_idx`; function `maps_gate_signin` |
| `ttm_` | shared across apps | table `ttm_admins`; functions `ttm_is_super`, `ttm_jwt_email`, `ttm_guard_visitor_flags`; trigger `ttm_guard_flags` |

Anything added later must follow the same rule — an unprefixed name in a
shared project is a collision waiting to happen. Every file here is
idempotent and safe to re-run.

## 2 · Wire the deployment

Vercel → project → **Settings → Environment Variables** → add:

| Variable | Value | Where to find it |
|---|---|---|
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Supabase → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | `sb_publishable_…` (or legacy `eyJ…` anon key) | Supabase → Settings → API → Project API keys |

Redeploy. `build.sh` injects both into `web/ttm/config.js` at build time —
publishable/anon keys are public by design (they ship to every browser;
row-level security is the actual boundary), the env indirection just keeps
instance identity out of the repo.

## 3 · Verify

- Open the site in a private window → sign the gate → Supabase → Table editor
  → `maps_visitors` shows the row.
- Mission Control (`/admin/`) → the Telemetry and Visitors panels populate;
  the Whitelabel card's **Publish** buttons write `maps_site_config`.
- Without the env vars everything still works local-only: the gate stores on
  the device, telemetry logs to the console, and the admin panels say exactly
  what's missing.

## Local development

The static pages read `web/ttm/config.js` directly. For a wired local run,
substitute the placeholders by hand (do not commit the result):

```bash
sed -i "s|%SUPABASE_URL%|https://<ref>.supabase.co|; s|%SUPABASE_ANON_KEY%|<key>|" web/ttm/config.js
```
