// Open Hardware Monitor dashboard — consumes the embedded web server's
// /data.json (Utilities/HttpServer.cs GenerateJSON): a pre-order tree of
// {id, Text, Children[], Min, Value, Max, ImageURL} where every value is a
// preformatted display string ("52.0 °C", "1,234 RPM"). We parse the number
// back out for meters/thresholds but always show the server's own string.
(function () {
  'use strict';

  const $ = s => document.querySelector(s);
  const els = {
    url: $('#src-url'), connect: $('#connect'), demo: $('#demo'),
    status: $('#status'), tree: $('#tree'), bridge: $('#bridge'),
    copy: $('#copy-bridge')
  };
  const toast = (msg, opts) => window.TTMToast && TTMToast.show(msg, opts || {});

  const POLL_MS = 5000;
  let timer = null;
  let mode = 'idle'; // idle | demo | live
  let lastTree = null;

  // ---- parsing ------------------------------------------------------------

  // "52.0 °C" -> 52.0 ; "1,234 RPM" -> 1234 ; "" -> null
  function num(s) {
    if (typeof s === 'number') return s;
    if (!s) return null;
    const m = String(s).replace(/,/g, '').match(/-?\d+(\.\d+)?/);
    return m ? parseFloat(m[0]) : null;
  }

  // Category comes from the type-group node's icon (images_icon/temperature.png …)
  function categoryOf(node) {
    const m = /images_icon\/([a-z_]+)\.png/.exec(node.ImageURL || '');
    return m ? m[1] : null;
  }

  // Flatten the tree into hardware blocks: [{name, icon, sensors:[{name, cat, value, min, max, n, nMin, nMax}]}]
  function flatten(root) {
    const blocks = [];
    const machines = (root.Children || []);
    machines.forEach(machine => {
      (machine.Children || []).forEach(function walkHw(hw) {
        const block = { name: hw.Text, icon: categoryOf(hw), sensors: [] };
        (hw.Children || []).forEach(child => {
          if (categoryOf(child) && child.Children && child.Children.length &&
              child.Children.every(c => !c.Children || !c.Children.length)) {
            // a type group (Temperatures / Fans / …) full of leaf sensors
            const cat = categoryOf(child);
            child.Children.forEach(s => block.sensors.push({
              name: s.Text, cat, group: child.Text,
              value: s.Value, min: s.Min, max: s.Max,
              n: num(s.Value), nMin: num(s.Min), nMax: num(s.Max)
            }));
          } else if (child.Children && child.Children.length) {
            walkHw(child); // sub-hardware (e.g. SuperIO chip under mainboard)
          }
        });
        if (block.sensors.length) blocks.push(block);
      });
    });
    return blocks;
  }

  // ---- thresholds ---------------------------------------------------------

  function stateOf(s) {
    if (s.n == null) return '';
    if (s.cat === 'temperature') {
      if (s.n >= 85) return 'hot';
      if (s.n >= 70) return 'warn';
    } else if (s.cat === 'load') {
      if (s.n >= 95) return 'hot';
      if (s.n >= 80) return 'warn';
    }
    return '';
  }

  function meterPct(s) {
    if (s.n == null) return null;
    if (s.cat === 'load' || /%/.test(s.value)) return Math.max(0, Math.min(100, s.n));
    // scale within the session's observed min..max window
    if (s.nMin != null && s.nMax != null && s.nMax > s.nMin)
      return ((s.n - s.nMin) / (s.nMax - s.nMin)) * 100;
    return null;
  }

  // ---- rendering ----------------------------------------------------------

  function render(root) {
    const blocks = flatten(root);
    els.tree.textContent = '';
    if (!blocks.length) {
      els.tree.innerHTML = '<p class="ttm-note">No sensors in the feed.</p>';
      return;
    }
    blocks.forEach(block => {
      const card = document.createElement('div');
      card.className = 'ttm-hw';
      const h = document.createElement('h3');
      h.textContent = block.name;
      card.appendChild(h);
      let lastGroup = null;
      block.sensors.forEach(s => {
        if (s.group !== lastGroup) {
          lastGroup = s.group;
          const g = document.createElement('div');
          g.className = 'ttm-sensor ttm-sensor--group';
          g.innerHTML = '<span class="nm">' + esc(s.group) + '</span><span></span><span></span>';
          card.appendChild(g);
        }
        const row = document.createElement('div');
        row.className = 'ttm-sensor' + (stateOf(s) ? ' ttm-sensor--' + stateOf(s) : '');
        const pct = meterPct(s);
        row.innerHTML =
          '<span class="nm" title="' + esc(s.name) + '">' + esc(s.name) + '</span>' +
          '<span class="meterbar" aria-hidden="true">' +
            (pct == null ? '' : '<i style="width:' + pct.toFixed(1) + '%"></i>') +
          '</span>' +
          '<span class="val">' + esc(s.value || '—') + '</span>';
        card.appendChild(row);
      });
      els.tree.appendChild(card);
    });
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  // ---- map bridge (SpaceAPI fragment) -------------------------------------

  function bridge(root) {
    const blocks = flatten(root);
    const machineNode = (root.Children || [])[0];
    const machine = machineNode ? machineNode.Text : 'machine';
    const temps = [], fans = [];
    blocks.forEach(b => b.sensors.forEach(s => {
      if (s.n == null) return;
      const loc = machine + ' / ' + b.name;
      if (s.cat === 'temperature') temps.push({ value: s.n, unit: '°C', location: loc, name: s.name });
      if (s.cat === 'fan') fans.push({ value: Math.round(s.n), unit: 'RPM', location: loc, name: s.name });
    }));
    const anyLoad = blocks.some(b => b.sensors.some(s => s.cat === 'load' && s.n != null && s.n > 5));
    const doc = {
      api_compatibility: ['14'],
      space: machine,
      url: 'https://example.org',
      location: { lat: 0, lon: 0 },
      state: {
        open: anyLoad,
        message: anyLoad ? 'machine active — sensors report load' : 'machine idle',
        lastchange: Math.floor(Date.now() / 1000)
      },
      sensors: { temperature: temps, fan_speed: fans },
      contact: {},
      'x-source': 'open hardware monitor /data.json via thetechmargin dashboard'
    };
    return JSON.stringify(doc, null, 2);
  }

  // ---- data flow ----------------------------------------------------------

  function apply(root) {
    lastTree = root;
    render(root);
    els.bridge.textContent = bridge(root);
    els.copy.disabled = false;
  }

  function setStatus(txt, tone) {
    els.status.textContent = txt;
    els.status.style.color = tone === 'ok' ? 'var(--ttm-success)'
      : tone === 'bad' ? 'var(--ttm-danger)' : '';
  }

  function stop() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  function startDemo() {
    stop();
    mode = 'demo';
    setStatus('demo', 'ok');
    apply(window.OHM_DEMO());
    timer = setInterval(() => apply(window.OHM_DEMO()), POLL_MS);
    toast('Demo data loaded — values animate like a live feed.', { type: 'success' });
  }

  function normalizeUrl(raw) {
    let u = (raw || '').trim();
    if (!u) return null;
    if (!/^https?:\/\//i.test(u)) u = 'http://' + u;
    if (!/data\.json(\?|$)/.test(u)) u = u.replace(/\/?$/, '/') + 'data.json';
    return u;
  }

  let failStreak = 0;
  async function poll(url) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const root = await res.json();
      failStreak = 0;
      setStatus('live', 'ok');
      apply(root);
    } catch (err) {
      failStreak++;
      setStatus('unreachable', 'bad');
      if (failStreak === 1) {
        toast('Could not reach ' + url + ' — ' + err.message +
          '. If the monitor is running, this is likely CORS: the embedded ' +
          'server sends no Access-Control-Allow-Origin header, so browsers ' +
          'block cross-origin reads. Open this page from the same origin, ' +
          'use a local proxy, or load demo data.', { type: 'error', timeout: 12000 });
      }
    }
  }

  function startLive() {
    const url = normalizeUrl(els.url.value);
    if (!url) { toast('Enter the machine URL first, e.g. http://machine:8085', { type: 'warning' }); return; }
    stop();
    mode = 'live';
    failStreak = 0;
    setStatus('connecting…');
    poll(url);
    timer = setInterval(() => poll(url), POLL_MS);
  }

  // ---- wiring -------------------------------------------------------------

  els.connect.addEventListener('click', startLive);
  els.url.addEventListener('keydown', e => { if (e.key === 'Enter') startLive(); });
  els.demo.addEventListener('click', startDemo);

  els.copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(els.bridge.textContent);
      toast('SpaceAPI fragment copied.', { type: 'success' });
    } catch (_) {
      toast('Copy failed — select the JSON and copy manually.', { type: 'warning' });
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { stop(); }
    else if (mode === 'demo') startDemo();
    else if (mode === 'live') startLive();
  });

  // ?demo=1 auto-loads demo data (handy for the deployed preview)
  if (new URLSearchParams(location.search).has('demo')) startDemo();
})();
