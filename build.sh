#!/usr/bin/env bash
set -euo pipefail
# Static demo build for Vercel git integration (vercel.json points here).
# Assembles the map + wizard from web/ into public/ with the committed data
# snapshot. The result is a self-contained, inert demo: no backend, no
# heartbeat, no polling of any space's endpoint — it reads only its own files.
# Gate the deploy on the freshness test suite (same logic the map ships)
node --test tests/web/freshness.test.mjs

mkdir -p public
cp -r web/. public/
# Not servable statically / not needed in the demo
# (test-fixtures and test-spaces stay in — they're the worked examples of what
#  a space publishes; admin/ ships too — it's the TTM Mission Control dashboard)
rm -rf public/mothersands public/canary \
       public/demo-data public/design-canvas.jsx "public/ZieZo Activiteiten.html" \
       public/genjson/bernard_copy.yaml

# TTM stack: inject Supabase credentials from the Vercel project env.
# Unset env → placeholders stay → the stack runs local-only by design.
if [ -n "${SUPABASE_URL:-}" ]; then
  sed -i "s|%SUPABASE_URL%|${SUPABASE_URL}|" public/ttm/config.js
fi
if [ -n "${SUPABASE_ANON_KEY:-}" ]; then
  sed -i "s|%SUPABASE_ANON_KEY%|${SUPABASE_ANON_KEY}|" public/ttm/config.js
fi
# The committed snapshot becomes the path the app fetches
mkdir -p public/data
cp web/demo-data/spaces.snapshot.geojson public/data/spaces.geojson
# Vercel needs an index at the root; keep the original filename working too
cp public/maps-of-making.html public/index.html
# bernard_copy.json is generated from the YAML source (gitignored, so a fresh
# clone doesn't have it — this is what broke the first Vercel build)
if [ ! -f public/genjson/bernard_copy.json ]; then
  npx --yes js-yaml web/genjson/bernard_copy.yaml > public/genjson/bernard_copy.json
fi
# genjson fetches /bernard_copy.json from the site root (it lives on its own
# subdomain in production) — mirror it to the root here
cp public/genjson/bernard_copy.json public/bernard_copy.json
echo "demo bundle assembled:" && du -sh public
