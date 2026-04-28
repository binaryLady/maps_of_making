---
status: ready-for-dev
---

# Spec: nginx + DNS cutover for mapsofmaking.org / .com and admin subdomain

## User Intent

Switch DNS from temporary `mapofmaking.debarquin.eu` to canonical `mapsofmaking.org` + `mapsofmaking.com`.
Enable admin subdomain routing for `admin.mapsofmaking.org` and `admin.mapsofmaking.com` with basic auth.
Deploy a minimal landing page at `/admin` to verify end-to-end connectivity before building the full Epic 4 dashboard.

## Acceptance Criteria

- [ ] HTTP blocks for `mapsofmaking.org` + `.com` + `admin.*` serve certbot ACME challenges
- [ ] HTTPS blocks activate: `mapsofmaking.org` proxies to maps-nginx, `.com` redirects to `.org`
- [ ] Admin HTTPS block proxies `admin.*` subdomains to internal nginx `/admin` location
- [ ] Admin landing page (`web/admin/index.html`) displays "Mission Control" with placeholder text
- [ ] Basic auth gate (`/etc/nginx/.htpasswd`) blocks unauthenticated access to `/admin`
- [ ] Certificates issued via certbot for all three domains (runbook documented)
- [ ] Temporary `mapofmaking.debarquin.eu` remains active to avoid broken bookmarks during TTL expiry
- [ ] Legacy `admin.debarquin.eu` HTTPS block left as commented template for future cert issuance

## Implementation Tasks

### Task 1: Create admin landing page

**File:** `web/admin/index.html`

Vanilla HTML (no framework). Served by internal nginx at `/admin/` via `try_files` rule.
Includes: heading "Maps of Making — Mission Control", status badge "Coming in Epic 4",
placeholder text about ingestion monitoring, link back to `https://mapsofmaking.org`.

### Task 2: Update main domain gateway config

**File:** `infra/gateway-nginx/06-mapsofmaking.conf`

**Add HTTP blocks (port 80):**
- `mapsofmaking.org` + `mapsofmaking.com`
- Serve `/.well-known/acme-challenge/` from `/var/www/certbot`
- Redirect other requests to `https://$host$request_uri`

**Uncomment and activate HTTPS blocks:**

1. **mapsofmaking.com redirect-only server:**
   - Listen 443 SSL (IPv4 + IPv6)
   - TLS config: protocols TLSv1.2/1.3, HIGH ciphers, session cache, prefer_server_ciphers
   - Certificate: `/etc/letsencrypt/live/mapsofmaking.com/`
   - Action: `return 301 https://mapsofmaking.org$request_uri`
   - Security headers: HSTS only (no frame/CSP needed for redirect)

2. **mapsofmaking.org primary server:**
   - Listen 443 SSL (IPv4 + IPv6)
   - TLS config: same as above
   - Certificate: `/etc/letsencrypt/live/mapsofmaking.org/`
   - Proxy block: `set $upstream http://maps-nginx:80; proxy_pass $upstream`
   - Security headers: X-Content-Type-Options, Referrer-Policy, HSTS, X-Frame-Options: ALLOWALL, CSP: frame-ancestors *
   - Proxy headers: Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
   - Logging: mapsofmaking_https_access.log, mapsofmaking_error.log
   - Error page: 50x.html

**Keep old blocks:**
- `mapofmaking.debarquin.eu` HTTP + HTTPS remain active (do not remove)

### Task 3: Update admin subdomain gateway config

**File:** `infra/gateway-nginx/07-admin-mapsofmaking.conf`

**Expand HTTP block:**
- Add `admin.debarquin.eu admin.mapsofmaking.org admin.mapsofmaking.com` to `server_name`
- Serve `/.well-known/acme-challenge/` from `/var/www/certbot`
- Redirect to `https://$host$request_uri`

**Uncomment and activate HTTPS block (production domains):**
- `server_name admin.mapsofmaking.org admin.mapsofmaking.com`
- Listen 443 SSL (IPv4 + IPv6)
- TLS config: same as main domain
- Certificate: `/etc/letsencrypt/live/admin.mapsofmaking.org/` (SAN covers .com)
- Proxy: `set $upstream http://maps-nginx:80; proxy_pass $upstream` (let internal nginx route `/admin`)
- Security headers: X-Content-Type-Options, Referrer-Policy, HSTS, X-Frame-Options: DENY (stricter than main)
- Proxy headers: Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
- Logging: admin_mapsofmaking_access.log, admin_mapsofmaking_error.log
- Error page: 50x.html

**Leave legacy domain as commented template:**
- `admin.debarquin.eu` HTTPS block remains commented, marked for later cert issuance

### Task 4: Issue TLS certificates (manual VPS runbook)

On the VPS, after pushing and deploying the nginx config changes:

```bash
# Step A — verify nginx config (should pass)
sudo nginx -t

# Step B — reload nginx to activate HTTP blocks (needed for certbot challenge)
sudo systemctl reload nginx

# Step C — issue cert for main production domains (single cert, SAN covers both)
sudo certbot certonly --webroot -w /var/www/certbot \
  -d mapsofmaking.org -d mapsofmaking.com

# Step D — issue cert for admin production domains (single cert, SAN covers both)
sudo certbot certonly --webroot -w /var/www/certbot \
  -d admin.mapsofmaking.org -d admin.mapsofmaking.com

# Step E — test updated config again
sudo nginx -t

# Step F — reload nginx to activate HTTPS blocks
sudo systemctl reload nginx

# Step G — verify end-to-end
curl -I https://mapsofmaking.org
curl -I https://mapsofmaking.com
curl -u admin:PASSWORD https://admin.mapsofmaking.org/
```

## Verification (local)

1. Inspect `web/admin/index.html` — contains "Mission Control", "Coming in Epic 4", link to main map
2. Inspect `infra/gateway-nginx/06-mapsofmaking.conf` — HTTP blocks for .org/.com, HTTPS blocks uncommented
3. Inspect `infra/gateway-nginx/07-admin-mapsofmaking.conf` — HTTP covers all admin subdomains, HTTPS blocks all production domains
4. Nginx syntax check via `nginx -t` (on VPS after pull)

## Verification (post-deployment)

After certbot certificates issued and nginx reloaded:

| Test | Expected | Command |
|---|---|---|
| HTTP redirect | 301 to HTTPS | `curl -I http://mapsofmaking.org` |
| Main domain HTTPS | 200, HSTS header | `curl -I https://mapsofmaking.org` |
| .com redirect | 301 to mapsofmaking.org | `curl -I https://mapsofmaking.com` |
| Admin unauthenticated | 401 (basic auth) | `curl -I https://admin.mapsofmaking.org/` |
| Admin authenticated | 200, HTML contains "Mission Control" | `curl -u admin:PASSWORD https://admin.mapsofmaking.org/` |
| Admin .com subdomain | Redirects to .org admin (if configured) | `curl -I https://admin.mapsofmaking.com/` |

## Deployment Order

1. Commit and push this branch
2. SSH to VPS, pull changes
3. Run Step A (nginx -t) to verify syntax
4. Run Step B (reload nginx)
5. Run Step C & D (certbot for both domains)
6. Run Step E & F (nginx test + reload)
7. Run Step G tests

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| DNS not fully propagated when certs issued | Check with `dig mapsofmaking.org` before certbot; if missing A record, certbot fails gracefully |
| Old debarquin.eu bookmarks break during TTL expiry | Keep debarquin.eu blocks active; users hitting old domain still work until TTL expires (typically 24-48h) |
| Admin `.com` domain not included in cert SAN | Use single cert for both `.org` and `.com` via `-d` flags in certbot call |
| Cert renewal fails if HTTP challenge path moves | HTTP blocks serve `/.well-known/` from same path as before; certbot renewal should work automatically |

## Files Modified

| File | Change |
|---|---|
| `web/admin/index.html` | New — vanilla HTML landing page |
| `infra/gateway-nginx/06-mapsofmaking.conf` | Add HTTP blocks, uncomment + complete HTTPS blocks for .org/.com |
| `infra/gateway-nginx/07-admin-mapsofmaking.conf` | Expand HTTP server_name, uncomment + complete HTTPS block for admin.*.org/.com |

## Related Work

- **Deferred:** Epic 4 Story 4.0 — full mission-control dashboard with ingestion monitoring
  (spec: `4-0-admin-foundation-subdomain-auth-space-comparison.md`)
