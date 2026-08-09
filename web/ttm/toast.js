// TTM toast notifications. Token-styled, accessible, user-friendly copy.
//   TTMToast.show('Published — live within a minute', { type: 'success' })
// Types: info (default) | success | warning | danger. Auto-dismisses (6s,
// danger 10s), manual dismiss button (44px target), stacks newest-last,
// announced via a polite live region so screen readers hear it without
// being interrupted. Reduced-motion handled in CSS.
(function () {
  'use strict';
  var region = null;
  function ensureRegion() {
    if (region) return region;
    region = document.createElement('div');
    region.className = 'ttm-toasts';
    region.setAttribute('role', 'status');
    region.setAttribute('aria-live', 'polite');
    document.body.appendChild(region);
    return region;
  }
  function show(message, opts) {
    opts = opts || {};
    var type = ['info', 'success', 'warning', 'danger'].indexOf(opts.type) !== -1 ? opts.type : 'info';
    var t = document.createElement('div');
    t.className = 'ttm-toast ttm-toast--' + type;
    var msg = document.createElement('span');
    msg.className = 'ttm-toast__msg';
    msg.textContent = String(message); // text only — never HTML
    var x = document.createElement('button');
    x.className = 'ttm-toast__close';
    x.type = 'button';
    x.setAttribute('aria-label', 'Dismiss notification');
    x.textContent = '×';
    t.appendChild(msg);
    t.appendChild(x);
    ensureRegion().appendChild(t);
    var ttl = opts.timeout || (type === 'danger' ? 10000 : 6000);
    var timer = setTimeout(dismiss, ttl);
    function dismiss() {
      clearTimeout(timer);
      t.classList.add('ttm-toast--out');
      setTimeout(function () { t.remove(); }, 250);
    }
    x.addEventListener('click', dismiss);
    return { dismiss: dismiss };
  }
  window.TTMToast = { show: show };
})();
