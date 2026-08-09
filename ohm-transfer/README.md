# OHM dashboard — transfer bundle

TTM web dashboard for `binaryLady/openhardwaremonitor`, staged as plain files
because the authoring session had push access to this repo but not to the OHM
fork. Transplant into a clone of the OHM fork, branch
`claude/ttm-web-dashboard`, then push + open a draft PR against
`binaryLady:master`. Delete this branch afterwards.

## Transplant recipe

From the OHM clone root, with this repo cloned at `$MAPS` (branch
`ohm-dashboard-transfer` for `ohm-transfer/`, branch `mom-demo` for the
shared assets — they are byte-identical between the two sites):

```bash
git checkout -b claude/ttm-web-dashboard
mkdir -p web/ttm web/vendor web/admin supabase

# 1. unique files from this bundle
cp $MAPS/ohm-transfer/web/index.html          web/index.html
cp $MAPS/ohm-transfer/web/dashboard.js        web/dashboard.js
cp $MAPS/ohm-transfer/web/demo-data.js        web/demo-data.js
cp $MAPS/ohm-transfer/web/admin/index.html    web/admin/index.html
cp $MAPS/ohm-transfer/web/ttm/stack.js        web/ttm/stack.js
cp $MAPS/ohm-transfer/web/ttm/theme.js        web/ttm/theme.js
cp $MAPS/ohm-transfer/supabase/schema.sql     supabase/schema.sql
cp $MAPS/ohm-transfer/vercel.json             vercel.json
cp $MAPS/ohm-transfer/build-web.sh            build-web.sh

# 2. components.css = maps base + additions (concatenate, in this order)
#    (checkout mom-demo copies first: git -C $MAPS checkout mom-demo -- web)
cat $MAPS/web/ttm/components.css \
    $MAPS/ohm-transfer/web/ttm/components-additions.css > web/ttm/components.css
# sanity: wc -c web/ttm/components.css  ->  expect 22630

# 3. shared assets, byte-identical on maps mom-demo
cp $MAPS/web/ttm/tokens.css   web/ttm/tokens.css
cp $MAPS/web/ttm/toast.js     web/ttm/toast.js
cp $MAPS/web/ttm/config.js    web/ttm/config.js
cp $MAPS/web/vendor/supabase.js web/vendor/supabase.js
cp $MAPS/web/favicon.ico      web/favicon.ico
cp $MAPS/web/icon.svg         web/icon.svg
cp $MAPS/web/apple-icon.png   web/apple-icon.png

# 4. gitignore the build output
grep -qx 'public/' .gitignore || printf 'public/\n' >> .gitignore

# 5. smoke checks (all must pass before committing)
node --check web/dashboard.js
node --check web/demo-data.js
node --check web/ttm/stack.js
node --check web/ttm/theme.js
bash build-web.sh          # expect: 14 files staged in public/
```

Commit (single commit is fine), push `claude/ttm-web-dashboard`, open a
**draft PR** against `binaryLady:master`.

## Suggested commit message

```
Add TTM web dashboard for the embedded sensor server

A static browser dashboard (web/, deployable on Vercel) that consumes the
embedded HTTP server's /data.json feed (Utilities/HttpServer.cs
GenerateJSON): parses the preformatted display-string tree, groups sensors
by hardware with threshold coloring, and generates a SpaceAPI-style map
bridge fragment for publishing the machine on Maps of Making. Includes an
animated demo feed (?demo=1), the TTM design stack (tokens + component
library + accessible drawer menu + toasts), a Supabase-backed visitor gate
and telemetry (ohm_-prefixed tables in the shared project, fail-soft
local-only without credentials), and a gated operator-only /admin/ page.
build-web.sh + vercel.json stage web/ into public/ for static deploy; the
C# application is untouched.
```

## Notes for the landing session

- The four original commits (dashboard, supabase stack, admin gating,
  component refactor) exist in the authoring session's container; this
  bundle is their squashed file state. History fidelity is not required.
- Verified before transfer: 48 demo sensor rows render, gate shows/clears,
  admin allowed+denied paths work, terminal theme flips correctly, zero
  console errors (headless Chromium).
- Vercel: the user connects the repo via git integration; vercel.json
  carries build command and output dir. Env vars SUPABASE_URL /
  SUPABASE_ANON_KEY enable the gate/telemetry (same values as the
  maps-of-making project).
- After the PR lands, ask the user to delete the `ohm-dashboard-transfer`
  branch from this repo (session credentials cannot delete remote branches).
