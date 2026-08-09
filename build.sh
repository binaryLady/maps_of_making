#!/usr/bin/env bash
set -euo pipefail
# Static demo build for Vercel git integration (vercel.json points here).
# Assembles the map + wizard from web/ into public/ with the committed data
# snapshot. The result is a self-contained, inert demo: no backend, no
# heartbeat, no polling of any space's endpoint — it reads only its own files.
mkdir -p public
cp -r web/. public/
# Not servable statically / not needed in the demo
# (test-fixtures and test-spaces stay in — they're the worked examples of what
#  a space publishes, useful for demos and for pasting into validators)
rm -rf public/mothersands public/admin public/canary \
       public/demo-data public/design-canvas.jsx "public/ZieZo Activiteiten.html" \
       public/genjson/bernard_copy.yaml
# The committed snapshot becomes the path the app fetches
mkdir -p public/data
cp web/demo-data/spaces.snapshot.geojson public/data/spaces.geojson
# Vercel needs an index at the root; keep the original filename working too
cp public/maps-of-making.html public/index.html
# genjson fetches /bernard_copy.json from the site root (it lives on its own
# subdomain in production) — mirror it to the root here
cp public/genjson/bernard_copy.json public/bernard_copy.json
echo "demo bundle assembled:" && du -sh public
