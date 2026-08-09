// TTM stack: Supabase client + visitor gate + telemetry, fail-soft throughout.
// - Gate: name + email required once per browser (localStorage ttm_visitor);
//   saved to Supabase table `visitors` when configured. ?nogate=1 skips it
//   (used by the admin a11y audit iframe and the test bench).
// - Telemetry: TTMStack.track(event, props) batches to `telemetry_events`
//   every 5s and on page hide; console-logs in local-only mode.
(function () {
  'use strict';
  var cfg = window.TTM_CONFIG || {};
  var sb = null;
  if (cfg.supabaseUrl && cfg.supabaseAnonKey && window.supabase) {
    try { sb = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey); }
    catch (e) { console.warn('[ttm] supabase init failed:', e.message); }
  }

  var sessionId = (function () {
    try {
      var s = sessionStorage.getItem('ttm_session');
      if (!s) {
        s = 'ts_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
        sessionStorage.setItem('ttm_session', s);
      }
      return s;
    } catch (e) { return 'ts_anon'; }
  })();

  function visitor() {
    try { return JSON.parse(localStorage.getItem('ttm_visitor')); } catch (e) { return null; }
  }

  // ── telemetry ──────────────────────────────────────────────────────────────
  var queue = [];
  function track(event, props) {
    queue.push({
      event: String(event).slice(0, 64),
      props: props || {},
      session_id: sessionId,
      page: location.pathname,
      visitor_email: (visitor() || {}).email || null,
      ts: new Date().toISOString(),
    });
  }
  function flush() {
    if (!queue.length) return;
    var batch = queue.splice(0, queue.length);
    if (!sb) { console.debug('[ttm telemetry local-only]', batch); return; }
    sb.from('maps_telemetry_events').insert(batch).then(function (r) {
      if (r.error) console.warn('[ttm] telemetry insert failed:', r.error.message);
    });
  }
  setInterval(flush, 5000);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') flush();
  });

  // ── gate ───────────────────────────────────────────────────────────────────
  var skipGate = new URLSearchParams(location.search).has('nogate');
  function gateCopy() {
    var g = (window.TTMBrand && window.TTMBrand.get('gate')) || {};
    return {
      enabled: g.enabled !== false,
      title: g.title || 'Before you explore',
      body: g.body || 'Tell us who you are — one time, this browser only. It helps us understand who the map serves.',
      fine: g.fine || 'Stored with the site operator (The Tech Margin). No third parties, no newsletter unless you ask for one.',
    };
  }
  function showGate() {
    var wrap = document.createElement('div');
    wrap.className = 'ttm-gate';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-labelledby', 'ttm-gate-title');
    var copy = gateCopy();
    wrap.innerHTML =
      '<form class="ttm-gate__card">' +
      '<h2 id="ttm-gate-title"></h2>' +
      '<p class="ttm-gate__body"></p>' +
      '<label for="ttm-gate-name">Name</label>' +
      '<input id="ttm-gate-name" name="name" autocomplete="name" required maxlength="120">' +
      '<label for="ttm-gate-email">Email</label>' +
      '<input id="ttm-gate-email" name="email" type="email" autocomplete="email" required maxlength="200">' +
      '<p class="ttm-gate__err" role="alert" aria-live="polite"></p>' +
      '<button class="ttm-gate__submit" type="submit">Enter the map</button>' +
      '<p class="ttm-gate__fine"></p>' +
      '</form>';
    // whitelabeled copy as text (never HTML) — operator-provided strings stay inert
    wrap.querySelector('#ttm-gate-title').textContent = copy.title;
    wrap.querySelector('.ttm-gate__body').textContent = copy.body;
    wrap.querySelector('.ttm-gate__fine').textContent = copy.fine;
    document.body.appendChild(wrap);
    var form = wrap.querySelector('form');
    var nameEl = wrap.querySelector('#ttm-gate-name');
    var mailEl = wrap.querySelector('#ttm-gate-email');
    var errEl = wrap.querySelector('.ttm-gate__err');
    nameEl.focus();
    // keep focus inside the dialog
    wrap.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var els = wrap.querySelectorAll('input,button');
      var first = els[0], last = els[els.length - 1];
      if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
      else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var name = nameEl.value.trim();
      var email = mailEl.value.trim();
      var emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      nameEl.setAttribute('aria-invalid', String(!name));
      mailEl.setAttribute('aria-invalid', String(!emailOk));
      if (!name || !emailOk) {
        errEl.textContent = !name ? 'Please tell us your name.' : 'That email doesn’t look complete.';
        return;
      }
      var rec = { name: name, email: email, first_seen: new Date().toISOString() };
      try { localStorage.setItem('ttm_visitor', JSON.stringify(rec)); } catch (err) {}
      var done = function () {
        track('gate_complete', {});
        wrap.remove();
      };
      if (sb) {
        sb.from('maps_visitors').upsert(
          { name: name, email: email, last_seen: new Date().toISOString(), user_agent: navigator.userAgent.slice(0, 250) },
          { onConflict: 'email' }
        ).then(function (r) {
          if (r.error) console.warn('[ttm] visitor save failed (kept locally):', r.error.message);
          done();
        });
      } else {
        console.debug('[ttm gate local-only]', rec);
        done();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var maybeGate = function () { if (!skipGate && !visitor() && gateCopy().enabled) showGate(); };
    // wait for whitelabel config (cached: instant) so copy + enabled are right
    if (window.TTMBrand) window.TTMBrand.ready().then(maybeGate); else maybeGate();
    track('page_view', { theme: (window.TTMTheme && window.TTMTheme.current()) || 'zine' });
  });

  window.TTMStack = { track: track, flush: flush, visitor: visitor, supabase: function () { return sb; }, sessionId: sessionId };
})();
