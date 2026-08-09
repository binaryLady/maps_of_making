// Whitelabel loader. Reads site_config (brand / theme / gate) from Supabase,
// caches it in localStorage for 60s, and applies it site-wide:
//   brand → page title, wordmark text, topbar tagline, footer badge name
//   theme → site default theme + site-wide token overrides
//   gate  → enabled flag + copy (stack.js consumes via TTMBrand.get('gate'))
// Precedence stays personal-first: a visitor's own theme choice and custom
// tokens (theme.js) override the published site theme. Fail-soft: without
// Supabase (or offline) the cached/default config applies and nothing breaks.
(function () {
  'use strict';
  var DEFAULTS = {
    brand: { name: '', tagline: '', footer_name: 'thetechmargin', footer_hidden: false, page_title: '' },
    theme: { 'default': null, tokens: {} },
    gate: { enabled: true, title: '', body: '', fine: '' },
  };
  var CACHE_KEY = 'ttm_site_config';
  var TTL_MS = 60000;
  var state = { config: null, ready: null };

  function readCache() {
    try {
      var c = JSON.parse(localStorage.getItem(CACHE_KEY));
      if (c && c.config) return c;
    } catch (e) {}
    return null;
  }
  function writeCache(config) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), config: config })); } catch (e) {}
  }
  function merge(rows) {
    var out = JSON.parse(JSON.stringify(DEFAULTS));
    (rows || []).forEach(function (r) {
      if (out[r.key]) Object.keys(r.value || {}).forEach(function (k) { out[r.key][k] = r.value[k]; });
    });
    return out;
  }

  function fetchRemote() {
    var cfg = window.TTM_CONFIG || {};
    if (!(cfg.supabaseUrl && cfg.supabaseAnonKey && window.supabase)) return Promise.resolve(null);
    try {
      var sb = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
      return sb.from('maps_site_config').select('key, value').then(function (r) {
        if (r.error || !r.data) return null;
        return merge(r.data);
      });
    } catch (e) { return Promise.resolve(null); }
  }

  function applyBrand(config) {
    var b = config.brand || {};
    if (b.page_title) document.title = b.page_title;
    var logo = document.querySelector('.brand .logo');
    if (logo && b.name) logo.textContent = b.name;
    var tag = document.querySelector('.brand .tag');
    if (tag && b.tagline) tag.textContent = b.tagline;
    var badgeName = document.querySelector('.ttm-footer-badge .brand-name');
    if (badgeName && b.footer_name) badgeName.textContent = b.footer_name;
    var badge = document.querySelector('.ttm-footer-badge');
    if (badge && b.footer_hidden) badge.style.display = 'none';
  }
  function applyTheme(config) {
    var t = config.theme || {};
    if (!window.TTMTheme) return;
    // Site tokens go under personal custom tokens (personal wins).
    var site = t.tokens || {};
    var personal = window.TTMTheme.getCustom();
    var mergedTokens = {};
    Object.keys(site).forEach(function (k) { mergedTokens[k] = site[k]; });
    Object.keys(personal).forEach(function (k) { mergedTokens[k] = personal[k]; });
    // Apply inline without persisting site tokens into the personal store.
    var root = document.documentElement;
    Object.keys(mergedTokens).forEach(function (k) {
      if (/^--(ttm|z|radius)-[a-z-]+$/.test(k)) root.style.setProperty(k, String(mergedTokens[k]).slice(0, 64));
    });
    // Site default theme (only where the visitor hasn't chosen)
    if (t['default'] !== null && t['default'] !== undefined) {
      try {
        if (localStorage.getItem('ttm_theme') === null) {
          localStorage.setItem('ttm_theme_default', t['default']);
          window.TTMTheme.apply(window.TTMTheme.current());
        }
      } catch (e) {}
    }
  }
  function applyAll(config) {
    state.config = config;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { applyBrand(config); });
    } else {
      applyBrand(config);
    }
    applyTheme(config);
  }

  // Boot: cached config immediately; remote refresh when stale.
  var cached = readCache();
  applyAll(cached ? merge(Object.keys(cached.config).map(function (k) {
    return { key: k, value: cached.config[k] };
  })) : JSON.parse(JSON.stringify(DEFAULTS)));

  state.ready = (cached && Date.now() - cached.ts < TTL_MS)
    ? Promise.resolve(state.config)
    : fetchRemote().then(function (remote) {
        if (remote) { writeCache(remote); applyAll(remote); }
        return state.config;
      });

  window.TTMBrand = {
    ready: function () { return state.ready; },
    get: function (section) { return (state.config || DEFAULTS)[section] || DEFAULTS[section]; },
    refresh: function () {
      return fetchRemote().then(function (remote) {
        if (remote) { writeCache(remote); applyAll(remote); }
        return state.config;
      });
    },
  };
})();
