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
  wizard_intro: "Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map.",
  floor_gate: "Name and address. That's the floor. Everything else, I'll derive.",
  localstorage_warning: "Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser.",
  localstorage_resume: "Continuing from where you left off.",
  validation_messages: { clear_confirm: "This will erase your saved progress. Continue?" }
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
    --bg: #1a1a1a;
    --surface: #2e2e2e;
    --border: #555;
    --text: #f0f0f0;
    --muted: #aaa;
    --placeholder: #777;
    --accent: #d4a843;
    --warn: #e07a5f;
    --font-mono: 'Courier New', 'Lucida Console', monospace;
    --mono: var(--font-mono);
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
    border-left: 3px solid var(--accent);
    padding: 0.6rem 1rem;
    margin: 1rem 0;
  }

  .tier-block {
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.5rem;
    margin: 1.5rem 0;
  }

  .tier-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 1rem;
  }

  .field-row {
    margin-bottom: 1.2rem;
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
    margin-bottom: 0.3rem;
    max-height: 2.4em;
    overflow: hidden;
  }

  .field-row input,
  .field-row textarea {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
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

  .field-row input:focus,
  .field-row textarea:focus {
    border-color: var(--accent);
  }

  .coords-preview {
    font-size: 0.8rem;
    color: var(--accent);
    margin-top: 0.4rem;
    min-height: 1.2em;
  }

  .coords-preview.error { color: var(--warn); }

  .btn {
    font-family: var(--mono);
    font-size: 0.9rem;
    padding: 0.6rem 1.4rem;
    border-radius: 3px;
    cursor: pointer;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    transition: border-color 0.15s;
  }

  .btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
  .btn:disabled { opacity: 0.35; cursor: not-allowed; }
  .btn-primary { border-color: var(--accent); color: var(--accent); }

  .btn-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-top: 1.2rem;
    align-items: center;
  }

  .skip-note {
    font-size: 0.8rem;
    color: var(--muted);
    font-style: italic;
  }

  .warn-banner {
    background: #2a1e1e;
    border: 1px solid var(--warn);
    border-radius: 3px;
    padding: 0.8rem 1rem;
    font-size: 0.82rem;
    color: var(--warn);
    margin: 1rem 0;
  }

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

  .tier-locked {
    opacity: 0.4;
    pointer-events: none;
  }

  .validation-warn {
    background: #2a2218;
    border: 1px solid var(--accent);
    border-radius: 3px;
    padding: 0.6rem 1rem;
    font-size: 0.8rem;
    color: var(--accent);
    margin-top: 0.8rem;
  }

  .fork {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
  }

  .fork-label {
    color: var(--accent);
    font-style: italic;
    font-size: 0.9rem;
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
  .fork-door:hover .fork-door-title { color: var(--accent); }
  .fork-door-sub { font-size: 0.75rem; color: var(--muted); }

  .fork-note {
    margin-top: 1rem;
    font-size: 0.8rem;
    color: var(--muted);
    font-style: italic;
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
  a.download = `${slugify(draft.space || 'space')}.json`;
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

  // Bernard intro — once on entry (bible §5, §9); no imagery
  const intro = document.createElement('div');
  intro.className = 'bernard-voice';
  intro.textContent = `— ${COPY.wizard_intro}`;
  container.appendChild(intro);

  // localStorage resume warning (AC5)
  if (hasDraft) {
    const resumeWarn = document.createElement('div');
    resumeWarn.className = 'warn-banner';
    resumeWarn.innerHTML = `— ${COPY.localstorage_warning}
      <div style="margin-top:0.6rem">
        <button class="clear-link" id="clear-btn">Clear &amp; start over</button>
      </div>`;
    container.appendChild(resumeWarn);
  }

  // ── Tier 0 ──────────────────────────────────────────────────────────────────
  const tier0 = document.createElement('div');
  tier0.className = 'tier-block';
  tier0.innerHTML = `
    <div class="tier-label">Tier 0 — Floor</div>
    <div class="bernard-voice">— ${COPY.floor_gate}</div>

    <div class="field-row">
      <label for="f-space">Space name</label>
      <input id="f-space" type="text" placeholder="e.g. Noisebridge" value="${esc(draft.space)}" />
    </div>
    <div class="field-row">
      <label for="f-address">Street address</label>
      <input id="f-address" type="text" placeholder="e.g. 272 Capp St" value="${esc(draft.address)}" />
    </div>
    <div class="field-row">
      <label for="f-city">City</label>
      <input id="f-city" type="text" placeholder="e.g. San Francisco" value="${esc(draft.city)}" />
    </div>
    <div class="field-row">
      <label for="f-postcode">Postcode</label>
      <input id="f-postcode" type="text" placeholder="e.g. 94110" value="${esc(draft.postcode)}" />
    </div>
    <div class="field-row">
      <label for="f-country">Country code</label>
      <input id="f-country" type="text" placeholder="e.g. US" maxlength="2" style="text-transform:uppercase;width:6rem" value="${esc(draft.country_code)}" />
    </div>
    <div class="coords-preview" id="coords-preview">${esc(coordsText())}</div>
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
    <div class="btn-row">
      <button class="btn btn-primary" id="continue-btn" ${tier0Passed ? '' : 'disabled'}>Continue →</button>
      <button class="btn" id="export-btn-t0" ${tier0Passed ? '' : 'disabled'}>Export JSON</button>
    </div>
    <div class="validation-warn" id="val-warn-t0" style="display:none"></div>
  `;
  container.appendChild(tier0);

  // ── Tier 1 ──────────────────────────────────────────────────────────────────
  const tier1 = document.createElement('div');
  tier1.className = `tier-block${tier0Passed ? '' : ' tier-locked'}`;
  tier1.id = 'tier1-block';
  tier1.innerHTML = `
    <div class="tier-label">Tier 1 — SpaceAPI core</div>

    <div class="field-row">
      <label for="f-logo">Logo URL</label>
      <div class="hint">${COPY.field_hints.logo}</div>
      <input id="f-logo" type="url" placeholder="https://example.org/logo.png" value="${esc(draft.logo)}" />
    </div>
    <div class="field-row">
      <label for="f-url">Space website</label>
      <div class="hint">${COPY.field_hints.url}</div>
      <input id="f-url" type="url" placeholder="https://example.org" value="${esc(draft.url)}" />
    </div>
    <div class="field-row">
      <label for="f-description">Description</label>
      <div class="hint">${COPY.field_hints.description}</div>
      <input id="f-description" type="text" placeholder="A hackerspace in the basement of the world." value="${esc(draft.description)}" />
    </div>
    <div class="field-row">
      <label for="f-email">Contact email</label>
      <div class="hint">${COPY.field_hints.contact_email}</div>
      <input id="f-email" type="email" placeholder="hello@example.org" value="${esc(draft.contact_email)}" />
    </div>
    <div class="field-row">
      <label for="f-matrix">Matrix</label>
      <div class="hint">${COPY.field_hints.contact_matrix}</div>
      <input id="f-matrix" type="text" placeholder="#yourspace:matrix.org" value="${esc(draft.contact_matrix)}" />
    </div>
    <div class="field-row">
      <span class="skip-note">open/closed status — deferred to a later step</span>
    </div>
    <div class="bernard-voice">— ${COPY.tier_1_exit}</div>
    <div class="btn-row">
      <button class="btn btn-primary" id="export-btn-t1">Export JSON</button>
    </div>
    <div class="validation-warn" id="val-warn-t1" style="display:none"></div>

    <!-- Fork stub (Option B) — two doors, respecting coordinator agency.
         Wired content arrives in Story 9.6 (Tier 2) and Story 9.8 (tutorial). -->
    <div class="fork">
      <div class="fork-label">— Two ways forward. Your call.</div>
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
  container.appendChild(tier1);

  // ── Wire events ──────────────────────────────────────────────────────────────
  wireEvents(container);
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

function wireEvents() {
  // Tier 0 address fields → draft + debounced geocode
  const t0FieldMap = {
    'f-space': 'space',
    'f-address': 'address',
    'f-city': 'city',
    'f-postcode': 'postcode',
    'f-country': 'country_code',
  };
  Object.entries(t0FieldMap).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      draft[key] = id === 'f-country' ? el.value.toUpperCase() : el.value;
      saveDraft();
      if (['address', 'city', 'postcode', 'country_code'].includes(key)) {
        triggerGeocodeDebounce();
      }
      updateContinueButton();
    });
  });

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
      updateCoordsPreview(coordsText(), false);
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
    el.addEventListener('input', () => { draft[key] = el.value; saveDraft(); });
    const norm = normalizers[key];
    if (norm) {
      el.addEventListener('blur', () => {
        const normalized = norm.fn(el.value);
        if (normalized !== el.value) {
          el.value = normalized;
          draft[key] = normalized;
          saveDraft();
          const hint = el.closest('.field-row')?.querySelector('.hint');
          if (hint) {
            const prev = hint.textContent;
            hint.textContent = COPY.validation_messages[norm.msg];
            hint.style.color = 'var(--accent)';
            setTimeout(() => { hint.textContent = prev; hint.style.color = ''; }, 3000);
          }
        }
      });
    }
  });

  // Continue button
  document.getElementById('continue-btn')?.addEventListener('click', () => {
    tier0Passed = true;
    const t1 = document.getElementById('tier1-block');
    if (t1) t1.classList.remove('tier-locked');
    updateExportButtons();
    document.getElementById('continue-btn').disabled = true;
  });

  // Export buttons
  document.getElementById('export-btn-t0')?.addEventListener('click', () => {
    exportJSON(document.getElementById('val-warn-t0'));
  });
  document.getElementById('export-btn-t1')?.addEventListener('click', () => {
    exportJSON(document.getElementById('val-warn-t1'));
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

  // Auto-geocode on resumed draft with coords missing
  if (draft.address && draft.city && draft.country_code && draft.lat === null) {
    triggerGeocodeDebounce();
  }

  // Show manual coords if draft has no coords but has address data
  if (draft.lat === null && (draft.address || draft.city)) {
    showManualCoords(true);
  }
}

function triggerGeocodeDebounce() {
  clearTimeout(geocodeDebounceTimer);
  geocodeDebounceTimer = setTimeout(async () => {
    const { address, city, postcode, country_code } = draft;
    if (!address || !city || !country_code) return;

    updateCoordsPreview('Geocoding…', false);

    const result = await geocode(address, city, postcode, country_code);

    if (result.error === 'unavailable') {
      draft.lat = null;
      draft.lon = null;
      updateCoordsPreview(COPY.validation_messages.nominatim_unavailable, true);
      showManualCoords(true);
    } else if (result.lat === null) {
      draft.lat = null;
      draft.lon = null;
      updateCoordsPreview(COPY.validation_messages.nominatim_no_result, true);
      showManualCoords(true);
    } else {
      draft.lat = result.lat;
      draft.lon = result.lon;
      saveDraft();
      updateCoordsPreview(`${result.lat}, ${result.lon}`, false);
      showManualCoords(false);
    }
    updateContinueButton();
  }, 800);
}

function updateCoordsPreview(text, isError) {
  const el = document.getElementById('coords-preview');
  if (!el) return;
  el.textContent = text;
  el.className = 'coords-preview' + (isError ? ' error' : '');
}

function showManualCoords(show) {
  const el = document.getElementById('manual-coords');
  if (el) el.style.display = show ? 'block' : 'none';
}

function updateContinueButton() {
  const ready = !!(draft.space && draft.address && draft.city && draft.country_code &&
    draft.lat !== null && draft.lon !== null);
  const btn = document.getElementById('continue-btn');
  if (btn) btn.disabled = !ready;
  updateExportButtons();
}

function updateExportButtons() {
  const ready = !!(draft.lat !== null && draft.lon !== null && draft.space && draft.address);
  ['export-btn-t0', 'export-btn-t1'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.disabled = !ready;
  });
}

// ── Boot ──────────────────────────────────────────────────────────────────────
// Script loaded with `defer` — DOM is already parsed when this runs.
// Guard handles the rare case where DOMContentLoaded hasn't fired yet.

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', render);
} else {
  render();
}
