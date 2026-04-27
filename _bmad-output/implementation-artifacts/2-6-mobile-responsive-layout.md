# Story 2.6: Mobile Responsive Layout

Status: ready-for-dev

## Story

As a maker browsing on a phone,
I want the map to fit, be usable, and help me find spaces near me,
So that I can discover open spaces and share them with my group — without needing a desktop.

**Mobile-first design principle:** Mobile = browsing mode. The mobile experience focuses on "find a space, go there, share it." Coordinator onboarding (Add your URL), health map analytics, and management features are desktop-only. When in doubt about a mobile feature, ask: does this help someone find or visit a space right now?

## Acceptance Criteria

### AC1 — Topbar does not overflow on narrow screens

**Given** the map is loaded on a screen narrower than 768px

**When** the page renders

**Then** the topbar buttons (`Filters`, `Search`, `Preset & embed`, `Add your URL`, `Tweaks`) do not overflow, clip, or wrap into multiple rows

**And** the buttons collapse into a compact icon-only row (labels hidden, icons remain) OR the topbar scrolls horizontally smoothly without clipping

**And** the brand logo remains visible in the top-left at all times

### AC2 — Map fills full viewport height

**Given** the page is loaded on mobile

**When** the page renders

**Then** the map fills the full viewport height minus the topbar — no gap below the topbar, no vertical scrollbar on the map canvas itself

**And** this is verified on a real phone, not just DevTools emulation (Nicolas's phone)

### AC3 — Touch gestures not blocked

**Given** the page is loaded on mobile

**When** the user touches the map

**Then** pinch-to-zoom and drag-to-pan work correctly — no overlay captures touch events and blocks MapLibre's touch handling

### AC4 — Drawers open as bottom sheets on mobile

**Given** the page is viewed on a screen narrower than 768px

**When** any drawer opens (Filters, "Add your URL", detail drawer on pin click)

**Then** the drawer appears as a bottom sheet: `position: fixed; bottom: 0; left: 0; right: 0; width: 100%`

**And** Filters drawer covers ~65% screen height; detail drawer covers ~80–85% (more content to read)

**And** the drawer has a visible drag handle (a short horizontal rule at the top of the sheet) to signal it is dismissible

**And** clicking/tapping outside the sheet or the close button dismisses it

**And** the `prefers-reduced-motion` media query suppresses the slide animation

### AC4b — "Claim this pin" CTA suppressed on mobile

**Given** a space has `status === 'seeded'` (Story 2.2 AC2 adds a CTA on desktop)

**When** the detail drawer opens on a screen narrower than 768px

**Then** the "Claim this pin / Add your URL →" CTA block is not rendered

**And** a single line of whisper text appears instead: `"Visit on desktop to register this space."` using `.wf-label` style (muted, small)

**Design rationale:** URL-pasting onboarding is a poor mobile UX. Mobile focus is browsing, not management. The CTA would add cognitive load without delivering value to the primary mobile persona (Arjun the maker-in-transit).

### AC5b — "📍 Near me" button on mobile

**Given** the page is viewed on a screen narrower than 768px

**When** the topbar renders

**Then** a `📍` icon button appears in the topbar (alongside the collapsed icon buttons)

**When** the user taps it

**Then** the browser requests geolocation permission

**And** on grant: the map flies to the user's position at zoom 12, and spaces within ~10km radius are visually emphasised (or the map simply centers — filter dimming is optional)

**And** on denial or error: silent fallback — no error shown, map stays at current view

**And** on desktop (≥ 768px) the button is also present (makers travel on laptops too) but lower visual priority

### AC8b — "⎘ Copy space link" in detail drawer

**Given** a maker has the detail drawer open for any space

**When** the drawer footer renders

**Then** a `⎘ Copy space link` button appears above the embed button

**When** tapped/clicked

**Then** the space's website URL (`s.website`, or `s.endpoint_url` for confirmed spaces if `s.website` is empty) is copied to the clipboard

**And** the button label changes briefly to `"Copied!"` for 1.5s then resets

**And** if no URL is available (`s.website` and `s.endpoint_url` both empty), the button is hidden

**Design rationale:** Arjun found a space he wants to share with his group chat. One tap copies the space's own page link — no manual text selection, no deep-link infrastructure needed. Works on mobile and desktop equally.

### AC5 — Loader and count text are readable on mobile

**Given** the page is loading on mobile

**When** the loader is visible

**Then** loader text and the results-count element in the topbar are readable — no truncation, no overflow, no illegible font size

### AC6 — Desktop layout is unchanged (≥ 768px)

**Given** the page is viewed on a screen 768px or wider

**Then** all existing desktop layout behaviour is preserved — left/right drawers, topbar with full labels, map height — no regression

### AC7 — Real-phone validation

**Given** the story implementation is complete

**When** Nicolas opens the URL on his actual phone

**Then** he can: browse the map (pan, zoom), open the Filters drawer, open the detail drawer by tapping a pin, and reach the "Add your URL" drawer — all without the layout breaking

**And** the story is not marked done until this is confirmed on hardware (not DevTools)

---

## Tasks / Subtasks

- [ ] **Task 1** — Topbar collapse for mobile (AC1)
  - [ ] Add `@media (max-width: 767px)` rule to hide button labels (keep icons), or enable `overflow-x: auto` on `.seg` if icon-only is not feasible
  - [ ] Ensure `.brand` stays visible (flex-shrink: 0 already present — verify it holds)
  - [ ] Remove `flex-wrap: wrap` behavior from `.topbar` that causes multi-row overflow (currently `flex-wrap: wrap` on `.topbar` line 51 — change to `nowrap` + rely on hidden labels)
  - [ ] Verify `.chip-btn` (Tweaks) collapses cleanly alongside `.seg`

- [ ] **Task 2** — Map viewport height (AC2)
  - [ ] Add CSS variable or JS measurement to ensure `#map` height = `100dvh` minus topbar height
  - [ ] Prefer CSS `height: calc(100dvh - var(--topbar-h))` with `--topbar-h` set via `getComputedStyle` on load and resize; or simply `height: 100dvh` with topbar `position: absolute` already overlaying it (verify current state does not leave a gap)
  - [ ] Test on real phone — iOS Safari and Android Chrome handle `100vh` vs `100dvh` differently

- [ ] **Task 3** — Bottom sheet drawers (AC3, AC4)
  - [ ] Add `@media (max-width: 767px)` overrides for `.drawer.left`, `.drawer.right`, `.drawer.bottom`:
    ```css
    @media (max-width: 767px) {
      .drawer.left, .drawer.right, .drawer.bottom {
        top: auto;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        max-height: 70vh;
        transform: translateY(100%);
        border-radius: 12px 12px 0 0;
      }
      .drawer.left.open, .drawer.right.open, .drawer.bottom.open {
        transform: translateY(0);
      }
    }
    ```
  - [ ] Add drag handle: `<div class="sheet-handle"></div>` as first child of `.drawer-head` — or as a pseudo-element `::before` on `.drawer-head` with `content: ''; width: 40px; height: 4px; background: var(--rule); border-radius: 2px; margin: 0 auto 8px;`
  - [ ] Ensure `prefers-reduced-motion` already covers `.drawer { transition: none !important; }` (it does — line 307 — verify it still applies after the new CSS)
  - [ ] Verify touch events pass through to MapLibre: `pointer-events: none` on closed drawers (already present via `opacity:0` + no pointer-events — confirm mobile behavior)

- [ ] **Task 4** — Loader and count text (AC5)
  - [ ] Verify `.loader` renders cleanly on 375px width (spot-check in DevTools)
  - [ ] `#results-count` inside `.seg` — if labels are hidden, verify count still shows
  - [ ] No new CSS needed unless visual regression is found

- [ ] **Task 5** — Suppress "Claim this pin" CTA on mobile; add whisper text (AC4b)
  - [ ] In `renderDetail()` (`app.js`), wrap the CTA block (Story 2.2 AC2) in a `window.innerWidth < 768` check
  - [ ] When mobile: render `<div class="wf-label" style="padding: 8px 16px;">Visit on desktop to register this space.</div>` in its place
  - [ ] When desktop: render CTA as before — no regression on Story 2.2

- [ ] **Task 6** — "📍 Near me" button (AC5b)
  - [ ] Add `<button class="chip-btn" id="btn-nearme" title="Near me">📍</button>` to the topbar HTML in `maps-of-making.html` (after the `.seg` group)
  - [ ] In `app.js` init: `$('#btn-nearme').addEventListener('click', () => { navigator.geolocation.getCurrentPosition(pos => { map.flyTo({ center: [pos.coords.longitude, pos.coords.latitude], zoom: 12 }); }, () => {} /* silent deny */); });`
  - [ ] CSS: on mobile hide the text label if any; ensure button fits in collapsed topbar row
  - [ ] No filter dimming required — flyTo is sufficient for this story

- [ ] **Task 7** — "⎘ Copy space link" in detail drawer (AC8b)
  - [ ] In `renderDetail()`, above the existing embed button, insert a "Copy space link" button
  - [ ] URL priority: `s.website || s.endpoint_url` — hide button if both empty
  - [ ] On click: `navigator.clipboard.writeText(url).then(() => { btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = '⎘ Copy space link', 1500); })`
  - [ ] Use existing `.btn` CSS class — no new styles
  - [ ] Verify button appears for both seeded (has `s.website` from VOW profile) and confirmed spaces

- [ ] **Task 8** — Smoke-test desktop regression (AC6)
  - [ ] Load on 1280px viewport — verify left/right drawer positions, topbar full labels, CTA visible for seeded spaces, no layout change

- [ ] **Task 9** — Real-phone acceptance (AC7)
  - [ ] Nicolas opens the page on his phone
  - [ ] Confirms: pan, zoom, Filters drawer, pin tap → detail drawer (no CTA for seeded spaces), "📍" button flies to location, "Copy space link" copies to clipboard, Add your URL drawer opens
  - [ ] Story NOT marked done until this step passes on hardware

---

## Dev Notes

### Current CSS — what already exists and what gaps remain

**What already works (do not change):**
- `@media (max-width: 720px)` at `maps-of-making.html:297–303`: already widens `.drawer.left` and `.drawer.right` to full viewport width and adjusts `.drawer.bottom` and `.tweaks`. This is a partial start — but drawers remain side-positioned (off-screen left/right), not bottom sheets.
- `@media (prefers-reduced-motion: reduce)` at `maps-of-making.html:306–309`: already covers all drawers — keep as-is; just extend the selector to include any new mobile-specific transitions.
- `.drawer.bottom` already exists as a class: `maps-of-making.html:92–94` — `left: 50%; bottom: 14px; transform: translate(-50%, ...)`. On mobile this is the correct anchor but needs width 100% and border-radius.
- `pointer-events: none` on closed drawers: already done via `opacity: 0` + no pointer-events on `.drawer` base rule.

**What is missing (this story adds):**
- Bottom sheet positioning for `.drawer.left` and `.drawer.right` on mobile — they currently slide in from sides even at 720px, which is unusable on 375px phones.
- Drag handle visual affordance on bottom sheets.
- Topbar label collapse — currently `flex-wrap: wrap` is NOT set on `.topbar` (line 51 shows `flex-wrap: wrap` IS set — this causes wrapping), but buttons use `white-space: nowrap` so they don't word-wrap internally. The issue is the `flex-wrap: wrap` on `.topbar` itself — at narrow widths the second `.seg` wraps below the first row and covers the map.

**Topbar HTML structure** (relevant to Task 1):
```html
<header class="topbar">              <!-- position:absolute; flex-wrap:wrap -->
  <div class="brand">…</div>         <!-- logo, flex-shrink:0 -->
  <div class="seg">                  <!-- Filters | Search | Preset & embed | Add your URL -->
    <button id="btn-filters">▤ Filters …</button>
    <button id="btn-search">⌕ Search</button>
    <button id="btn-preset">⎘ Preset & embed</button>
    <button id="btn-addurl">＋ Add your URL</button>
  </div>
  <div class="spacer"></div>
  <button class="chip-btn" id="btn-tweaks">⚙ Tweaks</button>
</header>
```

Recommended mobile approach (minimal JS):
```css
@media (max-width: 767px) {
  .topbar { flex-wrap: nowrap; overflow-x: auto; gap: 6px; }
  .seg button { padding: 8px; }
  .seg button .label { display: none; }  /* add class="label" to text spans if needed */
  .chip-btn .label { display: none; }
}
```
Alternative — icon-only: add `<span class="label">Filters</span>` wrapping text in each button, hide `.label` in mobile. But inspect whether just shrinking padding is enough first.

**`#map` height gap — investigation needed:**

`#map` is `position: absolute; inset: 0` (verify in HTML — it may just be width/height 100%). On iOS Safari `100vh` includes the browser chrome (address bar) height which causes overflow. Use `height: 100dvh` if supported, or the JS window.innerHeight approach. Check current `#map` CSS rule at `maps-of-making.html:~345`.

**Drawer `setDrawer()` — no JS changes needed:**

`setDrawer(name)` at `app.js:759` simply toggles `.open` class. The CSS media query handles the visual difference — no JS branching needed. The same `setDrawer('addurl')` call opens the addurl drawer as a side panel on desktop and as a bottom sheet on mobile purely via CSS.

**bot-drawer — separate element, check separately:**

`.bot-drawer` at `maps-of-making.html:245` is `position: absolute; right: 14px; bottom: 14px` — on mobile this may cover too much of the screen. Consider full-width bottom sheet treatment for it too within the same media query.

### Bottom sheet drag handle — preferred implementation

Add as a CSS `::before` pseudo-element on `.drawer-head` within the media query:
```css
@media (max-width: 767px) {
  .drawer-head::before {
    content: '';
    display: block;
    width: 40px;
    height: 4px;
    background: var(--rule);
    border-radius: 2px;
    margin: 0 auto 8px;
  }
}
```
No HTML changes needed. No swipe-to-dismiss JS — just the visual handle. If swipe dismiss is desired later, that's Epic 5 polish.

### MapLibre touch handling — no changes needed

MapLibre handles touch natively. The risk is a CSS overlay with `pointer-events: auto` blocking the map canvas. Currently `.topbar` and `.drawer` elements are `pointer-events: none` when closed. Verify on real device that no overlay remains touch-blocking after drawers close.

### Viewport units — iOS Safari note

Use `height: 100dvh` (dynamic viewport height) for the map. `100vh` on iOS Safari includes the browser toolbar height, causing a gap or overflow. `dvh` is supported in iOS 15.4+ (Safari 15.4). If `dvh` is unavailable, fall back to `100vh`. Check if `#map` already uses `position: absolute; inset: 0` (which fills the parent body) — if body is `height: 100vh`, same issue applies.

### No JS framework — CSS-only approach

Per epics spec: "Do NOT add a JS framework for this — vanilla CSS media queries and minimal JS." All layout changes go in `<style>` in `maps-of-making.html`. If a JS measurement is needed for topbar height, one `addEventListener('resize', ...)` in `app.js` is acceptable.

### "Claim this pin" CTA suppression — JS pattern (AC4b)

In `renderDetail()` (`app.js`), the CTA block added by Story 2.2 AC2 should be conditionally rendered:

```js
if (s.status === 'seeded') {
  if (window.innerWidth >= 768) {
    // desktop: full CTA (Story 2.2 AC2 — unchanged)
    body.appendChild(/* existing CTA block */);
  } else {
    // mobile: whisper text only
    body.appendChild(el('div', { class: 'wf-label', style: { padding: '8px 16px' } },
      ['Visit on desktop to register this space.']));
  }
}
```

No `resize` listener needed — drawer re-renders on each open, so viewport width is checked fresh each time.

### "📍 Near me" geolocation (AC5b)

```js
$('#btn-nearme').addEventListener('click', () => {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    pos => map.flyTo({ center: [pos.coords.longitude, pos.coords.latitude], zoom: 12 }),
    () => {} // silent denial — no error UI
  );
});
```

`getCurrentPosition` triggers the browser permission prompt on first call. If previously denied, the callback fires with an error immediately — silent fallback is correct here. No retry, no persistent state.

### "⎘ Copy space link" — clipboard pattern (AC8b)

```js
const url = s.website || s.endpoint_url || '';
if (url) {
  const copyBtn = el('button', { class: 'btn' }, ['⎘ Copy space link']);
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(url).then(() => {
      copyBtn.textContent = 'Copied!';
      setTimeout(() => { copyBtn.textContent = '⎘ Copy space link'; }, 1500);
    });
  });
  body.appendChild(copyBtn);
}
```

`navigator.clipboard` requires HTTPS (already the case in prod; localhost also works). No fallback needed for `execCommand` — if clipboard API unavailable, button simply does nothing. `s.website` for VOW spaces is the VOW profile URL already in the GeoJSON; `s.endpoint_url` for confirmed spaces is the coordinator's JSON-LD endpoint — the website is more useful to share, so prefer it.

### Files touched

```
web/
  maps-of-making.html   ← CSS changes (media queries, drag handle, near-me button HTML)
  app.js                ← renderDetail() amendments (CTA suppression, copy button);
                           topbar wiring for #btn-nearme; optional resize listener
```

No backend changes. No nginx changes. No Python changes. No new dependencies.

### References

- Existing media query: `maps-of-making.html:297–303`
- `prefers-reduced-motion`: `maps-of-making.html:306–309`
- `.topbar` CSS: `maps-of-making.html:50–64`
- `.drawer` base + variants: `maps-of-making.html:84–94`
- `.bot-drawer`: `maps-of-making.html:245–248`
- `setDrawer()`: `web/app.js:759–794`
- Story 2.6 epics spec: `_bmad-output/planning-artifacts/epics.md` — "Story 2.6: Mobile Responsive Layout"
- Deferred work log: `_bmad-output/implementation-artifacts/deferred-work.md` (no mobile items currently deferred — clean slate)

---

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (story creation, 2026-04-27)

### Debug Log References

### Completion Notes List

### File List
