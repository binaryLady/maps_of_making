---
status: completed
---

# Investigation: Heartbeat Staleness & Data Freshness Bug — RESOLVED

## Problem Statement

After completing 3.2, the heartbeat system showed contradictory UI signals:

- **OpenFab case**: UI displayed "update 55min ago" but "fetched: 16h ago"
- **Symptom**: Manual JSON edits made 1h ago were not appearing in the RAW JSON card display
- **Impact**: Map visitors could not trust freshness signals; coordinators could not confirm endpoint health

## Root Cause Identified

**Stale HTTP Cache Headers (ETag/Last-Modified) in heartbeat_log.db**

Timeline:
1. Endpoint URL changed from `.jsonld` to `.json` 24h ago (repo rename)
2. Heartbeat fetched old `.jsonld` version and stored its ETag and Last-Modified headers in SQLite
3. URL re-registration via "add url" endpoint updated Oxigraph registration
4. User updated JSON content 1h ago (GitHub commit + deploy)
5. Next heartbeat cycle fetched with old conditional headers (`If-None-Match`, `If-Modified-Since`)
6. Server responded with **304 Not Modified** (cache still matched old .jsonld version)
7. Heartbeat skipped content update → `mom:lastUpdated` never changed
8. UI showed stale "update 55min" while "fetched recently" kept refreshing on 304

**Evidence from logs:**
```
GET https://openfab.be/openfab.json "HTTP/1.1 304 Not Modified"
304 Not Modified for openfab — bandwidth saved
heartbeat 304 state-only write for openfab (healthy/confirmed)
```

## Solution Applied

### Step 1: Clear Stale Cache from heartbeat_log.db

```python
import sqlite3
con = sqlite3.connect('/app/tasks/heartbeat_log.db')
con.execute('UPDATE heartbeat_log SET etag = NULL, last_modified = NULL WHERE space_id = ?', ('openfab',))
con.commit()
con.close()
```

This forces the next fetch to proceed without conditional headers, guaranteeing a 200 response.

### Step 2: Fix SELinux Permission on activity_map.yaml

**Issue**: On Fedora with SELinux, the activity_map.yaml mount was blocked with permission denied.

**Fix A** (Applied): Apply SELinux context label to file on host:
```bash
chcon -t container_file_t /var/home/nicolas/github/maps_of_making/scripts/activity_map.yaml
```

**Fix B** (For future): Added `:z` flag to docker-compose.dev.yml volume mount:
```yaml
mak-link-handler:
  volumes:
    - ../scripts/activity_map.yaml:/app/scripts/activity_map.yaml:ro,z
```

### Step 3: Restart Container

Removed and recreated the link-handler container to pick up:
- Fresh heartbeat_log.db with cleared cache
- New volume mount with SELinux relabeling

### Step 4: Verify Fix

Manual heartbeat refresh after restart:
```
GET https://openfab.be/openfab.json "HTTP/1.1 200 OK"
heartbeat refreshed openfab (healthy/confirmed)
```

✓ **Outcome: Content successfully updated, `mom:lastUpdated` reset to current time**

## Lessons for Future Endpoint Changes

1. **Endpoint format changes** (e.g., .jsonld → .json): The heartbeat caches HTTP headers. When changing endpoint format/URL:
   - Option A: Clear the heartbeat_log.db entry for the space before restart
   - Option B: Deploy a new minor version that auto-resets stale cache on format detection mismatch
   - Option C: Implement a `/api/cache-clear/{space_id}` admin endpoint (for Epic 4 operator dashboard)

2. **SELinux on Fedora**: All container volume mounts need `:z` flag for Fedora/distrobox environments. Updated docker-compose.dev.yml serves as the template.

3. **Trust model**: Card displays now correctly reflect:
   - "update X min ago" = `mom:lastUpdated` (content freshness clock)
   - "fetched X min ago" = `last_fetched` timestamp (endpoint reachability, updates on 304 too)
   - Discrepancy between them indicates either 304-cached content or pending next cycle

## Status

✓ RESOLVED — OpenFab now fetches fresh content, `mom:lastUpdated` reflects current state, UI signals are consistent.

All other 8 registered spaces have been running normally throughout this issue (using their original endpoints that didn't change format).
