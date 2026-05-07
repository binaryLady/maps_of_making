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
    showUnhealthy: false,
    tweaks: {
      mapStyle: 'dim',
      density: 'roomy',
      pulse: 'on',
    },
    embed: { centerId: null },
    markers: new Map(),        // id -> maplibre.Marker
    _lastMapStyle: 'dim',      // track last applied style to avoid redundant setStyle() calls
  };

  // ───────────────────────────── dom helpers
  const $ = (sel, root = document) => root.querySelector(sel);
  const escHtml = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
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
        loader.innerHTML = '';
        loader.appendChild(el('div', { class: 'hand', style: { color: 'var(--accent)' } }, ['Map data temporarily unavailable']));
        loader.appendChild(el('div', { class: 'mono' }, ['Try refreshing the page']));
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
  let mapInitialized = false;
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
      if (mapInitialized) return;
      mapInitialized = true;
      map.resize();
      renderMarkers();
      dismissLoader();
    });
    // Fallback: if tiles are blocked or load is slow, dismiss anyway.
    setTimeout(() => { if (!mapInitialized) { mapInitialized = true; try { map.resize(); renderMarkers(); } catch {} dismissLoader(); } }, 1500);

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
      const lat = s.coordinates?.lat, lon = s.coordinates?.lon;
      if (typeof lat !== 'number' || typeof lon !== 'number' || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn('[renderMarkers] skipping space with invalid coords:', s.id, lat, lon);
        continue;
      }
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
        .setLngLat([lon, lat])
        .addTo(map);
      state.markers.set(s.id, marker);
    }
    if (state.selectedId) highlightSelected();
    updateCounts();
  }

  function markerKind(s) {
    if (!s) return 'seeded';
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
      if (!state.showUnhealthy && HEALTH_STATUSES.has(s.status)) return false;
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
    const networks = unique(state.spaces.flatMap((s) => s.network_memberships))
      .map((n) => [n, n.split('/').pop().toUpperCase()]);
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
    // Pre-compute match counts to avoid O(n) filter per chip
    const counts = new Map();
    for (const v of values) {
      const [val] = Array.isArray(v) ? v : [v, v];
      let count = 0;
      for (const s of state.spaces) {
        if (chipMatches(selector, s, val)) count++;
      }
      counts.set(val, count);
    }
    for (const v of values) {
      const [val, label] = Array.isArray(v) ? v : [v, v];
      const count = counts.get(val) || 0;
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
          el('div', { class: 'meta' }, [`${s.city}, ${s.country}${(s.network_memberships || []).length ? ' · ' + s.network_memberships.map((n) => n.split('/').pop().toUpperCase()).join(' · ') : ''}`]),
          el('div', { class: 'tags' }, (s.specialties || []).slice(0, 4).map((sp) => el('span', { class: 'tag' }, [sp]))),
        ]),
        el('span', { class: `status-label ${kind}`, style: { alignSelf: 'flex-start' } }, [kind])
      ]);
      item.addEventListener('click', () => selectSpace(s.id, { fly: true }));
      host.appendChild(item);
    }
  }

  // ───────────────────────────── detail drawer helpers
  function _logoPlaceholder() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '22'); svg.setAttribute('height', '22'); svg.setAttribute('viewBox', '0 0 20 20'); svg.setAttribute('fill', 'none');
    svg.innerHTML = '<rect x="3" y="3" width="14" height="14" stroke="#8a8070" stroke-width="1.4"/><circle cx="7" cy="7.5" r="1.4" fill="#8a8070"/><polyline points="3,14 7,10 10,13 13,10 17,14" stroke="#8a8070" stroke-width="1.4" fill="none"/>';
    return svg;
  }

  function _contactChannel(key) {
    const SVG_ICONS = {
      email: '<path d="M1.5 3h11l-5.5 5L1.5 3zm-1 1v7.5c0 .3.2.5.5.5h12c.3 0 .5-.2.5-.5V4l-6.5 5.5L.5 4z"/>',
      twitter: '<path d="M13 1.5L8.5 6.7l5 5.8H11L7.5 8.4 3.5 12.5H1l4.7-5.4L1.2 1.5H4L7.2 5l3.7-3.5H13z"/>',
      mastodon: '<path d="M7 1C4.2 1 2 3 2 5.5v3C2 10.5 3.8 12 6 12c.4.6.9 1 1 1s.6-.4 1-1c2.2 0 4-1.5 4-3.5v-3C12 3 9.8 1 7 1zm0 1.5c2 0 3.5 1.3 3.5 3V9c0 1.1-1.1 2-2.5 2l-.4.6-.6-.6C5.6 11 4.5 10.1 4.5 9V5.5C4.5 4.3 5.8 2.5 7 2.5zM5.5 5v3.5h1V5h-1zm2 0v3.5h1V5h-1z"/>',
      facebook: '<path d="M8.5 2H7C5.9 2 5 2.9 5 4v1H3.5v2H5v5h2V7h1.5l.5-2H7V4.2c0-.4.2-.7.7-.7H8.5V2z"/>',
    };
    const URL_KEYS = new Set(['twitter', 'mastodon', 'facebook', 'website', 'ml', 'blog']);
    const TEXT_LABELS = { phone: '[ph]', irc: '[#]', website: '↗', ml: '↗', matrix: '[mx]', foursquare: '[fs]' };

    const action = URL_KEYS.has(key) ? 'url' : 'copy';
    let node;
    if (SVG_ICONS[key]) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 14 14'); svg.setAttribute('fill', 'currentColor');
      svg.setAttribute('width', '15'); svg.setAttribute('height', '15');
      svg.innerHTML = SVG_ICONS[key];
      node = svg;
    } else {
      const label = TEXT_LABELS[key] || '[' + key.slice(0, 2) + ']';
      node = document.createTextNode(label);
    }
    return { node, action };
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
    // Share CTA in drawer header (hidden on mobile via CSS)
    const drawerHead = document.querySelector('#drawer-detail .drawer-head');
    let shareBtn = drawerHead && drawerHead.querySelector('.share-cta');
    const SHARE_SVG = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><circle cx="11" cy="3" r="1.6"/><circle cx="11" cy="11" r="1.6"/><circle cx="3" cy="7" r="1.6"/><line x1="9.7" y1="3.7" x2="4.3" y2="6.3"/><line x1="4.3" y1="7.7" x2="9.7" y2="10.3"/></svg>';
    if (drawerHead && !shareBtn) {
      shareBtn = el('button', { class: 'share-cta', title: 'Copy profile link', style: { marginLeft: 'auto', width: '28px', height: '28px', border: '1.5px solid var(--rule)', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'transparent', cursor: 'pointer', borderRadius: '2px', marginRight: '0' } }, []);
      shareBtn.innerHTML = SHARE_SVG;
      const closeBtn = drawerHead.querySelector('.close');
      drawerHead.insertBefore(shareBtn, closeBtn);
    }
    if (shareBtn) {
      shareBtn.onclick = () => {
        const url = window.location.origin + '/?space=' + s.id;
        navigator.clipboard.writeText(url).then(() => {
          shareBtn.textContent = '✓';
          setTimeout(() => { shareBtn.innerHTML = SHARE_SVG; }, 1500);
        }).catch(() => {});
      };
    }
    const networkLabel = (urn) => urn.split('/').pop().toUpperCase();

    // ── Hero ──
    const logoBox = el('div', { class: 'sp-logo' });
    if (s.logo) {
      const img = document.createElement('img');
      img.src = s.logo;
      img.alt = '';
      img.onerror = () => { img.remove(); logoBox.classList.add('is-placeholder'); logoBox.appendChild(_logoPlaceholder()); };
      logoBox.appendChild(img);
    } else {
      logoBox.classList.add('is-placeholder');
      logoBox.appendChild(_logoPlaceholder());
    }
    const badgeKindClass = { open: 'sp-badge-open', confirmed: 'sp-badge-confirmed', broken: 'sp-badge-broken', seeded: 'sp-badge-seeded' };
    body.appendChild(el('div', { class: 'sp-hero' }, [
      el('div', { class: 'sp-name-row' }, [
        el('div', { class: 'sp-name' }, [s.name]),
        logoBox,
      ]),
      el('div', { class: 'sp-address' }, [s.address || el('em', { class: 'sp-fact-empty' }, ['address not provided'])]),
      el('div', { class: 'sp-badges-row' }, [
        el('span', { class: `sp-badge ${badgeKindClass[kind] || 'sp-badge-tag'}` }, [kind]),
        ...(s.network_memberships || []).map((n) => el('span', { class: 'sp-badge sp-badge-tag' }, [networkLabel(n)])),
        s.open_for_hosting ? el('span', { class: 'sp-badge sp-badge-tag' }, ['open for hosting']) : null,
      ]),
    ]));

    // ── Status bar (non-seeded) ──
    if (s.status !== 'seeded') {
      const dotClass = ['aging', 'zombie'].includes(s.status) ? 'sp-dot sp-dot-stale'
        : s.status === 'broken' ? 'sp-dot sp-dot-error' : 'sp-dot';
      const statusPhrases = { open: 'Open right now', confirmed: 'Confirmed', broken: 'Endpoint issue', aging: 'Going quiet', zombie: 'Unreachable', dead: 'Permanently closed' };
      const phrase = statusPhrases[kind] || kind;
      body.appendChild(el('div', { class: 'sp-status-bar' }, [
        el('div', { class: 'sp-status-left' }, [
          el('div', { class: dotClass }),
          el('span', {}, [phrase]),
        ]),
        el('div', { class: 'sp-status-right' }, [
          'updated ' + (s.last_updated ? timeAgo(s.last_updated) + ' ago' : 'unknown')
        ]),
      ]));
    }

    // ── Quick Facts (non-seeded) ──
    if (s.status !== 'seeded') {
      const factsKids = [
        el('span', { class: 'sp-fact-key' }, ['Description']),
        el('span', { class: 'sp-fact-val' }, [s.description || el('em', { class: 'sp-fact-empty' }, ['—'])]),
        el('span', { class: 'sp-fact-key' }, ['Website']),
        el('span', { class: 'sp-fact-val' }, [s.website
          ? el('a', { href: s.website, target: '_blank', rel: 'noopener' }, [s.website.replace(/^https?:\/\//, '')])
          : el('em', { class: 'sp-fact-empty' }, ['—'])]),
        el('span', { class: 'sp-fact-key' }, ['Hours']),
        el('span', { class: 'sp-fact-val' }, [s.opening_hours || el('em', { class: 'sp-fact-empty' }, ['—'])]),
      ];
      // Next event — always rendered (— when missing) so visitors see the gap
      factsKids.push(el('span', { class: 'sp-fact-key' }, ['Next event']));
      factsKids.push(el('span', { class: 'sp-fact-val' }, [s.next_event || el('em', { class: 'sp-fact-empty' }, ['—'])]));

      // Contact — always rendered
      factsKids.push(el('span', { class: 'sp-fact-key' }, ['Contact']));
      const hasContact = s.contact && typeof s.contact === 'object' && Object.keys(s.contact).length > 0;
      if (hasContact) {
        const channelsDiv = el('div', { class: 'sp-channels' });
        Object.entries(s.contact).forEach(([key, val]) => {
          const { node: iconNode, action } = _contactChannel(key);
          const btn = el('button', { class: 'sp-channel', title: `${key}: ${val}` }, []);
          btn.appendChild(iconNode);
          btn.addEventListener('click', () => {
            if (action === 'url') {
              const safeVal = String(val);
              if (safeVal.startsWith('https://') || safeVal.startsWith('http://')) {
                window.open(safeVal, '_blank', 'noopener');
              }
            } else {
              navigator.clipboard.writeText(String(val)).then(() => {
                btn.textContent = '✓';
                setTimeout(() => { btn.innerHTML = ''; btn.appendChild(_contactChannel(key).node); }, 1500);
              }).catch(() => {});
            }
          });
          channelsDiv.appendChild(btn);
        });
        factsKids.push(el('span', { class: 'sp-fact-val' }, [channelsDiv]));
      } else {
        factsKids.push(el('span', { class: 'sp-fact-val' }, [el('em', { class: 'sp-fact-empty' }, ['—'])]));
      }
      body.appendChild(el('div', { class: 'sp-section' }, [
        el('div', { class: 'sp-section-label' }, ['Quick Facts']),
        el('div', { class: 'sp-facts' }, factsKids),
      ]));
    }

    // ── Specialties ──
    if (s.specialties && s.specialties.length > 0) {
      body.appendChild(el('div', { class: 'sp-section' }, [
        el('div', { class: 'sp-section-label' }, ['Specialties']),
        el('div', { class: 'sp-pills' }, s.specialties.map((sp) => el('span', { class: 'sp-pill' }, [sp]))),
      ]));
    }

    // ── Embed CTA (desktop-only via CSS) ──
    if (s.status !== 'seeded') {
      const embedBtn = el('button', { class: 'sp-embed-btn' }, []);
      embedBtn.innerHTML = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><polyline points="4.5,3 1.5,7 4.5,11"/><polyline points="9.5,3 12.5,7 9.5,11"/><line x1="8.2" y1="2.5" x2="5.8" y2="11.5"/></svg> Embed this space →';
      embedBtn.addEventListener('click', () => embedSpace(s.id));
      body.appendChild(el('div', { class: 'sp-section sp-embed-wrap' }, [embedBtn]));
    }

    // ── What your data unlocks / state banners ──
    {
      const ERROR_LABELS = {
        'connection_timeout': 'Connection timeout',
        'invalid_json_ld': 'Invalid JSON-LD',
        'missing_coordinates': 'Missing coordinates',
        'http_error': 'HTTP error',
        '404': 'Endpoint not found (404)',
        '500': 'Server error (500)',
      };

      if (s.status === 'seeded') {
        const bannerDiv = el('div', { class: 'sp-section', style: { cursor: 'pointer' } }, [
          el('div', { class: 'sp-section-label' }, ['Is this your space?']),
          el('div', { style: { fontSize: '13px', color: 'var(--muted)', marginTop: '4px' } }, ['Register your SpaceAPI endpoint to activate it on the map and keep your information up to date.']),
        ]);
        bannerDiv.addEventListener('click', () => setDrawer('addurl'));
        body.appendChild(bannerDiv);
      } else if (s.status === 'broken') {
        const errLabel = ERROR_LABELS[s.error_type] || 'Endpoint unavailable';
        body.appendChild(el('div', { class: 'sp-section' }, [
          el('div', { class: 'sp-section-label' }, ['Endpoint issue']),
          el('div', { style: { fontSize: '13px', color: 'var(--error, #c0392b)', marginTop: '4px' } }, [`${errLabel} — check your SpaceAPI endpoint is reachable and returns valid JSON-LD.`]),
        ]));
      } else if (s.status === 'aging') {
        const agingAgo = s.last_fetched ? ` — last fetched ${timeAgo(s.last_fetched)} ago` : '';
        body.appendChild(el('div', { class: 'sp-section' }, [
          el('div', { class: 'sp-section-label' }, ['Heads up']),
          el('div', { style: { fontSize: '13px', color: 'var(--muted)', marginTop: '4px' } }, [`Going quiet${agingAgo}. Data may be slightly stale.`]),
        ]));
      } else if (s.status === 'zombie') {
        const zombieAgo = s.last_fetched ? `. Last seen ${timeAgo(s.last_fetched)} ago` : '';
        body.appendChild(el('div', { class: 'sp-section' }, [
          el('div', { class: 'sp-section-label' }, ['Heads up']),
          el('div', { style: { fontSize: '13px', color: 'var(--error, #c0392b)', marginTop: '4px' } }, [`Unreachable for a while — information may be outdated${zombieAgo}.`]),
        ]));
      } else if (s.status === 'dead') {
        body.appendChild(el('div', { class: 'sp-section' }, [
          el('div', { class: 'sp-section-label' }, ['Space status']),
          el('div', { style: { fontSize: '13px', color: 'var(--muted)', marginTop: '4px' } }, ['This space is permanently closed.']),
        ]));
      }

      // Stepped unlock section — confirmed or broken-with-guidance
      const showUnlock = (s.status === 'confirmed') || (s.status === 'broken' && s.next_unlock);
      if (showUnlock) {
        const unlockSection = el('div', { class: 'sp-section' }, [
          el('div', { class: 'sp-section-label' }, ['What your data unlocks']),
        ]);
        if (s.subset === 'spaceapi:compatible') {
          const step = el('div', { class: 'sp-unlock-step' }, [
            el('div', { class: 'sp-unlock-marker done' }, ['✓']),
            el('div', { class: 'sp-unlock-body' }, []),
          ]);
          step.querySelector('.sp-unlock-body').innerHTML = '<strong>Full SpaceAPI compatibility</strong> — interoperable with mapall.space.';
          unlockSection.appendChild(step);
        } else {
          const stepDone = el('div', { class: 'sp-unlock-step' }, [
            el('div', { class: 'sp-unlock-marker done' }, ['✓']),
            el('div', { class: 'sp-unlock-body' }, []),
          ]);
          stepDone.querySelector('.sp-unlock-body').innerHTML = "<strong>You're here.</strong> Space is registered on the map.";
          unlockSection.appendChild(stepDone);
          if (s.next_unlock) {
            const stepNext = el('div', { class: 'sp-unlock-step' }, [
              el('div', { class: 'sp-unlock-marker next' }, ['→']),
              el('div', { class: 'sp-unlock-body' }, []),
            ]);
            stepNext.querySelector('.sp-unlock-body').innerHTML = '<strong>Level up.</strong> ' + s.next_unlock.replace(/<|>/g, (c) => c === '<' ? '&lt;' : '&gt;');
            unlockSection.appendChild(stepNext);
          }
        }
        body.appendChild(unlockSection);
      }
    }

    // ── Source Data — desktop only, non-seeded ──
    if (window.innerWidth >= 768 && s.status !== 'seeded') {
      const zone3 = el('div', { class: 'detail-section zone-source', style: { padding: '12px 14px', borderBottom: '1px dashed var(--rule)' } }, [
        el('div', { class: 'sp-section-header' }, [
          el('div', { class: 'sp-section-label' }, ['Source Data']),
          s.endpoint_url ? el('a', { href: s.endpoint_url, target: '_blank', rel: 'noopener', class: 'sp-section-label', style: { textDecoration: 'none', marginBottom: '0' } }, ['↗ Open source']) : null,
        ]),
        el('div', { class: 'raw-content', style: { color: 'var(--muted)', fontSize: '11px' } }, ['Loading source data…']),
      ]);
      body.appendChild(zone3);
      const rawEl = zone3.querySelector('.raw-content');

      const _loadZone3 = () => {
        if (!rawEl) return;
        rawEl.innerHTML = '';
        fetch(`/api/space/${s.id}/raw`)
          .then(r => r.json())
          .then(result => {
            if (!rawEl) return;
            rawEl.innerHTML = '';
            if (result.error || result.truncated) {
              rawEl.textContent = result.truncated ? 'Source data exceeds display limit.' : 'Source unavailable.';
              if (rawEl.parentElement) {
                rawEl.parentElement.querySelector('.sp-refresh-btn')?.remove();
                rawEl.parentElement.appendChild(_makeRefreshBtn(null));
              }
              return;
            }
            const termWrap = el('div', { class: 'sp-terminal-wrap' }, [
              el('div', { class: 'sp-terminal-head' }, [
                el('span', { class: 'sp-terminal-head-label' }, ['JSON · Endpoint Response']),
                el('span', { class: 'sp-terminal-head-meta' }, [result.snapshot_date ? new Date(result.snapshot_date).toLocaleString() : '—']),
              ]),
            ]);
            const pre = document.createElement('pre');
            pre.className = 'json sp-terminal-body';
            pre.appendChild(jsonHighlight(result.raw));
            termWrap.appendChild(pre);
            rawEl.appendChild(termWrap);
            const trustLine = el('div', { class: 'sp-trust-line' }, ['The map only reads & enhances your data — it never edits the source.']);
            rawEl.appendChild(trustLine);
            if (rawEl.parentElement) {
              rawEl.parentElement.querySelector('.sp-refresh-btn')?.remove();
              rawEl.parentElement.appendChild(_makeRefreshBtn(s.last_fetched));
            }
          })
          .catch(() => {
            if (rawEl) {
              rawEl.textContent = 'Source unavailable.';
              if (rawEl.parentElement) {
                rawEl.parentElement.querySelector('.sp-refresh-btn')?.remove();
                rawEl.parentElement.appendChild(_makeRefreshBtn(null));
              }
            }
          });
      };

      const _makeRefreshBtn = (lastFetched) => {
        const btn = document.createElement('button');
        btn.className = 'sp-refresh-btn';
        btn.title = 'Refresh data from endpoint';
        btn.innerHTML = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M12.5 2v3.5h-3.5"/><path d="M12.3 5.3A5.5 5.5 0 1 1 10.1 2.5"/></svg> Refresh from endpoint'
          + (lastFetched ? `<span class="sp-refresh-meta">fetched ${timeAgo(lastFetched)} ago</span>` : '');
        btn.addEventListener('click', () => {
          btn.disabled = true;
          btn.innerHTML = '… Refreshing';
          const msgEl = btn.nextSibling && btn.nextSibling.className === 'sp-refresh-msg' ? btn.nextSibling : null;
          if (msgEl) msgEl.remove();
          fetch(`/api/heartbeat-space/${s.id}`, { method: 'POST' })
            .then(r => r.json().then(body => ({ ok: r.ok, status: r.status, body })))
            .then(({ ok, status, body }) => {
              btn.innerHTML = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M12.5 2v3.5h-3.5"/><path d="M12.3 5.3A5.5 5.5 0 1 1 10.1 2.5"/></svg> Refresh from endpoint';
              btn.disabled = false;
              if (status === 429) {
                const msg = document.createElement('span');
                msg.className = 'sp-refresh-msg';
                const retryAfter = body?.detail?.retry_after_seconds;
                msg.textContent = retryAfter ? `Refreshed recently — try again in ${retryAfter}s` : 'Refreshed recently — try again shortly';
                btn.after(msg);
                setTimeout(() => msg.remove(), 3000);
              } else if (ok) {
                fetch(`/data/spaces.geojson?t=${Date.now()}`)
                  .then(r => r.json())
                  .then(geoJson => {
                    state.spaces = (geoJson.features || []).map(f => ({
                      ...f.properties,
                      coordinates: { lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] },
                    }));
                    renderMarkers();
                    renderDetail();
                  })
                  .catch(() => {})
                  .finally(() => _loadZone3());
              } else {
                const msg = document.createElement('span');
                msg.className = 'sp-refresh-msg sp-refresh-msg--error';
                msg.textContent = 'Refresh failed — try again later';
                btn.after(msg);
                setTimeout(() => msg.remove(), 3000);
              }
            })
            .catch(() => {
              btn.innerHTML = '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px"><path d="M12.5 2v3.5h-3.5"/><path d="M12.3 5.3A5.5 5.5 0 1 1 10.1 2.5"/></svg> Refresh from endpoint';
              btn.disabled = false;
              const msg = document.createElement('span');
              msg.className = 'sp-refresh-msg sp-refresh-msg--error';
              msg.textContent = 'Refresh failed — try again later';
              btn.after(msg);
              setTimeout(() => msg.remove(), 3000);
            });
        });
        return btn;
      };

      _loadZone3();
    }
  }

  function freshnessText(s) {
    if (s.status === 'seeded') return 'Seeded by network — not yet confirmed by the space.';
    if (s.status === 'broken') {
      const ERROR_LABELS = {
        'connection_timeout': 'Connection timeout',
        'invalid_json_ld': 'Invalid JSON-LD',
        'missing_coordinates': 'Missing coordinates',
        'http_error': 'HTTP error',
        '404': 'Not found (404)',
        '500': 'Server error (500)',
      };
      const errorMsg = ERROR_LABELS[s.error_type] || s.error_type || 'URL broken';
      return `🔴 ${errorMsg} · last successful fetch: ${timeAgo(s.last_fetched)}.`;
    }
    if (s.status === 'unlinked' || s.status === 'stale') return 'Not linked to a network — present but independent.';
    if (s.status === 'aging') return `Going quiet · last content update ${timeAgo(s.last_updated)} ago.`;
    if (s.status === 'zombie') return `Unreachable · last content update ${timeAgo(s.last_updated)} ago.`;
    if (s.status === 'dead') return `Long inactive · last content update ${timeAgo(s.last_updated)} ago.`;
    if (s.status === 'broken') return `Endpoint unreachable · last successful fetch ${timeAgo(s.last_fetched)} ago.`;
    if (s.open_now) return `Open right now · last content update ${timeAgo(s.last_updated)} ago.`;
    return `Confirmed · last content update ${timeAgo(s.last_updated)} ago.`;
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

  // ───────────────────────────── add URL
  let _addUrlOriginalHTML = null;

  function _resetAddUrlForm() {
    if (_addUrlOriginalHTML === null) return;
    // Skip if form is already in initial state (avoid double-init on first open)
    const result = $('#url-result');
    const input = $('#url-input');
    if (result && !result.innerHTML && input && !input.value) return;
    $('.addurl-body').innerHTML = _addUrlOriginalHTML;
    _wireAddUrlHandlers();
  }

  function _wireAddUrlHandlers() {
    $('#btn-fetch-url').addEventListener('click', _onFetchUrl);
  }

  async function _onFetchUrl() {
    const out = $('#url-result');
    const url = $('#url-input').value.trim();
    if (!url) { out.innerHTML = ''; out.appendChild(el('span', { style: { color: 'var(--accent)' } }, ['✗ enter a URL first.'])); return; }
    // Basic URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) { out.innerHTML = ''; out.appendChild(el('span', { style: { color: 'var(--accent)' } }, ['✗ URL must start with http:// or https://'])); return; }
    out.innerHTML = ''; out.appendChild(el('span', { style: { color: 'var(--muted)' } }, ['→ resolving DNS…']));
    let data;
    try {
      const resp = await fetch('/api/validate-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (!resp.ok && resp.headers.get('content-type')?.includes('text/html')) {
        out.innerHTML = '';
        out.appendChild(el('span', { style: { color: 'var(--accent)' } }, [`✗ API error: HTTP ${resp.status} — backend may be down`]));
        return;
      }
      data = await resp.json();
    } catch (e) {
      out.innerHTML = '';
      out.appendChild(el('span', { style: { color: 'var(--accent)' } }, [`✗ Network error: ${e.message}`]));
      return;
    }

    const lines = [];
    let blocking = false;

    if (!data.reachable) {
      lines.push({ ok: false, text: `not reachable — ${escHtml(data.error || 'unreachable')}` });
      blocking = true;
    } else {
      lines.push({ ok: true, text: `reachable (${escHtml(data.status_code)} OK)` });
      if (!data.schema_valid) {
        lines.push({ ok: false, text: `schema not recognised — ${escHtml(data.error || 'missing name or space field')}` });
        blocking = true;
      } else {
        const schemaLabel = {
          'spaceapi:compatible': 'SpaceAPI v14 compatible',
          'mom:card': 'SpaceAPI — full detail card',
          'mom:required': 'SpaceAPI — pin only (missing website / opening hours)',
        }[data.subset] || 'schema recognised';
        lines.push({ ok: true, text: schemaLabel });
        lines.push({ ok: true, text: `name: ${escHtml(data.name_found)}` });
        if (!data.coords_found) {
          lines.push({ ok: false, text: 'coordinates missing — add lat/lon under location or schema:geo' });
          blocking = true;
        } else {
          lines.push({ ok: true, text: `coordinates found (${escHtml(data.lat)}, ${escHtml(data.lon)})` });
        }
        if (data.pii_warning) {
          lines.push({ warn: true, text: `personal data detected: ${escHtml((data.pii_fields || []).join(', '))} — will not be stored` });
        }
      }
    }

    out.innerHTML = lines.map((l, i) => {
      const icon = l.warn ? '⚠' : l.ok ? '✓' : '✗';
      const color = l.warn ? 'var(--yellow, #b8860b)' : l.ok ? 'var(--green)' : 'var(--accent)';
      return `<div class="check-line" style="--i:${i};animation-delay:calc(0.1s * var(--i));color:${color};">${icon} ${l.text}</div>`;
    }).join('');

    if (blocking) {
      out.innerHTML += '<div style="color:var(--muted);margin-top:6px;font-size:11px;">↩ Fix the issues above and try again.</div>';
      return;
    }

    const btn = el('button', { id: 'btn-confirm-register', class: 'btn btn-primary', style: 'margin-top:10px;' }, ['Confirm & register your space →']);
    out.appendChild(btn);

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.textContent = 'Registering…';
      let reg;
      try {
        const resp = await fetch('/api/register-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
        });
        reg = await resp.json();
        if (!resp.ok) throw new Error(reg.detail?.error || `HTTP ${resp.status}`);
      } catch (e) {
        btn.disabled = false;
        btn.textContent = 'Confirm & register your space →';
        out.appendChild(el('div', { style: { color: 'var(--accent)', marginTop: '6px' } }, [`✗ Registration failed: ${e.message}`]));
        return;
      }

      // Refresh map state — clear filters first so the new space is always visible
      state.filters.networks.clear();
      state.filters.countries.clear();
      state.filters.statuses.clear();
      state.filters.specialties.clear();
      state.showUnhealthy = false;
      try {
        const geoResp = await fetch(`/data/spaces.geojson?t=${Date.now()}`);
        const geoJson = await geoResp.json();
        state.spaces = (geoJson.features || []).map((f) => ({
          ...f.properties,
          coordinates: { lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] },
        }));
        if (state.selectedId && !state.spaces.find((s) => s.id === state.selectedId)) {
          state.selectedId = null;
        }
        buildFilterChips();
        renderMarkers();
      } catch (_) { /* non-fatal */ }

      const spaceName = reg.space_name || 'Your space';
      // space_uri is "urn:mak:space/{slug}" — extract slug as the local ID
      const parts = reg.space_uri ? reg.space_uri.split('/') : [];
      const spaceId = parts.length > 0 ? parts[parts.length - 1] : null;
      const hasSpace = Boolean(spaceId);

      // Build subset progress message
      const subset = reg.subset || 'none';
      const unlockMsg = reg.unlock_message;
      const nextUnlock = reg.next_unlock;
      const subsetBadge = subset !== 'none' ? `<span class="status-label" style="display:inline-block;margin-left:8px;">${escHtml(subset)}</span>` : '';

      let subsetSection = '';
      if (unlockMsg) {
        subsetSection = `
          <div style="margin-top:16px;padding:12px;background:var(--note-bg);border-radius:4px;">
            <div style="margin-bottom:8px;">Your data unlocks: <strong>${escHtml(unlockMsg)}</strong></div>
            ${nextUnlock ? `<div style="color:var(--muted);font-size:13px;">To unlock ${escHtml(reg.next_subset || 'full compatibility')}: ${escHtml(nextUnlock)}</div>` : ''}
            <div style="color:var(--muted);font-size:12px;margin-top:8px;">
              <a href="https://github.com/SpaceApi/schema" target="_blank" rel="noopener">See schema guide →</a>
            </div>
          </div>
        `;
      }

      $('.addurl-body').innerHTML = `
        <div style="text-align:center;padding:20px 0;">
          <div style="font-size:22px;margin-bottom:8px;">✓ ${escHtml(spaceName)} is live on the map!${subsetBadge}</div>
          <div style="color:var(--muted);margin-bottom:18px;">Your pin has flipped from ⚪ to 🔵.</div>
          ${subsetSection}
          <div style="color:var(--muted);font-size:12px;margin-top:16px;">Opening your space profile…</div>
        </div>`;
      if (hasSpace) {
        setTimeout(() => {
          closeDrawer('addurl');
          selectSpace(spaceId, { fly: true });
        }, unlockMsg ? 8000 : 2000);
      }
    });
  }

  function initAddUrl() {
    _addUrlOriginalHTML = $('.addurl-body').innerHTML;
    _wireAddUrlHandlers();
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
    // Reset addurl form when re-opening (clears post-confirmation screen)
    if (name === 'addurl') { _resetAddUrlForm(); setTimeout(() => { const inp = $('#url-input'); if (inp) inp.focus(); }, 50); }
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
    // Near me (AC5b)
    $('#btn-nearme').addEventListener('click', function nearMeClick() {
      if (!navigator.geolocation) {
        console.warn('[near-me] geolocation API unavailable');
        return;
      }
      const btn = $('#btn-nearme');
      const original = btn.innerHTML;
      btn.innerHTML = '<span aria-hidden="true">⏳</span> <span class="label">Locating…</span>';
      btn.disabled = true;

      function onSuccess(pos) {
        btn.innerHTML = original;
        btn.disabled = false;
        map.flyTo({ center: [pos.coords.longitude, pos.coords.latitude], zoom: 12 });
      }
      function onError(err) {
        btn.innerHTML = original;
        btn.disabled = false;
        if (err.code === 1) {
          console.warn('[near-me] geolocation permission denied');
        } else if (err.code === 3) {
          console.warn('[near-me] geolocation timeout (15s exceeded)');
        } else {
          console.warn('[near-me] geolocation error', err.code, err.message);
        }
      }

      // Use Permissions API first on browsers that support it (Android Chrome 88+)
      // This ensures the permission prompt fires in the same user-gesture tick.
      if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: 'geolocation' }).then(function(result) {
          console.log('[near-me] permission state:', result.state);
          // 'granted', 'prompt', or 'denied'
          if (result.state === 'denied') {
            onError({ code: 1, message: 'Permission denied' });
          } else if (result.state === 'prompt') {
            // State is 'prompt' — show dialog with getCurrentPosition
            navigator.geolocation.getCurrentPosition(onSuccess, onError,
              { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
          } else {
            // State is 'granted' — proceed directly
            navigator.geolocation.getCurrentPosition(onSuccess, onError,
              { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
          }
        }).catch(function() {
          // Permissions API failed — fall back to direct call
          navigator.geolocation.getCurrentPosition(onSuccess, onError,
            { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
        });
      } else {
        navigator.geolocation.getCurrentPosition(onSuccess, onError,
          { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 });
      }
    });
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
    $('#btn-show-unhealthy').addEventListener('click', () => {
      state.showUnhealthy = !state.showUnhealthy;
      $('#btn-show-unhealthy').setAttribute('aria-pressed', state.showUnhealthy ? 'true' : 'false');
      renderMarkers();
    });

    $('#btn-reset-filters').addEventListener('click', () => {
      state.filters.networks.clear();
      state.filters.countries.clear();
      state.filters.statuses.clear();
      state.filters.specialties.clear();
      state.showUnhealthy = false;
      $('#btn-show-unhealthy').setAttribute('aria-pressed', 'false');
      state.search = '';
      const searchInput = $('#search-input');
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      buildFilterChips();
      renderMarkers();
    });

    // Preset name → re-render code
    $('#preset-name').addEventListener('input', renderPresetPreview);
    // Copy buttons
    $$('[data-copy]').forEach((b) => b.addEventListener('click', async () => {
      const id = b.dataset.copy;
      const elem = $('#' + id + '-text');
      if (!elem) {
        console.warn(`[copy] element not found: ${id}-text`);
        return;
      }
      const txt = elem.textContent;
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
    if (map && !map._presetPreviewListenerAdded) {
      map._presetPreviewListenerAdded = true;
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

      // Auto-refresh: poll heartbeat last-run timestamp every 60s.
      // When a new cycle completes, soft-reload GeoJSON without touching map pan/zoom.
      let _lastKnownRun = null;
      setInterval(async () => {
        try {
          const r = await fetch('/api/heartbeat/last-run');
          if (!r.ok) return;
          const { last_run } = await r.json();
          if (!last_run) return;
          if (_lastKnownRun === null) { _lastKnownRun = last_run; return; }
          if (last_run === _lastKnownRun) return;
          _lastKnownRun = last_run;
          const geo = await fetch(`/data/spaces.geojson?t=${Date.now()}`);
          if (!geo.ok) return;
          const geoJson = await geo.json();
          state.spaces = (geoJson.features || []).map((f) => ({
            ...f.properties,
            coordinates: { lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] },
          }));
          buildFilterChips();
          renderMarkers();
          renderDetail();
          updateCounts();
        } catch (_) {}
      }, 60_000);
    } catch (e) {
      console.error(e);
      $('#loader').innerHTML = `<div class="hand" style="color: var(--accent)">Couldn't load seed data.</div><div class="mono">${e.message}</div>`;
    }
  })();
})();
