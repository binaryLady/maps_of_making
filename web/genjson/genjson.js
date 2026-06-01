/**
 * genjson.js — Bernard's Workshop wizard (Story 9.3 / 9.5)
 * Renders into #wizard-root. Vanilla JS, no framework, no build step.
 * CSP: default-src 'self' 'unsafe-inline' — fonts self-hosted, no CDN.
 */

'use strict';

const DRAFT_KEY = 'genjson_draft';  // must match Story 9.2 drawer contract

// ── Copy artifact ─────────────────────────────────────────────────────────────

let COPY = null;

const COPY_FALLBACK = {
  drawer_one_liner: "Two ways onto the map. Tell me about your space, or paste your endpoint URL if you've got one. Either's fine.",
  wizard_intro: "Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map.",
  floor_gate: "Let's define your bedrock. What does your community call this place?",
  beat_name_ack: "Okay, and where do I find it?",
  bedrock_confirm: "That's your bedrock. The rest is yours to give, or not.",
  keyboard_nav_hint: "Tab or Enter to move on.",
  tier_1_exit: "Core's in. Other SpaceAPI apps can read this file as-is.",
  tier_2_exit: "MoM fields in. Now the world can see your membership, your hours, the goals you work toward.",
  tier_3_exit: "Silo fields in. The bits only your kind of space needs are switched on.",
  sovereignty_disclosure: "You publish, we make it legible. The rest is history.",
  localstorage_warning: "Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser.",
  localstorage_resume: "Continuing from where you left off.",
  field_hints: {
    space: "The name your community knows you by.",
    address: "Street address — the part before city.",
    city: "City or municipality.",
    postcode: "Postal code.",
    country_code: "Two-letter ISO country code. e.g. DE, FR, BE.",
    logo: "We scale by height and keep your ratio — transparent PNG works best.",
    url: "Your space's main web page.",
    description: "One or two sentences. What kind of space is this?",
    contact_email: "Not a personal inbox — somewhere the space can be reached.",
    contact_matrix: "Your space's room, not a personal account.",
    opening_hours: "When are you open? We use OSM opening_hours format.",
    memberOf: "Which network(s) is this space part of? URL preferred.",
    sdgs: "Which UN Sustainable Development Goals does your space contribute to? Numbers only.",
  },
  validation_messages: {
    schema_invalid: "Something's off. Check the fields marked in red — the file isn't valid yet.",
    geocoding_in_progress: "Working out where that is.",
    geocode_resolved: "Dropping the pin here:",
    nominatim_unavailable: "Geocoding temporarily unavailable — enter coordinates manually.",
    nominatim_no_result: "No result — enter coordinates manually.",
    nominatim_rate_limit: "Too many requests — wait a moment and try again.",
    clear_confirm: "This will erase your saved progress. Continue?",
    url_scheme_added: "Added https:// — update if wrong.",
    matrix_sigil_added: "Added # for a room — change to + if it's a community.",
  },
  export_button: "Export JSON",
  fork_stub: {
    tier2_teaser: "Tier 2 is on the way. Network features land in a later step.",
    tutorial_teaser: "Self-hosting walkthrough is on the way. Export your file and keep it warm for now.",
  },
};

async function fetchCopy() {
  try {
    const resp = await fetch('/bernard_copy.json');
    if (!resp.ok) throw new Error('copy fetch failed');
    COPY = await resp.json();
  } catch {
    COPY = COPY_FALLBACK;
  }
}

// ── Styles ────────────────────────────────────────────────────────────────────

const CSS = `
  @font-face {
    font-family: 'Special Elite';
    src: url('fonts/SpecialElite-Regular.woff2') format('woff2');
    font-display: swap;
  }

  :root {
    /* ── Dusk base (Direction B — liminal workshop threshold) ── */
    --bg:         oklch(11% 0.03 210);   /* deep blue-green night */
    --surface:    oklch(17% 0.025 210);  /* card/input surface */
    --border:     oklch(33% 0.025 210);  /* border / divider */
    --text:       #f0ede8;               /* warm near-white, high contrast */
    --muted:      oklch(74% 0.02 210);   /* secondary text (lifted for WCAG AA 3:1 on dark) */
    --placeholder:oklch(71% 0.02 210);   /* input placeholder (WCAG AA 3:1 on surface) */

    /* ── Bernard's spectrum (lifted for dark base; see bernard-bible §1) ── */
    --amber:  oklch(80% 0.14 78);   /* lamplight gold — voice + primary CTA */
    --blue:   oklch(76% 0.17 250);  /* cobalt — links / navigation (lifted for WCAG AA on dark) */
    --green:  oklch(70% 0.15 148);  /* sea-grass — valid / confirmed */
    --error:  oklch(65% 0.19 25);   /* riso red — errors ONLY */
    --uv:     oklch(73% 0.11 288);  /* UV shimmer — sparing (focus/hover glow) */

    /* ── Semantic aliases (keep existing code references working) ── */
    --accent: var(--amber);
    --warn:   var(--error);
    /* UV glow (Approach C, locked) — filter:drop-shadow stack glows the shape
       with a real gaussian falloff. Apply via 'filter: var(--uv-glow)'. */
    --uv-glow: drop-shadow(0 0 3px oklch(73% 0.11 288 / 0.6)) drop-shadow(0 0 14px oklch(73% 0.11 288 / 0.4));

    --font-mono: 'Courier New', 'Lucida Console', monospace;
    --mono: var(--font-mono);

    /* ── UI border — passes WCAG 1.4.11 Non-text Contrast (3:1 on dark bg) ── */
    --input-border: oklch(74% 0.025 210);

    /* ── Spacing scale (AC4) — one source of truth for rhythm ── */
    --space-1: 0.6rem;
    --space-2: 1rem;
    --space-3: 1.5rem;
    --space-4: 2rem;
  }

  #wizard-root * { box-sizing: border-box; }

  #wizard-root {
    font-family: var(--mono);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 2rem 1rem;
  }

  .wiz-container {
    max-width: 680px;
    margin: 0 auto;
  }

  .bernard-voice {
    font-family: 'Special Elite', var(--font-mono), monospace;
    font-size: 17px;
    line-height: 1.55;
    color: var(--accent);
    margin: 1rem 0;
  }

  /* Tier progression (AC3) — three states read via colour + size + border,
     never font-weight (Special Elite is single-weight). Harmonized with the
     drawer's muted-tombstone pattern (dashed + muted for inactive).
       locked  → dashed, dimmed tombstone (ahead, not yet reachable)
       active  → brighter border + label (the current frontier, "you are here")
       settled → default solid border, muted label (done; focus has moved on) */
  .tier-block {
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: var(--space-3);
    margin: var(--space-3) 0;
    transition: border-color 0.25s ease;
  }

  /* Active frontier: lift the border so the current step stands out. */
  .tier-block.tier-active {
    border-color: var(--muted);
  }

  .tier-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 1rem;
  }

  /* Active tier's label is brighter + a touch larger — hierarchy by size+colour. */
  .tier-block.tier-active .tier-label {
    color: var(--text);
    font-size: 0.82rem;
  }

  .field-row {
    margin-bottom: var(--space-2);
  }

  .field-row label {
    display: block;
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
    color: var(--text);
  }

  .field-row .hint {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.3rem;
    max-height: 2.4em;
    overflow: hidden;
  }
  /* Keyboard affordance: sits BELOW its input, quiet — teaches commit-to-advance. */
  .field-row .kbd-hint {
    margin-bottom: 0;
    margin-top: 0.35rem;
    font-size: 0.72rem;
    color: var(--placeholder);
  }

  .field-row input,
  .field-row textarea {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--input-border);
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.9rem;
    padding: 0.5rem 0.7rem;
    border-radius: 3px;
    outline: none;
  }

  .field-row input::placeholder,
  .field-row textarea::placeholder {
    color: var(--placeholder);
  }

  /* Focus = navigation affordance → blue outline, matching the drawer's
     .inline-link:focus-visible pattern (web/maps-of-making.html). NOT UV
     (UV is reserved for Bernard's labor — bible §1). */
  .field-row input:focus-visible,
  .field-row textarea:focus-visible {
    border-color: var(--blue);
    outline: 2px solid var(--blue);
    outline-offset: 2px;
  }

  /* Inline text link — mirrors drawer .inline-link (blue, underlined). */
  .inline-link {
    font: inherit;
    color: var(--blue);
    background: none;
    border: 0;
    padding: 0;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  .inline-link:hover { color: var(--text); }
  .inline-link:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; border-radius: 2px; }

  /* coords-preview: muted while geocoding, green when confirmed (valid),
     red on failure. Green = a valid state; the UV flash (Bernard's labor)
     fires separately on resolve via .uv-flash. */
  .coords-preview {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.4rem;
    min-height: 1.2em;
  }

  .coords-preview.ok { color: var(--green); }
  .coords-preview.error { color: var(--error); }

  .btn {
    font-family: var(--mono);
    font-size: 0.9rem;
    padding: 0.6rem 1.4rem;
    border-radius: 3px;
    cursor: pointer;
    border: 1px solid var(--input-border);
    background: var(--surface);
    color: var(--text);
    transition: border-color 0.15s, background 0.15s;
  }

  /* Subordinate button: hover lifts the border only (NOT amber — amber is
     reserved for the primary CTA so it stays meaningful). */
  .btn:hover:not(:disabled) { border-color: var(--muted); }
  .btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .btn:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }

  /* Primary CTA = amber (Bernard's voice colour). */
  .btn-primary { border-color: var(--amber); color: var(--amber); }
  .btn-primary:hover:not(:disabled) {
    border-color: var(--amber);
    background: oklch(80% 0.14 78 / 0.12);
  }

  .btn-row {
    display: flex;
    gap: var(--space-2);
    flex-wrap: wrap;
    margin-top: var(--space-2);
    align-items: center;
  }

  .skip-note {
    font-size: 0.8rem;
    color: var(--muted);
    font-style: italic;
  }

  .warn-banner {
    background: oklch(20% 0.04 25);
    border: 1px solid var(--error);
    border-radius: 3px;
    padding: 0.8rem var(--space-2);
    font-size: 0.82rem;
    color: var(--error);
    margin: var(--space-2) 0;
  }
  .warn-banner-actions { margin-top: var(--space-1); }

  /* Country-code input — short fixed-width, uppercase normalizer visible. */
  .input-country { text-transform: uppercase; width: 6rem; }

  .clear-link {
    background: none;
    border: none;
    color: var(--muted);
    text-decoration: underline;
    cursor: pointer;
    font-family: var(--mono);
    font-size: 0.8rem;
    padding: 0;
  }
  .clear-link:hover { color: var(--warn); }

  /* Locked tier = muted tombstone: dashed border + dimmed, but still legible
     (perceivable per AC7). Reads as "present but not yet reachable". */
  .tier-locked {
    opacity: 0.5;
    border-style: dashed;
    pointer-events: none;
  }

  /* Beat-by-beat reveal (AC10, P2 — kill the wall). Each beat is a CSS grid that
     animates its single row 0fr→1fr; the inner wrapper clips the overflow so the
     content slides open. Cheap, no library (drawer .url-fork model). */
  .beat {
    display: grid;
    grid-template-rows: 0fr;
    opacity: 0;
    transition: grid-template-rows 0.45s cubic-bezier(.2,.8,.2,1), opacity 0.45s ease;
  }
  .beat > .beat-inner { overflow: hidden; min-height: 0; }
  .beat.revealed { grid-template-rows: 1fr; opacity: 1; }
  /* Pre-filled beats on resume snap open without replaying the reveal. */
  .beat.instant { transition: none; }
  @media (prefers-reduced-motion: reduce) {
    .beat { transition: none; }
  }

  /* Transient intro (AC5) — launches visible, then recedes to give way to Tier 0.
     Same grid-rows trick as .beat but in reverse: starts 1fr, collapses to 0fr. */
  .bernard-intro {
    display: grid;
    grid-template-rows: 1fr;
    opacity: 1;
    overflow: hidden;
    transition: grid-template-rows 0.55s cubic-bezier(.2,.8,.2,1), opacity 0.55s ease;
  }
  .bernard-intro.receding {
    grid-template-rows: 0fr;
    opacity: 0;
  }
  .bernard-intro > .intro-inner { overflow: hidden; min-height: 0; }
  @media (prefers-reduced-motion: reduce) {
    .bernard-intro { transition: none; }
  }

  /* Validation gaps → red (AC2: "validation gaps" is an errors/danger signal). */
  .validation-warn {
    background: oklch(20% 0.04 25);
    border: 1px solid var(--error);
    border-radius: 3px;
    padding: 0.6rem 1rem;
    font-size: 0.8rem;
    color: var(--error);
    margin-top: 0.8rem;
  }

  .fork {
    margin-top: var(--space-4);
    padding-top: var(--space-3);
    border-top: 1px solid var(--border);
  }

  .fork-label {
    margin-bottom: 1rem;
  }

  .fork-doors {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .fork-door {
    flex: 1;
    min-width: 220px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.3rem;
    padding: 1rem 1.2rem;
    text-align: left;
  }

  .fork-door-title { font-size: 0.95rem; color: var(--text); }
  /* Fork doors are navigation → blue on hover. */
  .fork-door:hover .fork-door-title { color: var(--blue); }
  .fork-door-sub { font-size: 0.75rem; color: var(--muted); }

  .fork-note {
    margin-top: 1rem;
    font-size: 0.8rem;
    color: var(--muted);
    font-style: italic;
  }

  /* UV = Bernard's labor (bible §1). One-shot glow for the *instant* scrub act
     (normalizer on blur) — never plain focus. Fades out via the drop-shadow
     alpha animating to 0. (The geocode beat uses the sustained .uv-working glow
     below, since it has a duration.) */
  @keyframes uv-pulse {
    0%, 35% {
      filter: drop-shadow(0 0 4px oklch(73% 0.13 288 / 0.95))
              drop-shadow(0 0 18px oklch(73% 0.13 288 / 0.7));
    }
    100% {
      filter: drop-shadow(0 0 4px oklch(73% 0.13 288 / 0))
              drop-shadow(0 0 18px oklch(73% 0.13 288 / 0));
    }
  }
  .uv-flash { animation: uv-pulse 1.4s ease-out; }

  /* Reduced motion: no animation, but still cue Bernard's act with a static
     glow (JS clears it after a beat) — the information survives, the movement doesn't. */
  @media (prefers-reduced-motion: reduce) {
    .uv-flash {
      animation: none;
      filter: drop-shadow(0 0 4px oklch(73% 0.13 288 / 0.95))
              drop-shadow(0 0 18px oklch(73% 0.13 288 / 0.7));
    }
  }

  /* UV "working" — a sustained, breathing glow on the geocode meter while
     Bernard derives the coordinates. The glow lives on the *labor* (the
     processing beat), NOT on the green result. Cleared when the meter stops. */
  @keyframes uv-working {
    0%, 100% {
      filter: drop-shadow(0 0 3px oklch(73% 0.13 288 / 0.5))
              drop-shadow(0 0 12px oklch(73% 0.13 288 / 0.3));
    }
    50% {
      filter: drop-shadow(0 0 5px oklch(73% 0.13 288 / 0.95))
              drop-shadow(0 0 20px oklch(73% 0.13 288 / 0.6));
    }
  }
  .uv-working { animation: uv-working 1.1s ease-in-out infinite; }

  @media (prefers-reduced-motion: reduce) {
    .uv-working {
      animation: none;
      filter: drop-shadow(0 0 4px oklch(73% 0.13 288 / 0.85))
              drop-shadow(0 0 16px oklch(73% 0.13 288 / 0.5));
    }
  }

  /* Mobile (AC8) — ≤480px reflow. Single-column by design; adjustments:
     - root side-padding tightened so 680px container doesn't clip
     - btn min-height + padding raised to ~44px tap target
     - fork-door min-width floored so two doors stack cleanly on narrow screens */
  @media (max-width: 480px) {
    #wizard-root { padding: 1.5rem 0.75rem; }
    .btn { padding: 0.75rem 1.2rem; min-height: 44px; }
    .strip-export-btn { padding: 0.75rem var(--space-2); min-height: 44px; }
    .fork-door { min-width: 160px; }
    .strip-filename { font-size: 0.72rem; }
  }

  /* Ownership strip (AC6, §4 P1) — static footer; always present, always subordinate.
     Progress: thin 2px bar, one threshold (bedrock), never a %, never red. */
  .ownership-strip {
    margin-top: var(--space-4);
    padding-top: var(--space-2);
    border-top: 1px solid var(--border);
  }
  .strip-progress {
    height: 2px;
    background: oklch(25% 0.02 210);
    border-radius: 1px;
    margin-bottom: var(--space-2);
    overflow: hidden;
  }
  .strip-progress-fill {
    height: 100%;
    width: 5%;
    background: var(--border);
    border-radius: 1px;
    transition: width 0.5s ease, background 0.5s ease;
  }
  .strip-row {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex-wrap: wrap;
  }
  .strip-filename {
    flex: 1;
    font-size: 0.78rem;
    color: var(--muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-family: var(--mono);
  }
  .strip-export-btn {
    font-size: 0.8rem;
    padding: 0.4rem var(--space-2);
  }
  .strip-warn {
    margin-top: var(--space-1);
    font-size: 0.78rem;
    color: var(--muted);
  }
`;

// ── State ─────────────────────────────────────────────────────────────────────

let draft = {
  space: '',
  address: '',
  city: '',
  postcode: '',
  country_code: '',
  lat: null,
  lon: null,
  logo: '',
  url: '',
  description: '',
  contact_email: '',
  contact_matrix: '',
};

let tier0Passed = false;
let geocodeDebounceTimer = null;
let lastGeocodeKey = '';  // address|city last sent — dedupes repeat commits (blur + Tab)
let schemaCache = null;

// ── Persistence ───────────────────────────────────────────────────────────────

function saveDraft() {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return false;
    const saved = JSON.parse(raw);
    draft = { ...draft, ...saved };
    return true;
  } catch (_) {
    return false;
  }
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY);
  draft = {
    space: '', address: '', city: '', postcode: '', country_code: '',
    lat: null, lon: null,
    logo: '', url: '', description: '',
    contact_email: '', contact_matrix: '',
  };
  tier0Passed = false;
}

// ── Geocode ───────────────────────────────────────────────────────────────────

async function geocode(address, city, postcode, country_code) {
  const resp = await fetch('/api/geocode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address, city, postcode, country_code }),
  });
  if (resp.status === 503) return { error: 'unavailable' };
  if (!resp.ok) return { error: 'unavailable' };
  return resp.json();
}

// ── SpaceAPI v15 schema (bundled) ─────────────────────────────────────────────

async function loadSchema() {
  if (schemaCache) return schemaCache;
  try {
    const resp = await fetch('/genjson/spaceapi-v15.schema.json');
    schemaCache = await resp.json();
    return schemaCache;
  } catch (_) {
    return null;
  }
}

function validateAgainstSchema(doc, schema) {
  if (!schema) return [];
  const errors = [];
  const required = schema.required || [];
  for (const field of required) {
    const val = doc[field];
    if (val === undefined || val === null || val === '') {
      errors.push(`"${field}" is required but missing`);
    }
  }
  return errors;
}

// ── Export ────────────────────────────────────────────────────────────────────

function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'space';
}

function draftFilename() {
  const space = slugify(draft.space || 'space');
  const city  = slugify(draft.city  || '');
  const date  = new Date().toISOString().slice(0, 10);
  return city ? `${space}-${city}-${date}.json` : `${space}-${date}.json`;
}

// Prepend https:// when a URL has no scheme. SpaceAPI url/logo consumers expect
// a fully-qualified URL (scheme-less breaks <img src> and card links).
function normalizeUrl(value) {
  const v = (value || '').trim();
  if (!v) return v;
  if (/^https?:\/\//i.test(v)) return v;
  // Leave other explicit schemes (ftp:, data:, etc.) untouched.
  if (/^[a-z][a-z0-9+.-]*:/i.test(v)) return v;
  return `https://${v}`;
}

// SpaceAPI contact.matrix is a room/community, not a personal MXID
// (examples: "#room:server.org", "+community:server.org"). When the value has
// the "name:server" shape but no leading sigil, prepend "#" (the room default).
// Leave existing sigils (# + ! @) untouched. Visible, not silent — same as URL.
function normalizeMatrix(value) {
  const v = (value || '').trim();
  if (!v) return v;
  if (/^[#+!@]/.test(v)) return v;
  if (v.includes(':')) return `#${v}`;
  return v;
}

function assemblev15Doc() {
  // Key order mirrors the wizard tier blocks top-to-bottom so the file builds
  // Maëlle's mental model: meta → Tier 0 → Tier 1 → Tier 2 (mom:) last.
  const doc = {
    api_compatibility: ['15'],
  };

  // ── Tier 0 — floor (name + location) ──
  if (draft.space) doc.space = draft.space;

  // location — address is a single string per v15 schema; country_code is a separate field
  const addrParts = [draft.address, draft.city, draft.postcode, draft.country_code].filter(Boolean);
  const location = {};
  if (addrParts.length) location.address = addrParts.join(', ');
  if (draft.country_code) location.country_code = draft.country_code;
  if (draft.lat !== null) location.lat = draft.lat;
  if (draft.lon !== null) location.lon = draft.lon;
  if (Object.keys(location).length) doc.location = location;

  // ── Tier 1 — SpaceAPI core ──
  // Normalize URL scheme at export too (safety net if blur didn't fire).
  if (draft.logo) doc.logo = normalizeUrl(draft.logo);
  if (draft.url) doc.url = normalizeUrl(draft.url);
  if (draft.description) doc.description = draft.description;

  const contact = {};
  if (draft.contact_email) contact.email = draft.contact_email;
  if (draft.contact_matrix) contact.matrix = normalizeMatrix(draft.contact_matrix);
  if (Object.keys(contact).length) doc.contact = contact;

  // state.open = null (valid v15 boolean/null; pipeline treats null as "opted out").
  // pipeline_helpers.py:97-100 returns None for any non-bool → pipeline.py:173
  // "operator opted out" → space resolves to `confirmed`. Full FSM in Story 9.7.
  doc.state = { open: null };

  // ── Tier 2 — mom: (last; seeds the next frontier) ──
  // mom:memberOf hints Tier 2 network membership (Story 9.6). additionalProperties
  // is open in the v15 schema so it validates.
  doc['mom:memberOf'] = null;

  return doc;
}

async function exportJSON(warnEl) {
  const doc = assemblev15Doc();
  const schema = await loadSchema();
  const errors = validateAgainstSchema(doc, schema);

  if (errors.length > 0 && warnEl) {
    warnEl.innerHTML = `<strong>Validation gaps (export not blocked):</strong><ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`;
    warnEl.style.display = 'block';
  } else if (warnEl) {
    warnEl.style.display = 'none';
  }

  const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = draftFilename();
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── Render ────────────────────────────────────────────────────────────────────

async function render() {
  await fetchCopy();
  const root = document.getElementById('wizard-root');
  if (!root) return;

  const hasDraft = loadDraft();
  const resumeHint = new URLSearchParams(location.search).get('resume') === '1';

  // ?resume=1 with no draft → load at Tier 0 with no pre-fill and no error (AC5)
  if (hasDraft) {
    tier0Passed = !!(draft.lat !== null && draft.lon !== null && draft.space && draft.address &&
      draft.city && draft.country_code);
  }

  root.innerHTML = '';

  // Inject styles
  const style = document.createElement('style');
  style.textContent = CSS;
  root.appendChild(style);

  const container = document.createElement('div');
  container.className = 'wiz-container';
  root.appendChild(container);

  // Bernard intro — launches visible, then recedes to give way to Tier 0 (AC5).
  const introWrap = document.createElement('div');
  introWrap.className = 'bernard-intro';
  introWrap.id = 'bernard-intro';
  const introInner = document.createElement('div');
  introInner.className = 'intro-inner';
  const introText = document.createElement('div');
  introText.className = 'bernard-voice';
  introText.textContent = `— ${COPY.wizard_intro}`;
  introInner.appendChild(introText);
  introWrap.appendChild(introInner);
  container.appendChild(introWrap);

  if (hasDraft) {
    // Resume: snap-collapse with no animation so Tier 0 is immediately the focus.
    introWrap.classList.add('receding');
    introWrap.style.transition = 'none';
  } else {
    // Fresh entry: 2s to read, then intro recedes and Tier 0 slides in together
    // (handoff: both transitions run in parallel so one gives way as the other opens).
    setTimeout(() => {
      introWrap.classList.add('receding');
      revealBeat('tier0-beat');
      revealBeat('beat-name');
      requestAnimationFrame(() => document.getElementById('f-space')?.focus());
    }, 4000);
  }

  // localStorage resume warning (AC5)
  if (hasDraft) {
    const resumeWarn = document.createElement('div');
    resumeWarn.className = 'warn-banner';
    resumeWarn.innerHTML = `— ${COPY.localstorage_warning}
      <div class="warn-banner-actions">
        <button class="clear-link" id="clear-btn">Clear &amp; start over</button>
      </div>`;
    container.appendChild(resumeWarn);
  }

  // ── Tier 0 — hidden behind a beat on fresh entry (P2: intro gives way first) ──
  const tier0Beat = document.createElement('div');
  tier0Beat.className = 'beat';
  tier0Beat.id = 'tier0-beat';
  if (!hasDraft) tier0Beat.setAttribute('inert', '');
  const tier0BeatInner = document.createElement('div');
  tier0BeatInner.className = 'beat-inner';
  tier0Beat.appendChild(tier0BeatInner);
  container.appendChild(tier0Beat);

  const tier0 = document.createElement('div');
  tier0.className = `tier-block${tier0Passed ? '' : ' tier-active'}`;
  tier0.id = 'tier0-block';
  tier0.innerHTML = `
    <div class="tier-label">Tier 0</div>
    <div class="bernard-voice">— ${COPY.floor_gate}</div>

    <!-- Beat 1 — name (always present on entry) -->
    <div class="beat" id="beat-name">
      <div class="beat-inner">
        <div class="field-row">
          <label for="f-space">Space name</label>
          <input id="f-space" type="text" placeholder="e.g. Noisebridge" value="${esc(draft.space)}" />
          <div class="hint kbd-hint">${COPY.keyboard_nav_hint}</div>
        </div>
      </div>
    </div>

    <!-- Beat 2 — location (reveals on commit: Tab / Enter / leaving the name).
         inert until revealed so keyboard focus can't land in it early. -->
    <div class="beat" id="beat-location" inert>
      <div class="beat-inner">
        <div class="bernard-voice beat-ack">— ${COPY.beat_name_ack}</div>
        <div class="field-row">
          <label for="f-address">Street address</label>
          <input id="f-address" type="text" placeholder="e.g. 272 Capp St" value="${esc(draft.address)}" />
        </div>
        <div class="field-row">
          <label for="f-city">City</label>
          <input id="f-city" type="text" placeholder="e.g. San Francisco" value="${esc(draft.city)}" />
        </div>
        <div class="coords-preview${draft.lat !== null && draft.lon !== null ? ' ok' : ''}" id="coords-preview">${esc(coordsText())}</div>
        <!-- Country is DERIVED from the address (§2). This manual fallback only
             surfaces when Nominatim returns no country for the result. -->
        <div id="manual-country" style="display:none">
          <div class="field-row">
            <label for="f-country">Country code</label>
            <div class="hint">${COPY.field_hints.country_code}</div>
            <input id="f-country" type="text" placeholder="e.g. US" maxlength="2" class="input-country" value="${esc(draft.country_code)}" />
          </div>
        </div>
        <div id="manual-coords" style="display:none">
          <div class="field-row">
            <label for="f-lat">Latitude</label>
            <input id="f-lat" type="number" step="any" placeholder="e.g. 37.76" value="${draft.lat !== null ? draft.lat : ''}" />
          </div>
          <div class="field-row">
            <label for="f-lon">Longitude</label>
            <input id="f-lon" type="number" step="any" placeholder="e.g. -122.42" value="${draft.lon !== null ? draft.lon : ''}" />
          </div>
        </div>
      </div>
    </div>

    <!-- Beat 3 — bedrock (reveals once coordinates resolve). inert until then. -->
    <div class="beat" id="beat-bedrock" inert>
      <div class="beat-inner">
        <div class="bernard-voice beat-ack">— ${COPY.bedrock_confirm}</div>
        <div class="btn-row">
          <button class="btn btn-primary" id="continue-btn" ${tier0Passed ? 'style="display:none"' : 'disabled'}>Continue →</button>
        </div>
      </div>
    </div>
  `;
  tier0BeatInner.appendChild(tier0);

  // ── Tier 1 — hidden behind a beat until Tier 0 passes (P2: one beat at a time) ──
  const tier1Beat = document.createElement('div');
  tier1Beat.className = 'beat';
  tier1Beat.id = 'tier1-beat';
  if (!tier0Passed) tier1Beat.setAttribute('inert', '');
  const tier1BeatInner = document.createElement('div');
  tier1BeatInner.className = 'beat-inner';
  tier1Beat.appendChild(tier1BeatInner);
  container.appendChild(tier1Beat);

  const tier1 = document.createElement('div');
  tier1.className = `tier-block${tier0Passed ? ' tier-active' : ''}`;
  tier1.id = 'tier1-block';
  tier1.innerHTML = `
    <div class="tier-label">Tier 1 — SpaceAPI core</div>

    <div class="field-row">
      <label for="f-logo">Logo URL</label>
      <input id="f-logo" type="url" placeholder="https://example.org/logo.png" value="${esc(draft.logo)}" />
      <div class="hint">${COPY.field_hints.logo}</div>
    </div>
    <div class="field-row">
      <label for="f-url">Space website</label>
      <input id="f-url" type="url" placeholder="https://example.org" value="${esc(draft.url)}" />
      <div class="hint">${COPY.field_hints.url}</div>
    </div>
    <div class="field-row">
      <label for="f-description">Description</label>
      <input id="f-description" type="text" placeholder="A hackerspace in the basement of the world." value="${esc(draft.description)}" />
      <div class="hint">${COPY.field_hints.description}</div>
    </div>
    <div class="field-row">
      <label for="f-email">Contact email</label>
      <input id="f-email" type="email" placeholder="hello@example.org" value="${esc(draft.contact_email)}" />
      <div class="hint">${COPY.field_hints.contact_email}</div>
    </div>
    <div class="field-row">
      <label for="f-matrix">Matrix</label>
      <input id="f-matrix" type="text" placeholder="#yourspace:matrix.org" value="${esc(draft.contact_matrix)}" />
      <div class="hint">${COPY.field_hints.contact_matrix}</div>
    </div>
    <div class="field-row">
      <span class="skip-note">Automated open/closed status — currently "opted-out" by default</span>
    </div>
    <div class="bernard-voice">— ${COPY.tier_1_exit}</div>

    <!-- Fork stub (Option B) — two doors, respecting coordinator agency.
         Wired content arrives in Story 9.6 (Tier 2) and Story 9.8 (tutorial). -->
    <div class="fork">
      <div class="bernard-voice fork-label">— Two ways forward. Your call.</div>
      <div class="fork-doors">
        <button class="btn fork-door" id="fork-deeper">
          <span class="fork-door-title">Go deeper →</span>
          <span class="fork-door-sub">Tier 2: membership, opening hours, SDGs</span>
        </button>
        <button class="btn fork-door" id="fork-live">
          <span class="fork-door-title">Go live →</span>
          <span class="fork-door-sub">Host this file yourself</span>
        </button>
      </div>
      <div class="fork-note" id="fork-note" style="display:none"></div>
    </div>
  `;
  tier1BeatInner.appendChild(tier1);

  // ── Ownership strip (AC6, §4 P1) ─────────────────────────────────────────────
  const strip = document.createElement('div');
  strip.className = 'ownership-strip';
  strip.id = 'ownership-strip';
  strip.style.display = 'none';
  strip.innerHTML = `
    <div class="strip-progress"><div class="strip-progress-fill" id="strip-fill"></div></div>
    <div class="strip-row">
      <span class="strip-filename" id="strip-filename"></span>
      <button class="btn strip-export-btn" id="strip-export-btn">${COPY.export_button}</button>
    </div>
    <div class="strip-warn" id="strip-warn" style="display:none"></div>
  `;
  container.appendChild(strip);

  // ── Wire events ──────────────────────────────────────────────────────────────
  wireEvents(container, hasDraft);
}

// Reveal a beat (AC10). instant=true snaps it open with no transition (resume).
function revealBeat(id, instant = false) {
  const el = document.getElementById(id);
  if (!el || el.classList.contains('revealed')) return;
  el.removeAttribute('inert');  // beat is reachable now (keyboard + AT)
  if (instant) {
    el.classList.add('instant', 'revealed');
    // Drop the transition-suppressor next frame so later changes animate.
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.remove('instant')));
  } else {
    el.classList.add('revealed');
  }
}

function coordsText() {
  if (draft.lat !== null && draft.lon !== null) {
    return `${draft.lat}, ${draft.lon}`;
  }
  return '';
}

function esc(str) {
  if (!str && str !== 0) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function wireEvents(container, hasDraft) {
  // Tier 0 fields → draft. Geocoding is NOT triggered on input (recalculating
  // mid-keystroke is jarring) — it fires on COMMIT of the address fields below.
  // Postcode + country are DERIVED (§2), so neither is a typed input on the
  // happy path; f-country only exists in the hidden manual-country fallback.
  const t0FieldMap = {
    'f-space': 'space',
    'f-address': 'address',
    'f-city': 'city',
    'f-country': 'country_code',
  };
  Object.entries(t0FieldMap).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      draft[key] = id === 'f-country' ? el.value.toUpperCase() : el.value;
      saveDraft();
      updateContinueButton();
      if (id === 'f-space' || id === 'f-city' || id === 'f-country') updateStrip();
    });
  });

  // Address commit → geocode (Bernard does the location math, §2/P3). Fires on
  // Tab / Enter / blur of street or city, never per keystroke. The guard inside
  // triggerGeocodeDebounce no-ops until both street + city are present.
  // Enter advances the cursor through the cluster just like Tab (street → city);
  // on the last field it just commits (geocode), focus stays put until the
  // bedrock beat reveals.
  const addrOrder = ['f-address', 'f-city'];
  addrOrder.forEach((id, i) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('blur', () => triggerGeocodeDebounce());
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Tab' && !e.shiftKey) {
        triggerGeocodeDebounce();  // native focus move handles the cursor
      } else if (e.key === 'Enter') {
        e.preventDefault();
        triggerGeocodeDebounce();
        document.getElementById(addrOrder[i + 1])?.focus();  // street → city; last → no-op
      }
    });
  });

  // Beat 1 → Beat 2: the name earns the location ask, but only on *commit* —
  // Tab / Enter / leaving the field — not while typing (a reveal mid-keystroke
  // is jarring). Tab & Enter also carry focus into the first address field so
  // the keyboard flow is unbroken.
  const nameEl = document.getElementById('f-space');
  if (nameEl) {
    const commitName = (moveFocus) => {
      if (!nameEl.value.trim()) return;
      revealBeat('beat-location');
      if (moveFocus) document.getElementById('f-address')?.focus();
    };
    nameEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || (e.key === 'Tab' && !e.shiftKey)) {
        if (!nameEl.value.trim()) return;  // empty → let Tab behave normally
        e.preventDefault();                // we own the hand-off to the address beat
        commitName(true);
      }
    });
    nameEl.addEventListener('blur', () => commitName(false));  // click-away commits, no focus steal
  }

  // Manual lat/lon — cancel any pending geocode debounce so it doesn't overwrite manual input
  ['f-lat', 'f-lon'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      clearTimeout(geocodeDebounceTimer);
      const val = parseFloat(el.value);
      if (id === 'f-lat') draft.lat = isNaN(val) ? null : val;
      else draft.lon = isNaN(val) ? null : val;
      saveDraft();
      // Manual coords are the coordinator's own input → green when valid, but
      // NO UV flash (UV marks Bernard's acts, not the user's).
      const hasCoords = draft.lat !== null && draft.lon !== null;
      updateCoordsPreview(coordsText(), hasCoords ? 'ok' : 'neutral');
      updateContinueButton();
    });
  });

  // Tier 1 fields
  const t1Map = {
    'f-logo': 'logo',
    'f-url': 'url',
    'f-description': 'description',
    'f-email': 'contact_email',
    'f-matrix': 'contact_matrix',
  };
  // On-blur normalizers: fill the prefix the format requires, visibly (not
  // silent) so Maëlle's mental model builds. URL → https:// ; Matrix → # room
  // sigil. Each carries its own feedback message key.
  const normalizers = {
    logo: { fn: normalizeUrl, msg: 'url_scheme_added' },
    url: { fn: normalizeUrl, msg: 'url_scheme_added' },
    contact_matrix: { fn: normalizeMatrix, msg: 'matrix_sigil_added' },
  };
  Object.entries(t1Map).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    const hint = el.closest('.field-row')?.querySelector('.hint');
    const origHint = hint ? hint.textContent : null;
    const norm = normalizers[key];

    el.addEventListener('input', () => {
      draft[key] = el.value;
      saveDraft();
      // The normalize message persists until the coordinator edits the field
      // again (their attention lands on the field first, then the hint — a 3s
      // timer was gone before they read it). Editing = acknowledged → restore.
      if (hint && hint.dataset.norm === '1') {
        hint.textContent = origHint;
        hint.style.color = '';
        delete hint.dataset.norm;
      }
    });

    if (norm) {
      el.addEventListener('blur', () => {
        const normalized = norm.fn(el.value);
        if (normalized !== el.value) {
          el.value = normalized;
          draft[key] = normalized;
          saveDraft();
          if (hint) {
            hint.textContent = COPY.validation_messages[norm.msg];
            hint.style.color = 'var(--accent)';  // amber = Bernard's voice
            hint.dataset.norm = '1';             // mark so input restores it
          }
          flashUV(el);                            // UV on the scrubbed input box = Bernard's labor
        }
      });
    }
  });

  // Enter advances focus through Tier 1 fields in order (same grammar as Tier 0).
  const t1Order = ['f-logo', 'f-url', 'f-description', 'f-email', 'f-matrix'];
  t1Order.forEach((id, i) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById(t1Order[i + 1])?.focus();
      }
    });
  });

  // Continue button — Tier 0 settles, Tier 1 beat reveals (P2: one tier at a time).
  document.getElementById('continue-btn')?.addEventListener('click', () => {
    tier0Passed = true;
    document.getElementById('tier0-block')?.classList.remove('tier-active');  // settle
    revealBeat('tier1-beat');
    document.getElementById('tier1-block')?.classList.add('tier-active');     // frontier
    updateStrip();
    document.getElementById('continue-btn').style.display = 'none';
  });

  // Strip export — always available; validation warn shown in the strip.
  document.getElementById('strip-export-btn')?.addEventListener('click', () => {
    exportJSON(document.getElementById('strip-warn'));
  });

  // Fork stub — content wired in Story 9.6 (Tier 2) and 9.8 (tutorial)
  const forkNote = () => document.getElementById('fork-note');
  document.getElementById('fork-deeper')?.addEventListener('click', () => {
    const n = forkNote();
    if (n) { n.textContent = `— ${COPY.fork_stub.tier2_teaser}`; n.style.display = 'block'; }
  });
  document.getElementById('fork-live')?.addEventListener('click', () => {
    const n = forkNote();
    if (n) { n.textContent = `— ${COPY.fork_stub.tutorial_teaser}`; n.style.display = 'block'; }
  });

  // Clear & start over
  document.getElementById('clear-btn')?.addEventListener('click', () => {
    if (confirm(COPY.validation_messages.clear_confirm)) {
      clearDraft();
      render();
    }
  });

  // Auto-geocode on resumed draft with coords missing (country is derived, not required)
  if (draft.address && draft.city && draft.lat === null) {
    triggerGeocodeDebounce();
  }

  // Resumed draft with coords but no derived country → show the manual fallback
  if (draft.lat !== null && draft.lon !== null && !draft.country_code) {
    showManualCountry(true);
  }

  // Show manual coords if draft has no coords but has address data
  if (draft.lat === null && (draft.address || draft.city)) {
    showManualCoords(true);
  }

  // Initial reveal (AC10 + AC5): on resume, snap all earned beats open instantly.
  // On fresh entry, beat-name is delayed (scheduled above in render() with the
  // intro recede at t=2000ms) so the intro and Tier 0 don't wall up together.
  if (hasDraft) {
    revealBeat('tier0-beat', true);
    revealBeat('beat-name', true);
    if (draft.space && draft.space.trim()) revealBeat('beat-location', true);
    if (draft.lat !== null && draft.lon !== null) revealBeat('beat-bedrock', true);
    if (tier0Passed) revealBeat('tier1-beat', true);
  }

  updateStrip();
}

// Geocode is COMMIT-driven now (Tab/Enter/blur of street or city), so we guard
// at call time — not on a delayed timer that could fire mid-typing in the next
// field. We also dedupe: the same address won't re-geocode on a repeat commit
// (blur fires right after a Tab keydown; editing the address changes the key).
function triggerGeocodeDebounce() {
  const { address, city } = draft;
  if (!address || !city) return;            // not enough committed yet → do nothing
  const key = `${address}|${city}`;
  if (key === lastGeocodeKey) return;       // already geocoded this exact address
  lastGeocodeKey = key;
  clearTimeout(geocodeDebounceTimer);
  geocodeDebounceTimer = setTimeout(async () => {
    const { address, city, postcode, country_code } = draft;
    if (!address || !city) return;  // country is derived now, not required as input

    // "Bernard does the location math" (P3): give the derivation a visible beat
    // — an animated meter + a minimum duration — so the result reads as *derived*,
    // not magicked, and the UV labor-glow has room to land. Real fetch is often
    // instant; we wait for the longer of (fetch, min beat).
    const stopMeter = startCoordsMeter(COPY.validation_messages.geocoding_in_progress);
    const [result] = await Promise.all([
      geocode(address, city, postcode, country_code),
      delay(2300),
    ]);
    stopMeter();

    if (result.error === 'unavailable') {
      draft.lat = null;
      draft.lon = null;
      updateCoordsPreview(COPY.validation_messages.nominatim_unavailable, 'error');
      showManualCoords(true);
    } else if (result.lat === null) {
      draft.lat = null;
      draft.lon = null;
      updateCoordsPreview(COPY.validation_messages.nominatim_no_result, 'error');
      showManualCoords(true);
    } else {
      draft.lat = result.lat;
      draft.lon = result.lon;
      // Postcode + country are what Bernard pulls from the address (§2). Derived
      // → fill silently + narrate next to the pin (· postcode · country); country
      // absent → ask via fallback; postcode absent → simply left empty.
      let derivedNote = `${COPY.validation_messages.geocode_resolved} ${result.lat}, ${result.lon}`;
      if (result.postcode) {
        draft.postcode = result.postcode;
        derivedNote += ` · ${result.postcode}`;
      }
      if (result.country_code) {
        draft.country_code = result.country_code;
        derivedNote += ` · ${result.country_code}`;
        showManualCountry(false);
      } else if (!draft.country_code) {
        showManualCountry(true);  // Nominatim gave no country → graceful manual entry
      }
      saveDraft();
      // Green = valid/confirmed (the coordinator's pin). The UV "working" glow
      // lived on the meter (Bernard's labor) and clears here — no UV on the result.
      updateCoordsPreview(derivedNote, 'ok');
      showManualCoords(false);
      revealBeat('beat-bedrock');  // Beat 2 → Beat 3: pin's dropped, bedrock's reachable
    }
    updateContinueButton();
    updateStrip();
  }, 100);  // prompt on commit — the call-time guard above already prevents double/stale fires
}

// status: 'neutral' (geocoding…/empty) | 'ok' (confirmed coords, green) | 'error' (red)
function updateCoordsPreview(text, status = 'neutral') {
  const el = document.getElementById('coords-preview');
  if (!el) return;
  el.textContent = text;
  el.className = 'coords-preview' + (status === 'error' ? ' error' : status === 'ok' ? ' ok' : '');
}

function delay(ms) { return new Promise((r) => setTimeout(r, ms)); }

// Indeterminate "Bernard's doing the math" meter on the coords line. Cycles a
// block bar (▰▱) while geocoding. Reduced-motion → static label, no bar.
// Returns a stop() that clears the interval.
function startCoordsMeter(label) {
  const el = document.getElementById('coords-preview');
  if (!el) return () => {};
  // UV "working" glow lives on the labor (this beat), not the green result.
  el.className = 'coords-preview uv-working';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) {
    el.textContent = label;
    return () => el.classList.remove('uv-working');
  }
  const total = 11;
  let filled = 0;
  const draw = () => {
    const bar = '▰'.repeat(filled) + '▱'.repeat(total - filled);
    el.textContent = `${label} ${bar}`;
    filled = (filled + 1) % (total + 1);
  };
  draw();
  const timer = setInterval(draw, 110);
  return () => { clearInterval(timer); el.classList.remove('uv-working'); };
}

// UV one-shot glow = Bernard's instant labor made briefly visible (bible §1).
// Used for the normalizer scrub (an instantaneous act); the geocode beat uses
// the sustained .uv-working glow instead. Never plain focus. Restarts cleanly
// if re-triggered; reduced-motion users get a static glow.
function flashUV(el) {
  if (!el) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  el.classList.remove('uv-flash');
  void el.offsetWidth;  // force reflow so the animation restarts
  el.classList.add('uv-flash');
  const clear = () => el.classList.remove('uv-flash');
  if (reduce) {
    // No animationend will fire (animation: none) — hold the static glow then clear.
    setTimeout(clear, 900);
  } else {
    el.addEventListener('animationend', clear, { once: true });
  }
}

function showManualCoords(show) {
  const el = document.getElementById('manual-coords');
  if (el) el.style.display = show ? 'block' : 'none';
  // Geocode failed → nothing could be derived; surface the country fallback too,
  // and keep Continue reachable via manual entry.
  if (show) {
    showManualCountry(true);
    revealBeat('beat-bedrock');
  }
}

// Country is normally derived (§2); this fallback only shows when Nominatim
// returned a result with no country component.
function showManualCountry(show) {
  const el = document.getElementById('manual-country');
  if (el) el.style.display = show ? 'block' : 'none';
}

function updateContinueButton() {
  const ready = !!(draft.space && draft.address && draft.city && draft.country_code &&
    draft.lat !== null && draft.lon !== null);
  const btn = document.getElementById('continue-btn');
  if (btn) btn.disabled = !ready;
  updateStrip();
}

function updateStrip() {
  const strip = document.getElementById('ownership-strip');
  if (!strip) return;
  if (!draft.space) { strip.style.display = 'none'; return; }
  strip.style.display = '';

  const filenameEl = document.getElementById('strip-filename');
  if (filenameEl) filenameEl.textContent = draftFilename();

  const fill = document.getElementById('strip-fill');
  if (!fill) return;
  const hasBedrock = tier0Passed ||
    !!(draft.lat !== null && draft.lon !== null && draft.space && draft.address && draft.city);
  if (hasBedrock) {
    fill.style.width = '100%';
    fill.style.background = 'var(--green)';
  } else {
    let pct = 5;
    if (draft.space) pct += 25;
    if (draft.address || draft.city) pct += 30;
    fill.style.width = `${pct}%`;
    fill.style.background = 'var(--border)';
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
// Script loaded with `defer` — DOM is already parsed when this runs.
// Guard handles the rare case where DOMContentLoaded hasn't fired yet.

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', render);
} else {
  render();
}
