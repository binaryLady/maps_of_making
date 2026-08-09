// Maps of Making — freshness axes, shared module (Story 3.10 logic, extracted).
// Pure functions only: f(space, now-implicit, thresholds) → token. No DOM, no map,
// no fetch. Loaded by app.js (before it, via script tag), by the test bench
// (web/test/), and by the Node test suite (tests/web/freshness.test.mjs) — one
// implementation, three consumers, so the bench and the tests exercise exactly
// what the map renders.
(function (root) {
  'use strict';

  // Numbers mirror infra/link_handler/config.yaml so a missing header degrades
  // visibly but does not silently render everything `confirmed`.
  const FALLBACK_THRESHOLDS = {
    endpoint_health: {
      unresponsive_minutes_threshold: 10,
      warning_minutes_threshold: 30,
      broken_minutes_threshold: 60,
    },
    operational_state: {
      aging_days_threshold: 30,
      zombie_days_threshold: 90,
      dead_days_threshold: 180,
    },
  };

  function ageMinutes(iso) {
    if (!iso) return null;
    const t = new Date(iso.endsWith('Z') ? iso : iso + 'Z').getTime();
    if (isNaN(t)) return null;
    return (Date.now() - t) / 60000;
  }
  function ageDays(iso) {
    const m = ageMinutes(iso);
    return m == null ? null : m / 1440;
  }

  // Axis A — endpoint health. Returns 'broken'|'warning'|'unresponsive'|'fresh'.
  function computeAxisA(s, thresholds) {
    if (!s) return 'broken';
    if (s.last_fetch_status === 'unreachable') return 'broken';
    if (!s.observed_at) return 'broken'; // never-observed → cannot claim healthy
    const t = (thresholds && thresholds.endpoint_health) || FALLBACK_THRESHOLDS.endpoint_health;
    const age = ageMinutes(s.observed_at);
    if (age == null) return 'broken';
    if (age >= t.broken_minutes_threshold) return 'broken';
    if (age >= t.warning_minutes_threshold) return 'warning';
    if (age >= t.unresponsive_minutes_threshold) return 'unresponsive';
    return 'fresh';
  }

  // updated_at as epoch ms, or null. Single anchor for Axis B and the status-bar
  // "updated X ago" line. last_open_change intentionally excluded (self-reported,
  // unreliable).
  function lastActivity(s) {
    if (!s || s.updated_at == null) return null;
    const v = s.updated_at;
    const n = Number(v);
    if (!isNaN(n) && n > 1e8) return n * 1000;
    const iso = String(v);
    const t = new Date(iso.endsWith('Z') ? iso : iso + 'Z').getTime();
    return isNaN(t) ? null : t;
  }

  // Axis B — content lifecycle. Returns 'dead'|'zombie'|'aging'|'confirmed'.
  // Null lastActivity → oldest supported state; never crash, never silently
  // render `confirmed`. Per-feature thresholds_override beats globals (canary
  // demo mode compresses aging/zombie/dead to seconds-scale).
  function computeAxisB(s, thresholds) {
    const override = s && s.thresholds_override && s.thresholds_override.operational_state;
    const t = override || (thresholds && thresholds.operational_state) || FALLBACK_THRESHOLDS.operational_state;
    if (!s) return 'dead';
    const lastMs = lastActivity(s);
    if (lastMs == null) return 'dead';
    const age = (Date.now() - lastMs) / 86400000;
    if (age >= t.dead_days_threshold) return 'dead';
    if (age >= t.zombie_days_threshold) return 'zombie';
    if (age >= t.aging_days_threshold) return 'aging';
    return 'confirmed';
  }

  // Axis C — operational liveness. Current source claim, does not age.
  function computeAxisC(s) {
    if (!s || s.open_now === undefined || s.open_now === null) return 'opt-out';
    return s.open_now === true ? 'open' : 'shut';
  }

  // Combined marker — precedence: dead/zombie/aging (B) → broken (A) →
  // open/shut (C) → confirmed → seeded. Long-term silence is louder than a
  // transient endpoint blip; a broken endpoint is louder than the open claim.
  function computeMarker(s, thresholds) {
    if (!s) return 'seeded';
    const b = computeAxisB(s, thresholds);
    if (lastActivity(s) != null && (b === 'dead' || b === 'zombie' || b === 'aging')) return b;
    const a = computeAxisA(s, thresholds);
    if (a === 'broken' && s.observed_at) return 'broken';
    const c = computeAxisC(s);
    if (c === 'open') return 'open';
    if (c === 'shut') return 'shut';
    if (lastActivity(s) != null || s.observed_at) return 'confirmed';
    return 'seeded';
  }

  root.MOMFreshness = {
    FALLBACK_THRESHOLDS,
    ageMinutes,
    ageDays,
    lastActivity,
    computeAxisA,
    computeAxisB,
    computeAxisC,
    computeMarker,
  };
})(typeof globalThis !== 'undefined' ? globalThis : this);
