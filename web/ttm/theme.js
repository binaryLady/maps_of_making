// TTM theme controller.
// Theme precedence: visitor choice (ttm_theme) → admin default
// (ttm_theme_default) → TTM_CONFIG.defaultTheme. '' = upstream zine look.
// Custom tokens (admin theme customizer): JSON map of {"--ttm-*": value}
// stored under ttm_custom_tokens, applied as inline custom properties on
// <html> — pure-token components pick them up with no further wiring.
(function () {
  'use strict';
  var THEMES = ['', 'ttm', 'terminal'];
  var LABELS = { '': '◑ zine', 'ttm': '◕ ttm', 'terminal': '◱ term' };
  var ALLOWED_TOKEN = /^--(ttm|z|radius)-[a-z-]+$/;

  function stored(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function currentTheme() {
    var v = stored('ttm_theme');
    if (v !== null && THEMES.indexOf(v) !== -1) return v;
    v = stored('ttm_theme_default');
    if (v !== null && THEMES.indexOf(v) !== -1) return v;
    var c = (window.TTM_CONFIG && window.TTM_CONFIG.defaultTheme) || '';
    return THEMES.indexOf(c) !== -1 ? c : '';
  }
  function getCustom() {
    try { return JSON.parse(stored('ttm_custom_tokens')) || {}; } catch (e) { return {}; }
  }
  function applyCustom(tokens) {
    var root = document.documentElement;
    // clear previously applied inline tokens, then set the new map
    Array.prototype.slice.call(root.style).forEach(function (p) {
      if (ALLOWED_TOKEN.test(p)) root.style.removeProperty(p);
    });
    Object.keys(tokens || {}).forEach(function (k) {
      if (ALLOWED_TOKEN.test(k)) root.style.setProperty(k, String(tokens[k]).slice(0, 64));
    });
  }
  function setCustom(tokens) {
    try { localStorage.setItem('ttm_custom_tokens', JSON.stringify(tokens || {})); } catch (e) {}
    applyCustom(tokens || {});
  }
  function resetCustom() { setCustom({}); }
  function apply(theme) {
    if (theme) document.documentElement.setAttribute('data-ttm-theme', theme);
    else document.documentElement.removeAttribute('data-ttm-theme');
    var btn = document.querySelector('.ttm-toggle');
    if (btn) btn.textContent = LABELS[theme];
  }

  apply(currentTheme());   // before first paint
  applyCustom(getCustom());

  document.addEventListener('DOMContentLoaded', function () {
    var topbar = document.querySelector('.topbar');
    if (topbar) {
      // Nav to the stack's other routes — the map previously had no way to
      // reach them from the UI.
      var nav = document.createElement('nav');
      nav.className = 'ttm-nav';
      nav.setAttribute('aria-label', 'Site sections');
      [['Wizard', '/genjson/'], ['Test', '/test/'], ['Admin', '/admin/']].forEach(function (r) {
        var a = document.createElement('a');
        a.href = r[1];
        a.textContent = r[0];
        nav.appendChild(a);
      });
      topbar.appendChild(nav);
      var btn = document.createElement('button');
      btn.className = 'ttm-toggle';
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Switch color theme');
      btn.textContent = LABELS[currentTheme()];
      btn.addEventListener('click', function () {
        var next = THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length];
        try { localStorage.setItem('ttm_theme', next); } catch (e) {}
        apply(next);
        if (window.TTMStack) window.TTMStack.track('theme_change', { theme: next || 'zine' });
      });
      topbar.appendChild(btn);
    }
    var badge = document.createElement('div');
    badge.className = 'ttm-footer-badge';
    badge.innerHTML = 'made with <span class="heart">❤</span> by <span class="brand-name gradient-text-rainbow">thetechmargin</span>';
    document.body.appendChild(badge);
  });

  window.TTMTheme = {
    apply: apply, current: currentTheme, THEMES: THEMES,
    getCustom: getCustom, setCustom: setCustom, resetCustom: resetCustom,
  };
})();
