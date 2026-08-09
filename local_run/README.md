# local_run — container-free local deployment

Runs the complete Maps of Making stack as native host processes, for
environments where Podman/Docker images can't be pulled (restricted networks,
sandboxes) or when you just want fast iteration without containers.

Functionally equivalent to `make devdeploy`: same code, same ports, same data
directories as the compose stack.

| Service | Port | How it runs here |
|---|---|---|
| Oxigraph (SPARQL store) | 7878 | `oxigraph_server.py` — pyoxigraph behind a minimal SPARQL 1.1 Protocol server, persisting to `data/oxigraph/` |
| link_handler (heartbeat engine) | 8000 | `venv/bin/uvicorn main:app` from `infra/link_handler/`, host paths via `link_handler_config.yaml` + env |
| nginx (web + proxy) | 8080 | system nginx with `nginx-app.conf` (adapted from `infra/nginx/conf.d/app.conf`: upstreams → 127.0.0.1, root → repo `web/`) |
| Dendrite (Matrix homeserver) | 8008 | built from source (`go build ./cmd/dendrite`), Postgres 16 backing |
| Bernard (Matrix bot) | — | `harness/main_matrix.py` with `PYTHONPATH=local_run` (the `bot/` package here mirrors the compose bind-mounts: `infra/bot/*` + link_handler's `schema.py`/`bot_keys.py`) |

## Bring-up order

1. `python3 -m venv venv && venv/bin/pip install pyoxigraph playwright -r scripts/requirements.txt -r infra/link_handler/requirements.txt -r harness/requirements.txt`
2. `.env` at repo root — `.env.example` plus `DENDRITE_DB_PASSWORD`, `MATRIX_HOMESERVER=http://localhost:8008`, `MATRIX_USER_ID=@bernard:localhost`, `MATRIX_ACCESS_TOKEN`, `MATRIX_DEVICE_ID` (the last two after step 7). `BOT_KEY_SECRET` must be a real Fernet key.
3. `venv/bin/python local_run/oxigraph_server.py &` then `bash scripts/load_ontology.sh http://localhost:7878`
4. link_handler (from `infra/link_handler/`, env: `OXIGRAPH_ENDPOINT=http://localhost:7878`, `GEOJSON_OUTPUT=<repo>/web/data/spaces.geojson`, `CONFIG_PATH=<repo>/local_run/link_handler_config.yaml`, `SNAPSHOT_DB_PATH=<repo>/data/tasks/snapshot_store.db`, `BOT_KEYS_DIR=<repo>/data/bot-keys`, `SCRIPTS_DIR=<repo>/scripts`): `uvicorn main:app --port 8000 &`
5. nginx: symlink `local_run/nginx-app.conf` into `/etc/nginx/conf.d/`, create `infra/nginx/.htpasswd` (`admin:$(openssl passwd -apr1 <pw>)`), start nginx → map at http://localhost:8080
6. Dendrite: init Postgres 16 cluster + `dendrite` user/db, generate `matrix_key.pem` with `generate-keys`, adapt `dendrite-sample.yaml` (server_name `localhost`, Postgres DSN, `registration_shared_secret`), run `dendrite --config … --http-bind-address 0.0.0.0:8008 &`
7. `create-account --config … --username bernard`, log in via `POST /_matrix/client/v3/login`, put token + device in `.env`
8. Bernard: from `harness/`, env from `.env` + `LINK_HANDLER_URL=http://localhost:8000` + `PYTHONPATH=<repo>/local_run` → `python main_matrix.py &`
9. Seed: `seed_bundle.py` with `data/seed-lists/*.bundle.json` (offline-friendly), or `seed_spaceapi.py` when the SpaceAPI directory is reachable; then `POST localhost:8000/api/heartbeat/run`

## Offline tile stubs

When `tiles.openfreemap.org` / `unpkg.com` are unreachable, the map would hang
on its loader. Two accommodations, both inert in production:

- MapLibre + pmtiles are vendored in `web/vendor/` (from npm) and referenced
  relatively in `maps-of-making.html` — removes the unpkg dependency entirely.
- `web/app.js` swaps basemap/glyph/terrain URLs to local `/tiles/` stubs
  (served by `nginx-app.conf`, empty tiles) **only when the page is opened on
  localhost**. Pins, interactions and zoom-theming all work; street detail is
  blank offline.

## Live test spaces

`web/test-spaces/*.json` are schema.org space files served by our own nginx —
register them with `POST /api/register-url {"url": "http://localhost:8080/test-spaces/<f>.json"}`
to get real heartbeat-polled, "claimed" spaces without any external lab.
The Mother Sands canary works the same way (`scripts/canary_scenarios.py` +
`scripts/canary_ops.py` with `CANARY_ENDPOINT_URL=http://localhost:8080/canary/mother-sands.json`).
