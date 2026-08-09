// Node twin of the in-browser assertions on web/test/ — exercises the exact
// web/freshness.js the map ships. Run: node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
// freshness.js is a plain browser script that attaches to globalThis.
new Function(readFileSync(join(root, 'web', 'freshness.js'), 'utf8'))();
const F = globalThis.MOMFreshness;

const MIN = 60000, HOUR = 3600000, DAY = 86400000;
const iso = (msAgo) => new Date(Date.now() - msAgo).toISOString();
const T = F.FALLBACK_THRESHOLDS;

// ── Axis A — endpoint health ────────────────────────────────────────────────
test('A: null space and never-observed are broken', () => {
  assert.equal(F.computeAxisA(null, T), 'broken');
  assert.equal(F.computeAxisA({}, T), 'broken');
});
test('A: unreachable fetch is broken regardless of age', () => {
  assert.equal(F.computeAxisA({ observed_at: iso(1 * MIN), last_fetch_status: 'unreachable' }, T), 'broken');
});
test('A: bucket boundaries are >= (10/30/60 min)', () => {
  assert.equal(F.computeAxisA({ observed_at: iso(9 * MIN) }, T), 'fresh');
  assert.equal(F.computeAxisA({ observed_at: iso(11 * MIN) }, T), 'unresponsive');
  assert.equal(F.computeAxisA({ observed_at: iso(31 * MIN) }, T), 'warning');
  assert.equal(F.computeAxisA({ observed_at: iso(61 * MIN) }, T), 'broken');
});
test('A: unparseable timestamp is broken, not a crash', () => {
  assert.equal(F.computeAxisA({ observed_at: 'not-a-date' }, T), 'broken');
});

// ── Axis B — content lifecycle ──────────────────────────────────────────────
test('B: no updated_at renders dead, never silently confirmed', () => {
  assert.equal(F.computeAxisB({}, T), 'dead');
  assert.equal(F.computeAxisB(null, T), 'dead');
});
test('B: bucket boundaries (30/90/180 days)', () => {
  assert.equal(F.computeAxisB({ updated_at: iso(29 * DAY) }, T), 'confirmed');
  assert.equal(F.computeAxisB({ updated_at: iso(31 * DAY) }, T), 'aging');
  assert.equal(F.computeAxisB({ updated_at: iso(91 * DAY) }, T), 'zombie');
  assert.equal(F.computeAxisB({ updated_at: iso(181 * DAY) }, T), 'dead');
});
test('B: epoch-seconds updated_at is understood', () => {
  const secs = Math.floor((Date.now() - 45 * DAY) / 1000);
  assert.equal(F.computeAxisB({ updated_at: secs }, T), 'aging');
});
test('B: per-feature thresholds_override beats globals (canary demo mode)', () => {
  const s = {
    updated_at: iso(5 * MIN),
    thresholds_override: { operational_state: {
      aging_days_threshold: 1 / 1440, zombie_days_threshold: 2 / 1440, dead_days_threshold: 3 / 1440 } },
  };
  assert.equal(F.computeAxisB(s, T), 'dead'); // 5 min old > 3-minute dead override
});
test('B: missing thresholds falls back, does not crash', () => {
  assert.equal(F.computeAxisB({ updated_at: iso(1 * DAY) }, undefined), 'confirmed');
});

// ── Axis C — operational liveness ───────────────────────────────────────────
test('C: absent open_now is opt-out, not shut', () => {
  assert.equal(F.computeAxisC({}), 'opt-out');
  assert.equal(F.computeAxisC({ open_now: null }), 'opt-out');
});
test('C: true/false map to open/shut', () => {
  assert.equal(F.computeAxisC({ open_now: true }), 'open');
  assert.equal(F.computeAxisC({ open_now: false }), 'shut');
});

// ── Combined marker precedence ──────────────────────────────────────────────
const fresh = { observed_at: iso(2 * MIN), updated_at: iso(1 * DAY) };
test('marker: the eight canonical states', () => {
  assert.equal(F.computeMarker(null, T), 'seeded');
  assert.equal(F.computeMarker({}, T), 'seeded');
  assert.equal(F.computeMarker({ ...fresh }, T), 'confirmed');
  assert.equal(F.computeMarker({ ...fresh, open_now: true }, T), 'open');
  assert.equal(F.computeMarker({ ...fresh, open_now: false }, T), 'shut');
  assert.equal(F.computeMarker({ observed_at: iso(2 * MIN), updated_at: iso(45 * DAY) }, T), 'aging');
  assert.equal(F.computeMarker({ observed_at: iso(2 * MIN), updated_at: iso(120 * DAY) }, T), 'zombie');
  assert.equal(F.computeMarker({ observed_at: iso(2 * MIN), updated_at: iso(200 * DAY) }, T), 'dead');
});
test('marker: long silence (B) outranks a live open claim (C)', () => {
  assert.equal(F.computeMarker({ observed_at: iso(2 * MIN), updated_at: iso(120 * DAY), open_now: true }, T), 'zombie');
});
test('marker: broken endpoint (A) outranks the open claim (C)', () => {
  assert.equal(F.computeMarker({ observed_at: iso(2 * HOUR), updated_at: iso(1 * DAY), open_now: true }, T), 'broken');
});
test('marker: seeded space with an unparseable endpoint stays seeded, not broken', () => {
  assert.equal(F.computeMarker({ name: 'dir import only' }, T), 'seeded');
});

// ── Data-contract smoke: any materialized data present must satisfy the module ─
import { existsSync } from 'node:fs';
const SNAPSHOT = ['web/demo-data/spaces.snapshot.geojson', 'web/data/spaces.geojson']
  .map((p) => join(root, ...p.split('/'))).find(existsSync);
test('snapshot: materialized data computes a marker for every feature', { skip: !SNAPSHOT && 'no materialized geojson in this checkout' }, () => {
  const fc = JSON.parse(readFileSync(SNAPSHOT, 'utf8'));
  assert.ok(fc.thresholds && fc.thresholds.operational_state, 'thresholds header present');
  const legal = new Set(['seeded', 'confirmed', 'open', 'shut', 'aging', 'zombie', 'dead', 'broken']);
  for (const f of fc.features) {
    const m = F.computeMarker(f.properties, fc.thresholds);
    assert.ok(legal.has(m), `illegal marker ${m} for ${f.properties.id}`);
  }
  assert.ok(fc.features.length > 0, 'materialized data has features');
});
