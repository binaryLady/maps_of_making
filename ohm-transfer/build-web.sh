#!/usr/bin/env bash
# Assemble the static TTM dashboard (web/) into public/ for Vercel.
# The C# application is untouched — this only ships the browser dashboard.
set -euo pipefail
cd "$(dirname "$0")"

rm -rf public
mkdir -p public
cp -r web/. public/

# Inject Supabase credentials from Vercel env vars (same shared project as
# the other TTM sites; this dashboard's tables are prefixed ohm_). Unset
# vars leave the placeholders, and the stack runs in local-only mode.
if [ -n "${SUPABASE_URL:-}" ]; then
  sed -i "s|%SUPABASE_URL%|${SUPABASE_URL}|" public/ttm/config.js
fi
if [ -n "${SUPABASE_ANON_KEY:-}" ]; then
  sed -i "s|%SUPABASE_ANON_KEY%|${SUPABASE_ANON_KEY}|" public/ttm/config.js
fi

echo "build-web: $(find public -type f | wc -l) files staged in public/"
