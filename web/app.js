// Maps of Making — hi-fi prototype
// Fullscreen MapLibre + slide-in drawers. Minimal cognitive load.
// Data: /data/spaces.geojson (GeoJSON FeatureCollection materialized from Oxigraph).

(function () {
  'use strict';

  // ───────────────────────────── state
  const state = {
    spaces: [],
    filters: {
      networks: new Set(),     // empty = all
      countries: new Set(),
      statuses: new Set(),
      specialties: new Set(),
    },
    search: '',
    selectedId: null,
    openDrawer: null,          // 'filters' | 'search' | 'preset' | 'addurl' | 'detail' | 'bot' | 'tweaks' | null
    tweaks: {
      mapStyle: 'dim',
      density: 'roomy',
      pulse: 'on',
      showHealthMap: false,
    },
    embed: { centerId: null },
    markers: new Map(),        // id -> maplibre.Marker
    _lastMapStyle: 'dim',      // track last applied style to avoid redundant setStyle() calls
  };

  // ───────────────────────────── dom helpers
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  function el(tag, attrs = {}, children = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') n.className = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(n.style, v);
      else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2), v);
      else if (v === true) n.setAttribute(k, '');
      else if (v === false || v == null) {}
      else n.setAttribute(k, v);
    }
    for (const c of [].concat(children)) {
      if (c == null) continue;
      n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return n;
  }

  // ───────────────────────────── data
  async function loadData() {
    const res = await fetch('/data/spaces.geojson');
    if (!res.ok) {
      console.error(`[loadData] Network error: HTTP ${res.status} ${res.statusText}`);
      document.body.classList.add('data-load-error');
      const loader = document.getElementById('loader');
      if (loader) {
        loader.innerHTML = '<div class="hand" style="color: var(--accent)">Map data temporarily unavailable</div><div class="mono">Try refreshing the page</div>';
      }
      state.spaces = [];
      return;
    }
    let json;
    try {
      json = await res.json();
    } catch (e) {
      console.error('[loadData] JSON parse error:', e.message);
      document.body.classList.add('data-load-error');
      state.spaces = [];
      return;
    }
    // Parse GeoJSON FeatureCollection; flatten properties + geometry into space objects
    const features = json.features || [];
    state.spaces = features.map((f) => ({
      ...f.properties,
      coordinates: {
        lat: f.geometry.coordinates[1],
        lon: f.geometry.coordinates[0],
      },
    }));
  }

  // ───────────────────────────── map
  // Dev: OpenFreeMap (CORS-enabled, no key). Production: swap TILES_URL to self-hosted PMTiles on VPS.
  const TILES_URL = 'https://tiles.openfreemap.org/planet';

  function buildStyle(flavor) {
    const colors = {
      light:     { bg: '#f7f2e7', water: '#b9d5e5', road: '#d4ccbb', building: '#e8e2d6', label: '#2a2a2a' },
      dark:      { bg: '#1a1a2e', water: '#16213e', road: '#333355', building: '#0f3460', label: '#cccccc' },
      grayscale: { bg: '#e8e8e8', water: '#c0d0d8', road: '#bbbbbb', building: '#d0d0d0', label: '#555555' },
    };
    const c = colors[flavor] || colors.light;
    return {
      version: 8,
      glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
      sources: {
        ofm: {
          type: 'vector',
          url: TILES_URL,
          attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a> © <a href="https://openfreemap.org">OpenFreeMap</a>',
        }
      },
      layers: [
        { id: 'background',  type: 'background', paint: { 'background-color': c.bg } },
        { id: 'landcover',   type: 'fill', source: 'ofm', 'source-layer': 'landcover',      paint: { 'fill-color': c.bg, 'fill-opacity': 0.6 } },
        { id: 'water',       type: 'fill', source: 'ofm', 'source-layer': 'water',          paint: { 'fill-color': c.water } },
        { id: 'landuse',     type: 'fill', source: 'ofm', 'source-layer': 'landuse',        paint: { 'fill-color': c.bg, 'fill-opacity': 0.4 } },
        { id: 'roads-minor', type: 'line', source: 'ofm', 'source-layer': 'transportation',
          filter: ['in', ['get', 'class'], ['literal', ['minor', 'service', 'track', 'path']]],
          paint: { 'line-color': c.road, 'line-width': ['interpolate', ['linear'], ['zoom'], 8, 0.3, 14, 1.5] } },
        { id: 'roads-major', type: 'line', source: 'ofm', 'source-layer': 'transportation',
          filter: ['in', ['get', 'class'], ['literal', ['primary', 'secondary', 'tertiary', 'trunk', 'motorway']]],
          paint: { 'line-color': c.road, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.5, 12, 3] } },
        { id: 'buildings',   type: 'fill', source: 'ofm', 'source-layer': 'building',       paint: { 'fill-color': c.building, 'fill-opacity': 0.8 } },
        { id: 'labels-places', type: 'symbol', source: 'ofm', 'source-layer': 'place',
          layout: { 'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']],
            'text-font': ['Noto Sans Regular'],
            'text-size': ['interpolate', ['linear'], ['zoom'], 4, 10, 10, 14],
            'text-max-width': 8 },
          paint: { 'text-color': c.label, 'text-halo-color': c.bg, 'text-halo-width': 1.5 } },
      ],
    };
  }

  let map;
  function initMap() {
    map = new maplibregl.Map({
      container: 'map',
      style: buildStyle('grayscale'),
      center: [4.8, 49.5],   // rough midpoint FR/DE
      zoom: 4.3,
      maxBounds: [[-25, 34], [45, 72]], // [west, south], [east, north] — Atlantic to Ural, N Africa to Scandinavia
      hash: false,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');

    const dismissLoader = () => {
      const ld = $('#loader');
      if (!ld) return;
      ld.style.transition = 'opacity 300ms';
      ld.style.opacity = '0';
      setTimeout(() => ld.remove(), 320);
    };
    map.on('load', () => {
      map.resize();
      renderMarkers();
      dismissLoader();
    });
    // Fallback: if tiles are blocked or load is slow, dismiss anyway.
    setTimeout(() => { try { map.resize(); renderMarkers(); } catch {} dismissLoader(); }, 1500);

    // Close drawers when clicking the map
    map.on('click', (e) => {
      // Only close if we didn't click on a marker element
      const target = e.originalEvent.target;
      if (target && target.closest && target.closest('.map-marker')) return;
      // leave drawers where user put them — this is map-first; only close detail
      if (state.openDrawer === 'detail') setDrawer(null);
    });
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';

  function createMarkerSVG(kind, size, pulseOff) {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', '0 0 22 22');
    svg.classList.add('map-marker', kind);
    svg.style.display = 'block';
    svg.style.overflow = 'visible'; // pulse ring bleeds outside bounds

    const r = 9; // circle radius in viewBox coords
    const cx = 11; const cy = 11;

    if (kind === 'open' && !pulseOff) {
      const ring = document.createElementNS(SVG_NS, 'circle');
      ring.setAttribute('cx', cx); ring.setAttribute('cy', cy); ring.setAttribute('r', r);
      ring.classList.add('marker-pulse');
      svg.appendChild(ring);
    }

    const EMOJI_ONLY = new Set(['aging', 'zombie', 'dead']);
    const MARKER_GLYPH = { broken: '×', aging: '⚠️', zombie: '🧟', dead: '🪦' };

    if (!EMOJI_ONLY.has(kind)) {
      const circle = document.createElementNS(SVG_NS, 'circle');
      circle.setAttribute('cx', cx); circle.setAttribute('cy', cy); circle.setAttribute('r', r);
      circle.classList.add('marker-fill');
      svg.appendChild(circle);
    }

    if (MARKER_GLYPH[kind]) {
      const t = document.createElementNS(SVG_NS, 'text');
      t.setAttribute('x', cx); t.setAttribute('y', cy);
      t.setAttribute('dominant-baseline', 'central');
      t.setAttribute('text-anchor', 'middle');
      t.classList.add(kind === 'broken' ? 'marker-x' : 'marker-emoji');
      t.textContent = MARKER_GLYPH[kind];
      svg.appendChild(t);
    }

    return svg;
  }

  function renderMarkers() {
    state.markers.forEach((m) => m.remove());
    state.markers.clear();
    const visible = filteredSpaces();
    const size = state.tweaks.density === 'compact' ? 14 : 22;
    const pulseOff = state.tweaks.pulse === 'off';
    for (const s of visible) {
      const kind = markerKind(s);
      const svg = createMarkerSVG(kind, size, pulseOff);
      svg.setAttribute('aria-label', `${s.name}, ${s.city}, ${s.country}, status ${kind}`);
      svg.setAttribute('role', 'button');
      svg.setAttribute('tabindex', '0');
      svg.addEventListener('click', (e) => {
        e.stopPropagation();
        selectSpace(s.id, { fly: false });
      });
      svg.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectSpace(s.id, { fly: false }); }
      });
      const marker = new maplibregl.Marker({ element: svg, anchor: 'center' })
        .setLngLat([s.coordinates.lon, s.coordinates.lat])
        .addTo(map);
      state.markers.set(s.id, marker);
    }
    if (state.selectedId) highlightSelected();
    updateCounts();
  }

  function markerKind(s) {
    if (!s || s === null || s === undefined) return 'seeded';
    if (s.status === 'broken' || s.status === 'error') return 'broken';
    if (s.status === 'unlinked' || s.status === 'stale') return 'unlinked';
    if (s.status === 'aging') return 'aging';
    if (s.status === 'zombie') return 'zombie';
    if (s.status === 'dead') return 'dead';
    if (s.open_now) return 'open';
    if (s.status === 'confirmed') return 'confirmed';
    return 'seeded';
  }

  function highlightSelected() {
    state.markers.forEach((m, id) => {
      const nd = m.getElement();
      if (id === state.selectedId) nd.classList.add('selected');
      else nd.classList.remove('selected');
    });
  }

  function selectSpace(id, opts = {}) {
    state.selectedId = id;
    highlightSelected();
    renderDetail();
    // If add-url is open, don't hijack; else open detail drawer
    if (state.openDrawer !== 'addurl') setDrawer('detail');
    if (opts.fly) {
      const s = state.spaces.find((x) => x.id === id);
      if (s) map.flyTo({ center: [s.coordinates.lon, s.coordinates.lat], zoom: Math.max(map.getZoom(), 8), speed: 1.2 });
    }
  }

  // ───────────────────────────── filtering
  function filteredSpaces() {
    const f = state.filters;
    const q = state.search.trim().toLowerCase();
    const HEALTH_STATUSES = new Set(['aging', 'zombie', 'dead']);
    return state.spaces.filter((s) => {
      if (String(state.tweaks.showHealthMap) !== 'true' && HEALTH_STATUSES.has(s.status)) return false;
      if (f.networks.size && !(s.network_memberships || []).some((n) => f.networks.has(n))) return false;
      if (f.countries.size && !f.countries.has(s.country)) return false;
      if (f.statuses.size) {
        const tag = markerKind(s);
        if (!f.statuses.has(tag)) return false;
      }
      if (f.specialties.size && !(s.specialties || []).some((sp) => f.specialties.has(sp))) return false;
      if (q) {
        const hay = (s.name + ' ' + s.city + ' ' + s.country + ' ' + (s.specialties || []).join(' ') + ' ' + (s.network_memberships || []).join(' ')).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function updateCounts() {
    const visible = filteredSpaces();
    const total = state.spaces.length;
    $('#results-count').textContent = String(visible.length);
    $('#drawer-count').textContent = `${visible.length} / ${total}`;
    renderResultsList(visible);
    renderPresetPreview();
    const filterN = state.filters.networks.size + state.filters.countries.size + state.filters.statuses.size + state.filters.specialties.size + (state.search ? 1 : 0);
    $('#filters-summary').textContent = filterN ? `${filterN} filter${filterN > 1 ? 's' : ''} on` : '';
  }

  // ───────────────────────────── filter chips
  function buildFilterChips() {
    // Networks
    const networks = unique(state.spaces.flatMap((s) => s.network_memberships));
    const countries = unique(state.spaces.map((s) => s.country));
    const statuses = ['seeded', 'confirmed', 'open', 'unlinked', 'broken'];
    const specialties = unique(state.spaces.flatMap((s) => s.specialties)).sort();

    renderChips('#chips-network', networks, state.filters.networks);
    renderChips('#chips-country', countries.map((c) => [c, countryLabel(c)]), state.filters.countries);
    renderChips('#chips-status', statuses.map((s) => [s, s]), state.filters.statuses, { swatch: true });
    renderChips('#chips-spec', specialties, state.filters.specialties);
  }

  function renderChips(selector, values, set, opts = {}) {
    const host = $(selector);
    host.innerHTML = '';
    for (const v of values) {
      const [val, label] = Array.isArray(v) ? v : [v, v];
      const count = state.spaces.filter((s) => chipMatches(selector, s, val)).length;
      const btn = el('button', { class: 'chip', 'aria-pressed': set.has(val) ? 'true' : 'false', type: 'button' }, [
        opts.swatch ? el('span', { class: `pin-swatch ${val}` }) : null,
        label.replace(/-/g, ' '),
        el('span', { class: 'count' }, [String(count)])
      ]);
      btn.addEventListener('click', () => {
        if (set.has(val)) set.delete(val); else set.add(val);
        btn.setAttribute('aria-pressed', set.has(val) ? 'true' : 'false');
        renderMarkers();
      });
      host.appendChild(btn);
    }
  }

  function chipMatches(selector, s, val) {
    if (selector === '#chips-network') return (s.network_memberships || []).includes(val);
    if (selector === '#chips-country') return s.country === val;
    if (selector === '#chips-status') return markerKind(s) === val;
    if (selector === '#chips-spec') return (s.specialties || []).includes(val);
    return false;
  }

  function countryLabel(c) { return c === 'FR' ? '🇫🇷 France' : c === 'DE' ? '🇩🇪 Germany' : c; }

  function unique(arr) { return Array.from(new Set(arr)); }

  // ───────────────────────────── results list
  function renderResultsList(visible) {
    const host = $('#results-list');
    host.innerHTML = '';
    if (!visible.length) {
      host.appendChild(el('div', { style: { padding: '24px 14px', color: 'var(--muted)', fontSize: '13px' } }, ['No spaces match these filters.']));
      return;
    }
    for (const s of visible.slice(0, 200)) {
      const kind = markerKind(s);
      const item = el('button', { class: 'result', role: 'option', 'aria-selected': state.selectedId === s.id ? 'true' : 'false', type: 'button' }, [
        el('span', { class: `pin-swatch ${kind}`, style: { marginTop: '2px' } }),
        el('div', { style: { flex: 1, minWidth: 0 } }, [
          el('div', { class: 'name' }, [s.name]),
          el('div', { class: 'meta' }, [`${s.city}, ${s.country} · ${s.network_memberships.join(' · ')}`]),
          el('div', { class: 'tags' }, s.specialties.slice(0, 4).map((sp) => el('span', { class: 'tag' }, [sp]))),
        ]),
        el('span', { class: `status-label ${kind}`, style: { alignSelf: 'flex-start' } }, [kind])
      ]);
      item.addEventListener('click', () => selectSpace(s.id, { fly: true }));
      host.appendChild(item);
    }
  }

  // ───────────────────────────── detail drawer
  function renderDetail() {
    const body = $('#detail-body');
    body.innerHTML = '';
    const s = state.spaces.find((x) => x.id === state.selectedId);
    if (!s) {
      body.appendChild(el('div', { style: { padding: '24px', color: 'var(--muted)' } }, ['Click a pin to see details.']));
      return;
    }
    const kind = markerKind(s);
    // Hero
    body.appendChild(el('div', { class: 'detail-hero' }, [
      el('h3', {}, [s.name]),
      el('div', { class: 'where' }, [`${s.address}`]),
      el('div', { class: 'badges' }, [
        el('span', { class: `status-label ${kind}` }, [kind]),
        ...s.network_memberships.map((n) => el('span', { class: 'status-label', style: { textTransform: 'none', color: 'var(--accent-2)', borderColor: 'var(--accent-2)' } }, [n])),
        s.open_for_hosting ? el('span', { class: 'status-label', style: { textTransform: 'none' } }, ['open for hosting']) : null,
      ])
    ]));
    // Freshness
    body.appendChild(el('div', { class: `freshness ${kind}` }, [
      el('span', { class: 'dot' }),
      el('span', {}, [freshnessText(s)])
    ]));
    // Quick facts
    body.appendChild(el('div', { class: 'detail-section' }, [
      el('div', { class: 'wf-label' }, ['Quick facts']),
      el('dl', { class: 'kv' }, [
        el('dt', {}, ['Hours']), el('dd', {}, [s.opening_hours]),
        el('dt', {}, ['Founded']), el('dd', {}, [String(s.founded)]),
        el('dt', {}, ['Capacity']), el('dd', {}, [`${s.capacity} members`]),
        el('dt', {}, ['Contact']), el('dd', {}, [el('a', { href: `mailto:${s.contact}` }, [s.contact])]),
        el('dt', {}, ['Website']), el('dd', {}, [el('a', { href: s.website, target: '_blank', rel: 'noopener' }, [s.website.replace(/^https?:\/\//, '')])]),
      ])
    ]));
    // Specialties
    body.appendChild(el('div', { class: 'detail-section' }, [
      el('div', { class: 'wf-label' }, ['Specialties']),
      el('div', { class: 'chips' }, s.specialties.map((sp) => el('span', { class: 'chip', 'aria-pressed': 'false', style: { cursor: 'default' } }, [sp])))
    ]));
    // JSON
    body.appendChild(el('div', { class: 'detail-section', style: { padding: 0 } }, [
      el('div', { class: 'wf-label', style: { padding: '12px 16px 0' } }, ['Raw JSON from endpoint']),
      el('pre', { class: 'json' }, [jsonHighlight(jsonForSpace(s))])
    ]));
    // Embed CTA
    const embedBtn = el('button', { class: 'btn btn-primary', style: { margin: '12px 16px 16px', width: 'calc(100% - 32px)' } }, ['⎘ Embed this space →']);
    embedBtn.addEventListener('click', () => embedSpace(s.id));
    body.appendChild(embedBtn);
  }

  function freshnessText(s) {
    if (s.status === 'seeded') return 'Seeded by network — not yet confirmed by the space.';
    if (s.status === 'error' || s.status === 'broken') return `URL broken · last successful fetch: ${timeAgo(s.last_fetched)}.`;
    if (s.status === 'unlinked' || s.status === 'stale') return 'Not linked to a network — present but independent.';
    if (s.status === 'aging') return `Going quiet · last fetched ${timeAgo(s.last_fetched)} ago.`;
    if (s.status === 'zombie') return `Unreachable · last seen ${timeAgo(s.last_fetched)} ago.`;
    if (s.status === 'dead') return 'Permanently closed.';
    if (s.open_now) return `Open right now · last fetched ${timeAgo(s.last_fetched)} ago.`;
    return `Confirmed · last fetched ${timeAgo(s.last_fetched)} ago.`;
  }

  function timeAgo(iso) {
    if (!iso) return 'never';
    const t = new Date(iso.endsWith('Z') ? iso : iso + 'Z').getTime();
    if (isNaN(t)) return 'unknown';
    const sec = (Date.now() - t) / 1000;
    if (sec < 60) return `${Math.round(sec)}s`;
    if (sec < 3600) return `${Math.round(sec / 60)}m`;
    if (sec < 86400) return `${Math.round(sec / 3600)}h`;
    return `${Math.round(sec / 86400)}d`;
  }

  function jsonForSpace(s) {
    // Serve a clean "as if from endpoint" shape, per the article
    return {
      name: s.name,
      address: s.address,
      website: s.website,
      contact: s.contact,
      status: s.status === 'broken' ? 'broken' : (s.open_now ? 'open' : (s.status === 'confirmed' ? 'open' : 'unknown')),
      opening_hours: s.opening_hours,
      specialties: s.specialties,
      network_memberships: s.network_memberships,
      open_for_hosting: s.open_for_hosting,
      coordinates: s.coordinates,
      endpoint_url: s.endpoint_url,
      last_fetched: s.last_fetched,
    };
  }

  function jsonHighlight(obj) {
    const txt = JSON.stringify(obj, null, 2);
    // minimal syntax highlight
    const frag = document.createDocumentFragment();
    const re = /("(?:\\(?:u[0-9a-fA-F]{4}|.)|[^"\\])*")(\s*:)?|(\btrue\b|\bfalse\b|\bnull\b)|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g;
    let last = 0, m;
    while ((m = re.exec(txt))) {
      if (m.index > last) frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
      if (m[1]) {
        const span = document.createElement('span');
        span.className = m[2] ? 'k' : 's';
        span.textContent = m[1] + (m[2] || '');
        frag.appendChild(span);
      } else if (m[3]) {
        const span = document.createElement('span');
        span.className = 'c'; span.textContent = m[3]; frag.appendChild(span);
      } else if (m[4]) {
        const span = document.createElement('span');
        span.className = 'n'; span.textContent = m[4]; frag.appendChild(span);
      }
      last = re.lastIndex;
    }
    if (last < txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
    return frag;
  }

  // ───────────────────────────── preset & embed
  function renderPresetPreview() {
    const visible = filteredSpaces();
    $('#pp-count').textContent = String(visible.length);
    const parts = [];
    if (state.filters.networks.size) parts.push(`networks=${[...state.filters.networks].join(',')}`);
    if (state.filters.countries.size) parts.push(`country=${[...state.filters.countries].join(',')}`);
    if (state.filters.statuses.size) parts.push(`status=${[...state.filters.statuses].join(',')}`);
    if (state.filters.specialties.size) parts.push(`specialty=${[...state.filters.specialties].join(',')}`);
    if (state.search) parts.push(`q=${encodeURIComponent(state.search)}`);
    const q = parts.join('&') || 'all';
    $('#pp-filters').textContent = q;

    const bbox = map ? (() => {
      const b = map.getBounds();
      return `${b.getWest().toFixed(2)},${b.getSouth().toFixed(2)},${b.getEast().toFixed(2)},${b.getNorth().toFixed(2)}`;
    })() : '—';

    const name = $('#preset-name').value.trim() || 'untitled-preset';
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const base = window.location.origin + window.location.pathname;
    const paramParts = [`preset=${slug}`, q !== 'all' ? q : null, `bbox=${bbox}`];
    if (state.embed.centerId) {
      const cs = state.spaces.find((x) => x.id === state.embed.centerId);
      if (cs) paramParts.push(`center=${cs.coordinates.lat.toFixed(5)},${cs.coordinates.lon.toFixed(5)}`);
    }
    const shareUrl = `${base}?${paramParts.filter(Boolean).join('&')}`;

    const iframe = `<figure style="margin:0">\n  <iframe src="${shareUrl}"\n          width="100%" height="520"\n          style="border:1.5px solid #1a1a1a;display:block"\n          title="${name}"\n          loading="lazy"></iframe>\n  <figcaption>Source: <a href="https://mapofmaking.debarquin.eu">Maps of Making</a> · Apache 2.0</figcaption>\n</figure>`;

    $('#code-iframe-text').textContent = iframe;
    $('#code-url-text').textContent = shareUrl;
  }

  function embedSpace(id) {
    const s = state.spaces.find((x) => x.id === id);
    if (!s) return;
    $('#preset-name').value = s.name;
    state.embed.centerId = id;
    if (map) map.flyTo({ center: [s.coordinates.lon, s.coordinates.lat], zoom: Math.max(map.getZoom(), 10), speed: 1.2 });
    setDrawer('preset');
  }

  // ───────────────────────────── add URL (simulated)
  function initAddUrl() {
    const sel = $('#url-space');
    for (const s of [...state.spaces].sort((a,b) => a.name.localeCompare(b.name))) {
      sel.appendChild(el('option', { value: s.id }, [`${s.name} — ${s.city}, ${s.country}`]));
    }
    $('#btn-sample').addEventListener('click', () => {
      const sample = state.spaces.find((s) => s.status === 'seeded');
      if (sample) {
        $('#url-input').value = `${sample.website}/maker.json`;
        $('#url-space').value = sample.id;
      }
    });
    $('#btn-fetch-url').addEventListener('click', () => {
      const out = $('#url-result');
      const url = $('#url-input').value.trim();
      const spaceId = $('#url-space').value;
      if (!url) { out.innerHTML = '<span style="color: var(--accent);">✗ enter a URL first.</span>'; return; }
      out.innerHTML = '<span style="color: var(--muted);">→ resolving DNS… fetching… parsing JSON… validating schema…</span>';
      setTimeout(() => {
        const ok = /^https?:\/\/.+\..+/.test(url);
        if (!ok) {
          out.innerHTML = '<span style="color: var(--accent);">✗ invalid URL shape.</span>';
          return;
        }
        if (spaceId) {
          const s = state.spaces.find((x) => x.id === spaceId);
          if (s) {
            s.status = 'confirmed';
            s.endpoint_url = url;
            s.last_fetched = new Date().toISOString();
            renderMarkers();
            selectSpace(spaceId, { fly: true });
            out.innerHTML = `<span style="color: var(--green);">✓ flipped <b>${s.name}</b> from ⚪ seeded to 🔵 confirmed. Pin updated.</span>`;
            return;
          }
        }
        out.innerHTML = `<span style="color: var(--green);">✓ URL validated (simulated). In production this would enqueue the endpoint for Oxigraph ingestion.</span>`;
      }, 900);
    });
  }

  // ───────────────────────────── drawers / UI wiring
  function setDrawer(name) {
    // Detail & addurl share the right slot — close the other first
    const prev = state.openDrawer;
    if (prev && prev !== name) closeDrawer(prev);
    if (!name) { state.openDrawer = null; return; }
    state.openDrawer = name;
    const id = ({
      filters: 'drawer-filters', search: 'drawer-search', preset: 'drawer-preset',
      addurl: 'drawer-addurl', detail: 'drawer-detail', bot: 'bot-drawer', tweaks: 'tweaks'
    })[name];
    const node = document.getElementById(id);
    if (!node) return;
    node.classList.add('open');
    node.setAttribute('aria-hidden', 'false');
    // Sync top-bar pressed state
    syncTopbar();
    // Focus handling
    const focusable = node.querySelector('input, button, [tabindex]');
    if (focusable && name !== 'detail') focusable.focus({ preventScroll: true });
    // Update preset code if opening preset
    if (name === 'preset') renderPresetPreview();
  }
  function closeDrawer(name) {
    const id = ({
      filters: 'drawer-filters', search: 'drawer-search', preset: 'drawer-preset',
      addurl: 'drawer-addurl', detail: 'drawer-detail', bot: 'bot-drawer', tweaks: 'tweaks'
    })[name];
    const node = document.getElementById(id);
    if (!node) return;
    node.classList.remove('open');
    node.setAttribute('aria-hidden', 'true');
    if (state.openDrawer === name) state.openDrawer = null;
    syncTopbar();
  }
  function toggleDrawer(name) {
    if (state.openDrawer === name) closeDrawer(name);
    else setDrawer(name);
  }
  function syncTopbar() {
    $('#btn-filters').setAttribute('aria-pressed', state.openDrawer === 'filters' ? 'true' : 'false');
    $('#btn-search').setAttribute('aria-pressed', state.openDrawer === 'search' ? 'true' : 'false');
    $('#btn-preset').setAttribute('aria-pressed', state.openDrawer === 'preset' ? 'true' : 'false');
    $('#btn-addurl').setAttribute('aria-pressed', state.openDrawer === 'addurl' ? 'true' : 'false');
    $('#btn-tweaks').setAttribute('aria-pressed', state.openDrawer === 'tweaks' ? 'true' : 'false');
    $('#btn-bot').setAttribute('aria-expanded', state.openDrawer === 'bot' ? 'true' : 'false');
    // When bot drawer is open, hide the FAB
    $('#btn-bot').style.display = state.openDrawer === 'bot' ? 'none' : 'flex';
  }

  function wireUI() {
    $('#btn-filters').addEventListener('click', () => toggleDrawer('filters'));
    $('#btn-search').addEventListener('click', () => toggleDrawer('search'));
    $('#btn-preset').addEventListener('click', () => toggleDrawer('preset'));
    $('#btn-addurl').addEventListener('click', () => toggleDrawer('addurl'));
    $('#btn-tweaks').addEventListener('click', () => toggleDrawer('tweaks'));
    $('#btn-bot').addEventListener('click', () => toggleDrawer('bot'));
    $$('[data-close]').forEach((b) => b.addEventListener('click', () => closeDrawer(b.dataset.close)));

    // ESC closes topmost drawer
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (state.openDrawer) { closeDrawer(state.openDrawer); return; }
      }
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        setDrawer('search');
      }
    });

    // Search
    const si = $('#search-input');
    si.addEventListener('input', () => {
      state.search = si.value;
      renderMarkers();
    });

    // Reset filters
    $('#btn-reset-filters').addEventListener('click', () => {
      state.filters.networks.clear();
      state.filters.countries.clear();
      state.filters.statuses.clear();
      state.filters.specialties.clear();
      state.search = '';
      $('#search-input').value = '';
      buildFilterChips();
      renderMarkers();
    });

    // Preset name → re-render code
    $('#preset-name').addEventListener('input', renderPresetPreview);
    // Copy buttons
    $$('[data-copy]').forEach((b) => b.addEventListener('click', async () => {
      const id = b.dataset.copy;
      const txt = $('#' + id + '-text').textContent;
      const original = b.textContent;
      try {
        await navigator.clipboard.writeText(txt);
        b.textContent = 'copied!';
        setTimeout(() => b.textContent = original, 1200);
      } catch (e) {
        b.textContent = 'copy failed';
        setTimeout(() => b.textContent = original, 1200);
      }
    }));

    // Tweaks
    $$('.tweaks .opts').forEach((group) => {
      const key = group.dataset.tweak;
      group.querySelectorAll('button').forEach((b) => {
        b.addEventListener('click', () => {
          group.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', 'false'));
          b.setAttribute('aria-pressed', 'true');
          state.tweaks[key] = b.dataset.val;
          applyTweaks();
          savePreferences();
        });
      });
    });

    // Keep preset preview bbox fresh as map moves
    if (map) {
      map.on('moveend', () => { if (state.openDrawer === 'preset') renderPresetPreview(); });
    }
  }

  function applyTweaks() {
    const styleMap = { dim: 'grayscale', dark: 'dark' };
    const mapEl = document.getElementById('map');
    if (map) {
      if (state.tweaks.mapStyle !== state._lastMapStyle) {
        state._lastMapStyle = state.tweaks.mapStyle;
        map.once('styledata', () => renderMarkers());
        map.setStyle(buildStyle(styleMap[state.tweaks.mapStyle] || 'grayscale'));
      } else {
        renderMarkers();
      }
    }
    if (mapEl) mapEl.className = 'map-' + state.tweaks.mapStyle;
    if (!map) renderMarkers();
  }

  function loadPreferences() {
    try {
      const stored = localStorage.getItem('mom_preferences');
      if (stored) {
        const prefs = JSON.parse(stored);
        const validKeys = ['mapStyle', 'density', 'pulse'];
        validKeys.forEach((key) => {
          if (key in prefs) state.tweaks[key] = prefs[key];
        });
      }
    } catch (e) {
      // Silently ignore: corrupted JSON, localStorage unavailable, etc.
    }
  }

  function savePreferences() {
    try {
      localStorage.setItem('mom_preferences', JSON.stringify(state.tweaks));
    } catch (e) {
      // Silently ignore: quota exceeded, private mode, etc.
    }
  }

  function syncTweakButtons() {
    $$('.tweaks .opts').forEach((group) => {
      const key = group.dataset.tweak;
      const val = String(state.tweaks[key]);
      group.querySelectorAll('button').forEach((b) => {
        b.setAttribute('aria-pressed', b.dataset.val === val ? 'true' : 'false');
      });
    });
  }

  // ───────────────────────────── drift measurement (DevTools probe)
  window.__driftProbe = () => {
    const rect = map.getContainer().getBoundingClientRect();
    const rows = [];
    state.markers.forEach((m, id) => {
      const ll = m.getLngLat();
      const projected = map.project(ll);
      const el = m.getElement();
      const r = el.getBoundingClientRect();
      const domX = r.left + r.width / 2 - rect.left;
      const domY = r.top + r.height / 2 - rect.top;
      rows.push({ id, lat: ll.lat, lon: ll.lng,
                  dx: +(domX - projected.x).toFixed(2),
                  dy: +(domY - projected.y).toFixed(2) });
    });
    console.table(rows.sort((a, b) => a.lat - b.lat));
    return rows;
  };
  window.__map = () => map;

  // ───────────────────────────── embed detection
  if (window.frameElement !== null) {
    document.body.classList.add('embed-mode');
  }

  // ───────────────────────────── boot
  (async function boot() {
    try {
      await loadData();
      // wait for maplibre
      if (typeof maplibregl === 'undefined') {
        await new Promise((r) => {
          const iv = setInterval(() => { if (typeof maplibregl !== 'undefined') { clearInterval(iv); r(); } }, 40);
        });
      }
      // Register PMTiles protocol — used when TILES_URL switches to self-hosted pmtiles:// in production
      if (typeof pmtiles !== 'undefined') {
        const protocol = new pmtiles.Protocol({ metadata: true });
        maplibregl.addProtocol('pmtiles', protocol.tile);
      }
      loadPreferences();
      initMap();
      buildFilterChips();
      initAddUrl();
      wireUI();
      syncTweakButtons();
      updateCounts();
      // Initial tweaks apply
      applyTweaks();
    } catch (e) {
      console.error(e);
      $('#loader').innerHTML = `<div class="hand" style="color: var(--accent)">Couldn't load seed data.</div><div class="mono">${e.message}</div>`;
    }
  })();
})();
