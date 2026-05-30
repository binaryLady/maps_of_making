# Story 9.1: Subdomain & Infra — `genjson.mapsofmaking.org` DNS + Nginx + Static Scaffold

**Status:** ready-for-dev
**Epic:** Epic 9 — Bernard's Workshop (M1 — must-ship)
**Milestone:** M1 Floor & Core (Stories 9.1–9.5)
**Depends on:** Story C.X (done ✓)
**Blocks:** Stories 9.2, 9.3, 9.4, 9.5 (all M1 stories require subdomain to be up)

---

## Story

As a space coordinator arriving at `genjson.mapsofmaking.org`,
I want a fast-loading, mobile-friendly page with no tracking and no login,
So that the wizard is reachable and trustworthy before any content is entered.

---

## Acceptance Criteria

**Given** the hetzner-gateway nginx config and existing cert infrastructure
**When** Story 9.1 lands
**Then** DNS A-record for `genjson.mapsofmaking.org` points to the hetzner gateway IP

**And** `infra/gateway-nginx/08-genjson-mapsofmaking.conf` exists with:
  - HTTP→HTTPS 301 redirect block (same as `06-mapsofmaking.conf` pattern)
  - HTTPS server block for `genjson.mapsofmaking.org`
  - `ssl_certificate` / `ssl_certificate_key` from `live/genjson.mapsofmaking.org/` (separate cert — not the wildcard)
  - `proxy_pass http://maps-nginx/genjson/` (URI prefix substitution — same pattern as `07-admin-mapsofmaking.conf`)
  - `add_header X-Frame-Options SAMEORIGIN` — not ALLOWALL/DENY
  - `add_header Content-Security-Policy "default-src 'self' 'unsafe-inline'"` — no third-party script CDNs
  - Standard security headers (X-Content-Type-Options, Referrer-Policy, HSTS) matching existing patterns

**And** `web/genjson/index.html` exists with:
  - `<title>Bernard's Workshop — MoM</title>`
  - `<meta charset="utf-8">`
  - `<meta name="viewport" content="width=device-width, initial-scale=1">`
  - A single `<div id="wizard-root"></div>`
  - `<script src="genjson.js" defer></script>` — reference only, no JS yet (placeholder empty `genjson.js` acceptable)
  - No external CDN script or stylesheet references (CSP compliance from day one)

**And** `web/genjson/genjson.js` exists (empty file or single `// placeholder` comment — required so the HTML doesn't generate a 404 console error)

**And** `GET https://genjson.mapsofmaking.org/` returns HTTP 200 with `Content-Type: text/html`

**And** `GET http://genjson.mapsofmaking.org/` returns HTTP 301 redirecting to HTTPS

**And** the page loads in a browser with no console errors and no external network requests

**Gating test (manual):**
```bash
curl -I https://genjson.mapsofmaking.org/   # → 200 text/html
curl -I http://genjson.mapsofmaking.org/    # → 301
```
Plus operator visual confirmation: page loads in browser, no console errors.

---

## Implementation Plan

### 1. Certbot — issue `genjson.mapsofmaking.org` cert

**Before** touching nginx config, a DNS A-record and an HTTP-only nginx block must be in place to pass the ACME challenge.

**Step A — DNS:**
Add A-record `genjson.mapsofmaking.org` → `<VPS IP>` in your DNS registrar. Propagation can take minutes.

**Step B — Temporary HTTP-only nginx-gateway block:**
Create `infra/gateway-nginx/08-genjson-mapsofmaking.conf` with HTTP-only content first:

```nginx
server {
    listen      80;
    listen [::]:80;
    server_name genjson.mapsofmaking.org;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        access_log off;
    }

    location / { return 301 https://$host$request_uri; }
}
```

Deploy this partial config to the VPS:
```bash
scp infra/gateway-nginx/08-genjson-mapsofmaking.conf hetzner:/home/nicolas/hetzner-gateway/nginx/conf.d/
ssh hetzner "docker exec nginx-gateway nginx -t && docker exec nginx-gateway nginx -s reload"
```

**Step C — Issue cert:**
```bash
ssh hetzner "sudo certbot certonly --webroot -w /var/www/certbot -d genjson.mapsofmaking.org"
```
Cert will be stored at `/etc/letsencrypt/live/genjson.mapsofmaking.org/`.

### 2. Create `web/genjson/` scaffold (local repo)

```
web/genjson/
├── index.html   ← scaffold per AC
└── genjson.js   ← empty placeholder
```

The `web/` directory is volume-mounted at `/var/www/mapsofmaking` in `maps-nginx` (see `infra/docker-compose.yml`). So `web/genjson/index.html` is served at `/genjson/index.html` from maps-nginx.

### 3. Complete nginx-gateway config (after cert issued)

Update `infra/gateway-nginx/08-genjson-mapsofmaking.conf` to full config:

```nginx
# =============================================================================
# SERVICE: Maps of Making — Bernard's Workshop JSON composer
# DOMAIN: genjson.mapsofmaking.org
# PURPOSE: TLS termination + reverse proxy to maps-nginx /genjson/
# ADDED: 2026-05-30 (Story 9.1)
# SSL: Let's Encrypt — certbot certonly --webroot -w /var/www/certbot
#       -d genjson.mapsofmaking.org
# DNS: A record genjson.mapsofmaking.org → <VPS IP>
# BACKEND: maps-nginx /genjson/ path (web/genjson/ in repo)
# =============================================================================

server {
    listen      80;
    listen [::]:80;
    server_name genjson.mapsofmaking.org;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        access_log off;
    }

    location / { return 301 https://$host$request_uri; }
}

server {
    listen      443 ssl;
    listen [::]:443 ssl;
    server_name genjson.mapsofmaking.org;

    http2 on;

    resolver 127.0.0.11 valid=30s ipv6=off;

    ssl_certificate     /etc/letsencrypt/live/genjson.mapsofmaking.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/genjson.mapsofmaking.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Content-Security-Policy "default-src 'self' 'unsafe-inline'" always;

    access_log /var/log/nginx/genjson_mapsofmaking_access.log combined;
    error_log  /var/log/nginx/genjson_mapsofmaking_error.log;

    location / {
        proxy_pass http://maps-nginx/genjson/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html { root /usr/share/nginx/html; }
}
```

**Key pattern note:** `proxy_pass http://maps-nginx/genjson/` uses URI substitution (same as `07-admin-mapsofmaking.conf`'s `proxy_pass http://maps-nginx/admin/`). Do NOT use a variable (`set $upstream`) here — variables prevent URI rewriting. The `/genjson/` path must be a literal.

### 4. Deploy

```bash
# Copy updated gateway config
scp infra/gateway-nginx/08-genjson-mapsofmaking.conf hetzner:/home/nicolas/hetzner-gateway/nginx/conf.d/
ssh hetzner "docker exec nginx-gateway nginx -t && docker exec nginx-gateway nginx -s reload"

# Push web/genjson/ to VPS (the web/ volume is live-mounted, but ensure files are there)
# Either git pull on the VPS, or scp the files:
scp -r web/genjson hetzner:/home/nicolas/maps_of_making/web/
```

### 5. Verify

```bash
curl -sI https://genjson.mapsofmaking.org/ | head -5  # 200, Content-Type: text/html
curl -sI http://genjson.mapsofmaking.org/ | head -3    # 301 to https
```
Then open in browser — no console errors, no network requests to external domains.

---

## Architecture & Infra Context

### Two-layer nginx (MUST UNDERSTAND)

```
Internet → nginx-gateway (port 443, TLS) → maps-nginx (port 80, internal)
            /home/nicolas/hetzner-gateway/    infra/ in this repo
            nginx/conf.d/0X-*.conf            nginx/conf.d/app.conf
```

- **nginx-gateway** terminates TLS, handles certs, proxies to `maps-nginx` over Docker `gateway` network
- **maps-nginx** serves `web/` files from `/var/www/mapsofmaking` and proxies API calls
- The `web/` directory maps to `/var/www/mapsofmaking` in maps-nginx via docker volume

### How genjson path works end-to-end

```
GET https://genjson.mapsofmaking.org/
  → nginx-gateway: proxy_pass http://maps-nginx/genjson/
  → maps-nginx receives: GET /genjson/index.html (URI substituted)
  → maps-nginx: try_files /genjson/index.html → serves web/genjson/index.html
```

The `proxy_pass http://maps-nginx/genjson/` strip-and-prepend pattern means the trailing slash on both sides is critical — matches `07-admin-mapsofmaking.conf` exactly.

### Cert path conventions

| Domain | Cert path |
|---|---|
| `mapsofmaking.org`, `.com` | `live/mapsofmaking.org/` |
| `admin.mapsofmaking.org` | `live/admin.mapsofmaking.org/` |
| `genjson.mapsofmaking.org` | `live/genjson.mapsofmaking.org/` (NEW) |

No wildcard cert — individual certs per subdomain, issued via webroot certbot.

### CSP reasoning

The main map uses `frame-ancestors *` (embeddable) and no content CSP. genjson is different: it will be a wizard with form inputs, no iframes, and Bernard's voice copy — **no CDN dependencies by design**. The strict `default-src 'self' 'unsafe-inline'` CSP is a deliberate data-sovereignty signal and must not be relaxed unless a specific Story 9.x justifies it.

`'unsafe-inline'` is permitted for inline `<style>` blocks needed for the wizard UI before a full CSS bundler is introduced. Remove when Story 9.3 establishes the build toolchain.

### Distrobox/VPS access pattern

The hetzner-gateway lives on the VPS, not inside distrobox. Use `ssh hetzner` or `distrobox-host-exec` as appropriate:

```bash
# From within distrobox:
distrobox-host-exec ssh hetzner "docker exec nginx-gateway nginx -t"
# Or if SSH keys are set up on the host:
ssh hetzner "..."
```

---

## Files to Create / Modify

| File | Action | Notes |
|---|---|---|
| `infra/gateway-nginx/08-genjson-mapsofmaking.conf` | NEW | nginx-gateway config for genjson subdomain |
| `web/genjson/index.html` | NEW | Scaffold HTML per ACs |
| `web/genjson/genjson.js` | NEW | Empty placeholder (avoids 404 on `<script>` reference) |

**Files NOT to modify:**
- `infra/nginx/conf.d/app.conf` — maps-nginx serves `/genjson/` path automatically via root + try_files; no changes needed
- `infra/docker-compose.yml` — `web/` is already volume-mounted; `web/genjson/` is picked up automatically

---

## Isolation Notes

- **Distrobox:** `distrobox-host-exec` works for accessing Podman/Docker from within the container. For VPS SSH, use `ssh hetzner` (keys must be configured on host).
- **SELinux:** All volume mounts in `infra/docker-compose.yml` that aren't already `:z` should get `:z` if running on Fedora — but `web/genjson/` is added under the existing `../web:/var/www/mapsofmaking:ro` mount, so no new volume entries needed.
- **VPS deploy:** The hetzner-gateway repo lives at `/home/nicolas/hetzner-gateway/` on the VPS. Config files are deployed via `scp` + `docker exec nginx-gateway nginx -s reload` — there is no CI pipeline for the gateway.

---

## Dev Notes

- This is a pure infra story — no JavaScript logic. The `genjson.js` file is a placeholder. Stories 9.3+ will add actual wizard code.
- The scaffold HTML intentionally has no content — Bernard's copy lands in Story 9.5, wizard UI in Story 9.3. Don't add placeholder copy that future stories will need to remove.
- Cert issuance requires DNS propagation first. If certbot fails, check DNS with `dig genjson.mapsofmaking.org` before debugging certbot.
- If the VPS already has a wildcard cert `*.mapsofmaking.org`, use it instead of a separate cert — confirm with `ssh hetzner "sudo certbot certificates"` before issuing a new one. If yes: update ssl_certificate paths to the wildcard cert and skip certbot step.

---

## Story Completion Checklist

- [ ] DNS A-record `genjson.mapsofmaking.org` → VPS IP added and propagated
- [ ] `infra/gateway-nginx/08-genjson-mapsofmaking.conf` created (HTTP block first)
- [ ] Initial config deployed + nginx reloaded (HTTP-only, for ACME)
- [ ] Cert issued: `certbot certonly --webroot -d genjson.mapsofmaking.org`
- [ ] `08-genjson-mapsofmaking.conf` updated with HTTPS block
- [ ] `web/genjson/index.html` created (scaffold per ACs)
- [ ] `web/genjson/genjson.js` created (empty placeholder)
- [ ] Full config deployed to VPS, nginx reloaded
- [ ] `curl -I https://genjson.mapsofmaking.org/` → 200 ✓
- [ ] `curl -I http://genjson.mapsofmaking.org/` → 301 ✓
- [ ] Browser: page loads, no console errors, no external network requests ✓
- [ ] Sprint status updated to `done`
