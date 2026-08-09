// TTM theme controller. Order of precedence: visitor's explicit choice
// (localStorage ttm_theme) → admin default (localStorage ttm_theme_default,
// set from /admin/) → TTM_CONFIG.defaultTheme. '' means the upstream zine look.
(function () {
  'use strict';
  var THEMES = ['', 'ttm', 'terminal'];
  var LABELS = { '': '◑ zine', 'ttm': '◕ ttm', 'terminal': '◱ term' };

  function stored(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function currentTheme() {
    var v = stored('ttm_theme');
    if (v !== null && THEMES.indexOf(v) !== -1) return v;
    v = stored('ttm_theme_default');
    if (v !== null && THEMES.indexOf(v) !== -1) return v;
    var c = (window.TTM_CONFIG && window.TTM_CONFIG.defaultTheme) || '';
    return THEMES.indexOf(c) !== -1 ? c : '';
  }
  function apply(theme) {
    if (theme) document.documentElement.setAttribute('data-ttm-theme', theme);
    else document.documentElement.removeAttribute('data-ttm-theme');
    var btn = document.querySelector('.ttm-theme-toggle');
    if (btn) btn.textContent = LABELS[theme];
  }

  apply(currentTheme()); // before first paint (script runs in <head> order)

  document.addEventListener('DOMContentLoaded', function () {
    // Toggle button, appended to the topbar when one exists (the map page)
    var topbar = document.querySelector('.topbar');
    if (topbar) {
      var btn = document.createElement('button');
      btn.className = 'ttm-theme-toggle';
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
    // Required TTM footer badge (visible in TTM themes only, via CSS)
    var badge = document.createElement('div');
    badge.className = 'ttm-footer-badge';
    badge.innerHTML = 'made with <span class="heart">❤</span> by <span class="brand-name">thetechmargin</span>';
    document.body.appendChild(badge);
  });

  window.TTMTheme = { apply: apply, current: currentTheme, THEMES: THEMES };
})();
