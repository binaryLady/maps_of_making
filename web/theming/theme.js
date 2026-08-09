// Maps of Making — optional theming + whitelabel loader.
// Everything is opt-in and fail-soft:
//   - No /site.config.json (404) → no behavior at all, upstream look intact.
//   - site.config.json may set: name, tagline, page_title (brand text),
//     theme_default ('' | 'dark'), tokens ({"--mom-*": value} overrides).
//   - A visitor's own choice (localStorage mom_theme) beats the site default.
// API: window.MOMTheme.apply('dark'|''), .current()
(function () {
  'use strict';
  var THEMES = ['', 'dark'];
  var TOKEN = /^--mom-[a-z-]+$/;

  function stored() {
    try { var v = localStorage.getItem('mom_theme'); return THEMES.indexOf(v) !== -1 ? v : null; }
    catch (e) { return null; }
  }
  function apply(theme) {
    if (theme) document.documentElement.setAttribute('data-mom-theme', theme);
    else document.documentElement.removeAttribute('data-mom-theme');
  }
  function applyTokens(tokens) {
    Object.keys(tokens || {}).forEach(function (k) {
      if (TOKEN.test(k)) document.documentElement.style.setProperty(k, String(tokens[k]).slice(0, 64));
    });
  }
  function applyBrand(cfg) {
    if (cfg.page_title) document.title = cfg.page_title;
    var logo = document.querySelector('.brand .logo');
    if (logo && cfg.name) logo.textContent = cfg.name;
    var tag = document.querySelector('.brand .tag');
    if (tag && cfg.tagline) tag.textContent = cfg.tagline;
  }

  var choice = stored();
  if (choice !== null) apply(choice);

  fetch('/site.config.json').then(function (r) {
    if (!r.ok) return null;
    return r.json();
  }).then(function (cfg) {
    if (!cfg) return;
    applyTokens(cfg.tokens);
    if (choice === null && THEMES.indexOf(cfg.theme_default) !== -1) apply(cfg.theme_default);
    var brand = function () { applyBrand(cfg); };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', brand);
    else brand();
  }).catch(function () { /* no config — upstream look, by design */ });

  window.MOMTheme = {
    apply: function (t) {
      if (THEMES.indexOf(t) === -1) return;
      try { localStorage.setItem('mom_theme', t); } catch (e) {}
      apply(t);
    },
    current: function () { return document.documentElement.getAttribute('data-mom-theme') || ''; },
  };
})();
