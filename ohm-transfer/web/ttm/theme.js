// TTM theme + navigation controller.
// Injects one accessible hamburger (fixed, top-right, every page that loads
// this script) collapsing: site routes in hierarchy order, then theme choice.
// A11y per the TTM spec + ARIA disclosure/menu practices: aria-expanded /
// aria-controls, focus moves in on open, Tab is trapped, Escape and backdrop
// close and return focus, aria-current marks the page you are on, 44px
// targets, reduced-motion honored in CSS.
// Theme precedence: visitor choice → admin default → config default.
(function () {
  'use strict';
  var THEMES = ['', 'ttm', 'terminal'];
  var THEME_LABELS = { '': 'Zine', 'ttm': 'Dark', 'terminal': 'Terminal' };
  var ALLOWED_TOKEN = /^--(ttm|z|radius)-[a-z-]+$/;
  // Information hierarchy: the product first, publishing second, operator
  // tools last, each with a role line so the list reads as a sitemap.
  var ROUTES = [
    { href: '/',         name: 'Dashboard',       desc: 'live hardware sensors' },
    { href: '/?demo=1',  name: 'Demo feed',       desc: 'animated mock sensor data' },
    { group: 'Operator tools' },
    { href: '/admin/',   name: 'Mission Control', desc: 'telemetry · visitors (admin)' },
    { group: 'Network' },
    { href: 'https://maps-of-making.vercel.app/', name: 'Maps of Making',
      desc: 'where the map bridge publishes to' },
  ];

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
    document.querySelectorAll('.ttm-menu__theme input').forEach(function (r) {
      r.checked = r.value === theme;
    });
  }

  apply(currentTheme());
  applyCustom(getCustom());

  function buildMenu() {
    var here = location.pathname.replace(/index\.html$/, '');
    var burger = document.createElement('button');
    burger.className = 'ttm-burger';
    burger.type = 'button';
    burger.setAttribute('aria-label', 'Site menu');
    burger.setAttribute('aria-expanded', 'false');
    burger.setAttribute('aria-controls', 'ttm-menu');
    burger.setAttribute('aria-haspopup', 'true');
    burger.innerHTML = '<span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>';

    var backdrop = document.createElement('div');
    backdrop.className = 'ttm-menu__backdrop';

    var panel = document.createElement('div');
    panel.className = 'ttm-menu';
    panel.id = 'ttm-menu';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Site menu');
    panel.setAttribute('aria-hidden', 'true');

    var html = '<div class="ttm-menu__head"><span class="ttm-menu__title">Menu</span>' +
      '<button type="button" class="ttm-menu__close" aria-label="Close menu">×</button></div>';
    // This page's actions: buttons proxy the dashboard's own controls.
    var ACTIONS = [
      { id: 'connect',     name: 'Connect',     desc: 'poll a machine’s data.json' },
      { id: 'demo',        name: 'Demo data',   desc: 'load the animated mock feed' },
      { id: 'copy-bridge', name: 'Copy bridge', desc: 'SpaceAPI fragment to clipboard' },
    ].filter(function (a) { return document.getElementById(a.id); });
    if (ACTIONS.length) {
      html += '<nav aria-label="Dashboard actions"><ul class="ttm-menu__list">';
      ACTIONS.forEach(function (a) {
        html += '<li><button type="button" class="ttm-menu__item ttm-menu__action" data-proxy="' + a.id + '">' +
          '<span class="ttm-menu__name">' + a.name + '</span>' +
          '<span class="ttm-menu__desc">' + a.desc + '</span></button></li>';
      });
      html += '</ul></nav>';
    }
    html += '<nav aria-label="Site sections"><ul class="ttm-menu__list">';
    ROUTES.forEach(function (r) {
      if (r.group) { html += '<li class="ttm-menu__group" role="presentation">' + r.group + '</li>'; return; }
      var current = here === r.href;
      html += '<li><a class="ttm-menu__item" href="' + r.href + '"' +
        (current ? ' aria-current="page"' : '') + '>' +
        '<span class="ttm-menu__name">' + r.name + '</span>' +
        '<span class="ttm-menu__desc">' + r.desc + '</span></a></li>';
    });
    html += '</ul></nav>';
    html += '<fieldset class="ttm-menu__theme"><legend>Theme</legend>';
    THEMES.forEach(function (t) {
      var id = 'ttm-theme-' + (t || 'zine');
      html += '<label for="' + id + '"><input type="radio" id="' + id + '" name="ttm-theme-pick" value="' + t + '"' +
        (currentTheme() === t ? ' checked' : '') + '><span>' + THEME_LABELS[t] + '</span></label>';
    });
    html += '</fieldset>';
    html += '<div class="ttm-menu__keys" aria-label="Keyboard shortcuts">' +
      '<kbd>?</kbd> open this menu &nbsp; <kbd>Esc</kbd> close<br>' +
      '<kbd>g</kbd> then <kbd>d</kbd> dashboard · <kbd>m</kbd> maps of making</div>';
    panel.innerHTML = html;

    function isOpen() { return panel.classList.contains('is-open'); }
    function open() {
      panel.classList.add('is-open'); backdrop.classList.add('is-open');
      panel.setAttribute('aria-hidden', 'false');
      burger.setAttribute('aria-expanded', 'true');
      document.body.classList.add('ttm-menu-open');
      var first = panel.querySelector('a, button, input');
      if (first) first.focus();
    }
    function close(returnFocus) {
      panel.classList.remove('is-open'); backdrop.classList.remove('is-open');
      panel.setAttribute('aria-hidden', 'true');
      burger.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('ttm-menu-open');
      if (returnFocus !== false) burger.focus();
    }
    burger.addEventListener('click', function () {
      isOpen() ? close() : open();
    });
    backdrop.addEventListener('click', function () { close(); });
    panel.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.stopPropagation(); close(); return; }
      if (e.key !== 'Tab') return;
      var els = panel.querySelectorAll('a, button, input');
      var first = els[0], last = els[els.length - 1];
      if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
      else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
    });
    panel.addEventListener('click', function (e) {
      if (e.target.closest('.ttm-menu__close')) { close(); return; }
      var btn = e.target.closest('.ttm-menu__action');
      if (!btn) return;
      close(false);
      var target = document.getElementById(btn.dataset.proxy);
      if (target) { target.click(); target.focus(); }
    });
    panel.addEventListener('change', function (e) {
      if (e.target.name !== 'ttm-theme-pick') return;
      try { localStorage.setItem('ttm_theme', e.target.value); } catch (err) {}
      apply(e.target.value);
      if (window.TTMToast) window.TTMToast.show(
        (THEME_LABELS[e.target.value] || 'Zine') + ' theme.', { type: 'success', timeout: 2500 });
      if (window.TTMStack) window.TTMStack.track('theme_change', { theme: e.target.value || 'zine' });
    });

    document.body.appendChild(backdrop);
    document.body.appendChild(burger);
    document.body.appendChild(panel);

    // ── Keyboard shortcuts: ? lands you in the menu; g-then-key navigates ──
    var pendingG = 0;
    document.addEventListener('keydown', function (e) {
      var tag = (document.activeElement && document.activeElement.tagName) || '';
      if (/INPUT|TEXTAREA|SELECT/.test(tag) || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === '?') { e.preventDefault(); isOpen() ? close() : open(); return; }
      var routes = { d: '/', m: 'https://maps-of-making.vercel.app/' };
      if (pendingG && Date.now() - pendingG < 1500 && routes[e.key]) {
        e.preventDefault();
        pendingG = 0;
        location.href = routes[e.key];
        return;
      }
      pendingG = e.key === 'g' ? Date.now() : 0;
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    buildMenu();
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
