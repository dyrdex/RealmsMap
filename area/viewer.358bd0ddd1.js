/* Room maps: the shared viewer. AreaViewer.mount(root, {base, svg, rooms, back, onClose})
   base: folder of the area's files; svg / rooms: their file names; back: link to the realm map (standalone page);
   onClose: close button instead (when shown over the world map). Pan: drag; zoom: wheel, pinch, buttons. */
(function () {
'use strict';
const KEY = [["room", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--node)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Room</span>"], ["mob", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--mob)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Room with a mob</span>"], ["entry", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--entry)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Area entrance from world map</span>"], ["item", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--sign)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Something to find (an item, a sign)</span>"], ["shop", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"10.2\" fill=\"none\" stroke=\"var(--shop)\" stroke-width=\"2.2\"/><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--node)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Shop: what it sells is on the room card</span>"], ["recall", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"10.2\" fill=\"none\" stroke=\"var(--recall)\" stroke-width=\"2.2\"/><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--node)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Recall point (where recall to the guild sets you down)</span>"], ["vert", "<svg viewBox=\"0 0 30 22\"><line x1=\"0\" y1=\"11\" x2=\"30\" y2=\"11\" stroke=\"var(--line)\" stroke-width=\"5\"/><circle cx=\"22\" cy=\"11\" r=\"9.5\" fill=\"none\" stroke=\"var(--line)\" stroke-width=\"1.5\"/><circle cx=\"22\" cy=\"11\" r=\"7\" fill=\"var(--node)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Bold line: up or down. Double ring: the lower room</span>"], ["jump", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"8\" fill=\"var(--paper)\" stroke=\"var(--line)\" stroke-width=\"1.6\"/><text x=\"15\" y=\"14.5\" text-anchor=\"middle\" font-size=\"10\" font-weight=\"700\" fill=\"var(--line)\" font-family=\"var(--serif)\">A</text></svg><span>Exit too long for a line: the two matching letters join</span>"], ["door", "<svg viewBox=\"0 0 30 22\"><line x1=\"0\" y1=\"11\" x2=\"30\" y2=\"11\" stroke=\"var(--line)\" stroke-width=\"2\"/><line x1=\"15\" y1=\"5\" x2=\"15\" y2=\"17\" stroke=\"var(--line)\" stroke-width=\"2\"/></svg><span>Door (open it first)</span>"], ["area", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--paper)\" stroke=\"var(--area)\" stroke-width=\"1.6\" stroke-dasharray=\"3 3\"/></svg><span>Leads to another area</span>"], ["plane", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--paper)\" stroke=\"var(--plane)\" stroke-width=\"1.6\" stroke-dasharray=\"3 3\"/></svg><span>Leads to a holy place or another plane</span>"], ["shared", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--mob)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/><text x=\"15\" y=\"14.5\" text-anchor=\"middle\" font-size=\"10\" font-weight=\"700\" fill=\"var(--mob-ink)\" font-family=\"var(--serif)\">1</text></svg><span>Same mob in several rooms, named once</span>"], ["oneway", "<svg viewBox=\"0 0 30 22\"><line x1=\"0\" y1=\"11\" x2=\"26\" y2=\"11\" stroke=\"var(--line)\" stroke-width=\"2\"/><path d=\"M19,6 L26,11 L19,16\" fill=\"none\" stroke=\"var(--line)\" stroke-width=\"2\"/></svg><span>One way only</span>"], ["bent", "<svg viewBox=\"0 0 30 22\"><line x1=\"0\" y1=\"16\" x2=\"30\" y2=\"16\" stroke=\"var(--line)\" stroke-width=\"2\"/><text x=\"15\" y=\"11\" text-anchor=\"middle\" font-size=\"11\" font-style=\"italic\" font-weight=\"600\" fill=\"var(--pick)\" font-family=\"var(--serif)\">s</text></svg><span>Line not drawn in its real direction: the tag gives it</span>"], ["wrap", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"8\" fill=\"var(--paper)\" stroke=\"var(--wrap)\" stroke-width=\"1.6\" stroke-dasharray=\"3 2\"/><text x=\"15\" y=\"14.5\" text-anchor=\"middle\" font-size=\"10\" fill=\"var(--wrap)\" font-family=\"var(--serif)\">5</text></svg><span>Maze exit: leads to the room with this number</span>"], ["house", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--paper)\" stroke=\"var(--area)\" stroke-width=\"1.6\" stroke-dasharray=\"3 3\"/></svg><span>Private house or apartment</span>"], ["danger", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--danger)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/><path d=\"M11.5,7.5 L18.5,14.5 M18.5,7.5 L11.5,14.5\" stroke=\"var(--danger-x)\" stroke-width=\"2\"/></svg><span>Deathtrap</span>"], ["holy", "<svg viewBox=\"0 0 30 22\"><circle cx=\"15\" cy=\"11\" r=\"7\" fill=\"var(--plane)\" stroke=\"var(--node-line)\" stroke-width=\"1.5\"/></svg><span>Holy place</span>"], ["dnum", "<svg viewBox=\"0 0 30 22\"><text x=\"15\" y=\"15\" text-anchor=\"middle\" font-size=\"10\" font-style=\"italic\" fill=\"var(--ink)\" font-family=\"var(--serif)\">dnum</text></svg><span>dnum: Dyrdex's Room Vnum</span>"]];
const sortName = n => String(n).replace(/^the\s+/i, '');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

async function mount(root, o) {
  const review = new URLSearchParams(location.search).has('review');
  root.classList.add('av');
  root.innerHTML = '<div class="av-bar"><h1></h1>' +
    '<button class="av-btn av-areas-btn" type="button" data-act="areas" aria-expanded="false" aria-controls="av-areas">Areas</button>' +
    '<div class="av-find" role="search"><input class="av-q" type="search" placeholder="Search this area" aria-label="Search this area: room names, terrain, mobs, items, room numbers" autocomplete="off" spellcheck="false"></div>' +
    '<button class="av-btn av-leg" type="button" data-act="legend" aria-expanded="false" aria-controls="av-legend">Map Legend</button>' +
    (o.onClose ? '<button class="av-btn" type="button" data-act="close">Back to World Map</button>'
               : '<a class="av-btn av-back" href="' + esc(o.back || '../../') + '">Back to World Map</a>') +
    '</div><div class="av-stage av-map"><div class="av-sheet"></div><div class="av-pin" hidden aria-hidden="true"><svg viewBox="-20 -46 40 64"><circle class="av-pin-ring" r="15"/><g class="av-pin-drop">' +
    '<ellipse class="av-pin-shadow" cx="5" cy="1" rx="7" ry="2.6"/><path class="av-pin-body" d="M0,0 C-4,-12 -11,-16.4 -11,-23 A11,11 0 1,1 11,-23 C11,-16.4 4,-12 0,0Z"/>' +
    '<circle class="av-pin-eye" cy="-23" r="4"/></g></svg></div><div class="av-hits" hidden></div><div class="av-areas" id="av-areas" hidden><input class="av-aq" type="search" placeholder="Find an area" aria-label="Find an area" autocomplete="off" spellcheck="false"><p class="av-hn"></p><ul></ul></div><div class="av-legend" id="av-legend" hidden><h2>Map Legend</h2><div class="av-key"></div></div><div class="av-msg">Loading the room map…</div>' +
    '<div class="av-zoom"><button class="av-btn" type="button" data-act="in" aria-label="Zoom in">+</button>' +
    '<button class="av-btn" type="button" data-act="out" aria-label="Zoom out">−</button>' +
    '<button class="av-btn" type="button" data-act="fit" aria-label="Show the whole area">⤢</button></div>' +
    '<aside class="av-side"><button class="av-grip" type="button" data-act="sheet" aria-label="Show or hide the room"></button>' +
    '<button class="av-x" type="button" data-act="unpick" aria-label="Close the room card">×</button>' +
    '<div class="av-in"><div class="av-room"></div>' +
    '<details class="av-checkbox" hidden><summary>To check</summary><ul class="av-check"></ul></details>' +
    '<p class="av-dnum"></p></div></aside></div>';
  const $ = q => root.querySelector(q), stage = $('.av-stage'), sheet = $('.av-sheet'), panel = $('.av-side'), side = $('.av-room');
  let svgText, R;
  try {
    [svgText, R] = await Promise.all([fetch(o.base + o.svg).then(r => { if (!r.ok) throw r.status; return r.text(); }),
                                      fetch(o.base + o.rooms).then(r => { if (!r.ok) throw r.status; return r.json(); })]);
  } catch (e) { $('.av-msg').textContent = 'The room map could not be loaded. Reload the page to try again.'; return; }
  // links to other areas (owner, Nov 3): the room-map list says which area's map has the room a link leads to
  const elsewhere = {};                              // room -> [slug, area name]
  let areaList = [];                                 // the Areas menu: [slug, entry] for every room map
  const linkTo = v => elsewhere[v] ? '../' + elsewhere[v][0] + '/#' + v : null;
  const openLink = v => { const e = elsewhere[v]; if (!e) return;
    if (o.openArea) o.openArea(e[0], v); else location.href = linkTo(v); };
  const indexReady = fetch(o.index || (o.base + '../index.json'), {cache: 'no-cache'})   // fresh: new areas' links work at once
   .then(r => r.ok ? r.json() : null).then(ix => {
    if (!ix || !ix.areas) return;
    areaList = Object.entries(ix.areas).sort((a, b) => sortName(a[1].name).localeCompare(sortName(b[1].name)));
    for (const [slug, a] of Object.entries(ix.areas)) if (a.name !== R.name) for (const v of a.rooms || []) if (!elsewhere[v]) elsewhere[v] = [slug, a.name];
  }).catch(() => {});
  $('.av-msg').remove();
  $('h1').textContent = R.name;
  // back to the world map with this area selected there (owner, Nov 2): the world page reads #place=<name>
  if (!o.onClose) $('.av-back').href = (o.back || '../../') + '#place=' + encodeURIComponent(R.place || R.name);
  if (!o.onClose) document.title = R.name + ' · Room map';
  sheet.innerHTML = svgText;
  const svg = sheet.querySelector('svg'); svg.removeAttribute('width'); svg.removeAttribute('height');
  sheet.style.width = R.w + 'px'; sheet.style.height = R.h + 'px';
  $('.av-key').innerHTML = KEY.filter(k => R.have.includes(k[0])).map(k => k[1]).join('');
  if (review && R.check.length) {
    $('.av-checkbox').hidden = false; $('.av-checkbox').open = true;
    $('.av-check').innerHTML = R.check.map(c => '<li><b>' + esc(c[0]) + '</b> ' + esc(c[1]) + '</li>').join('');
  }

  // ---- view: the map sheet moves as one picture (CSS transform; the browser redraws it sharp when a gesture ends)
  const W = R.w, H = R.h, U = R.u, PAD = 24;
  const phone = () => matchMedia('(max-width:760px)').matches;
  let V = null, idle = 0;
  const size = () => { const r = stage.getBoundingClientRect(); return [Math.max(r.width, 1), Math.max(r.height, 1)]; };
  // the part of the stage not covered by the room panel
  const room = () => { const [sw, sh] = size(); if (panel.hidden) return [0, 0, sw, sh]; if (phone()) return [0, 0, sw, sh - 84];
    const p = panel.getBoundingClientRect(), r = stage.getBoundingClientRect(); return [0, 0, Math.max(sw / 2, p.left - r.left - 8), sh]; };
  // the map pin on the selected room: outside the sheet, so it keeps its size at any zoom
  const pin = $('.av-pin'), pinRing = $('.av-pin-ring'), dotR = +(svg.querySelector('.node .dot') || {getAttribute: () => 8}).getAttribute('r');
  let pinAt = null;
  const placePin = () => { if (!pinAt) return;
    pin.style.transform = 'translate(' + (V.x + pinAt[0] * V.k) + 'px,' + (V.y + pinAt[1] * V.k) + 'px)';
    pinRing.setAttribute('r', Math.max(14, dotR * V.k + 5).toFixed(1)); };
  const apply = () => {
    sheet.style.transform = 'translate(' + V.x + 'px,' + V.y + 'px) scale(' + V.k + ')'; placePin();
    sheet.classList.add('moving'); clearTimeout(idle); idle = setTimeout(() => sheet.classList.remove('moving'), 160);
  };
  const kmin = () => { const [, , w, h] = room(); return Math.min((w - 2 * PAD) / W, (h - 2 * PAD) / H) * .6; };
  const kmax = () => { const [sw] = size(); return Math.max(sw / (U * 4), kmin() * 2); };
  function fit() {
    const [x0, y0, w, h] = room(), k = Math.min((w - 2 * PAD) / W, (h - 2 * PAD) / H);
    V = {k, x: x0 + (w - W * k) / 2, y: y0 + (h - H * k) / 2}; apply();
  }
  function zoomAt(f, px, py) {
    const k = Math.min(kmax(), Math.max(kmin(), V.k * f)); f = k / V.k;
    V.x = px - (px - V.x) * f; V.y = py - (py - V.y) * f; V.k = k; apply();
  }
  function centerOn(x, y, cells) {
    const [x0, y0, w, h] = room();
    if (cells) V.k = Math.min(kmax(), Math.max(kmin(), w / (U * cells)));
    V.x = x0 + w / 2 - x * V.k; V.y = y0 + h / 2 - y * V.k; apply();
  }
  fit();
  let last = size();
  new ResizeObserver(() => { if (!V) return; const now = size();
    V.x += (now[0] - last[0]) / 2; V.y += (now[1] - last[1]) / 2; last = now; apply(); }).observe(stage);
  stage.addEventListener('wheel', e => { if (e.target.closest('.av-side, .av-hits, .av-legend, .av-areas')) return; e.preventDefault(); const r = stage.getBoundingClientRect();
    zoomAt(Math.exp(-e.deltaY * (e.deltaMode ? 0.05 : 0.0015)), e.clientX - r.left, e.clientY - r.top); }, {passive: false});
  const pts = new Map(); let moved = false, two = null;
  stage.addEventListener('pointerdown', e => {
    if (e.target.closest('.av-zoom, .av-side, .av-hits, .av-legend, .av-areas')) return;
    pts.set(e.pointerId, [e.clientX, e.clientY]); if (pts.size === 1) moved = false; two = null;
  });
  stage.addEventListener('pointermove', e => {
    if (!pts.has(e.pointerId)) return;
    const prev = pts.get(e.pointerId), r = stage.getBoundingClientRect();
    if (pts.size === 1) {
      const dx = e.clientX - prev[0], dy = e.clientY - prev[1];
      if (!moved && Math.hypot(dx, dy) < 5) return;
      if (!moved) { moved = true; stage.classList.add('drag'); try { stage.setPointerCapture(e.pointerId); } catch (_) {} }
      V.x += dx; V.y += dy; apply();
    } else if (pts.size === 2) {
      pts.set(e.pointerId, [e.clientX, e.clientY]);
      const [a, b] = [...pts.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      const cx = (a[0] + b[0]) / 2 - r.left, cy = (a[1] + b[1]) / 2 - r.top;
      if (two) { V.x += cx - two.cx; V.y += cy - two.cy; zoomAt(d / two.d, cx, cy); }
      two = {d, cx, cy}; moved = true; return;
    }
    pts.set(e.pointerId, [e.clientX, e.clientY]);
  });
  const up = e => { pts.delete(e.pointerId); two = null; if (!pts.size) stage.classList.remove('drag'); };
  stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
  // phones: the room panel is a bottom sheet (tap or swipe the handle)
  let gy = null;
  $('.av-grip').addEventListener('pointerdown', e => { gy = e.clientY; });
  $('.av-grip').addEventListener('pointerup', e => { if (gy === null) return; const dy = e.clientY - gy; gy = null;
    if (Math.abs(dy) > 20) panel.classList.toggle('closed', dy > 0); else panel.classList.toggle('closed'); });
  if (phone()) panel.classList.add('closed');

  // ---- rooms
  const nodeOf = v => svg.querySelector('.node[data-v="' + v + '"]');
  function where(v) { const c = nodeOf(v).querySelector('.dot'); return [+c.getAttribute('cx'), +c.getAttribute('cy')]; }
  let opened = false;                        // the first room shown does not open the phone sheet
  let jumpLine = null;
  const clearJump = () => { if (jumpLine) { jumpLine.remove(); jumpLine = null; } };
  function jump(from, to) {
    show(to);
    const [x0, y0] = where(from), [x1, y1] = where(to), dx = x1 - x0, dy = y1 - y0, d = Math.hypot(dx, dy) || 1;
    const bend = Math.min(.22 * d, 3 * U), cx = (x0 + x1) / 2 - dy / d * bend, cy = (y0 + y1) / 2 + dx / d * bend;
    const ex = x1 - (x1 - cx) / Math.hypot(x1 - cx, y1 - cy) * (U * .28), ey = y1 - (y1 - cy) / Math.hypot(x1 - cx, y1 - cy) * (U * .28);
    const ux = (ex - cx) / Math.hypot(ex - cx, ey - cy), uy = (ey - cy) / Math.hypot(ex - cx, ey - cy), h = U * .22;
    jumpLine = document.createElementNS('http://www.w3.org/2000/svg', 'g'); jumpLine.setAttribute('class', 'av-jumpline');
    jumpLine.innerHTML = '<path class="arc" d="M' + x0 + ',' + y0 + ' Q' + cx + ',' + cy + ' ' + ex + ',' + ey + '"/>' +
      '<path class="head" d="M' + (ex - ux * h + uy * h * .55) + ',' + (ey - uy * h - ux * h * .55) + ' L' + ex + ',' + ey +
      ' L' + (ex - ux * h - uy * h * .55) + ',' + (ey - uy * h + ux * h * .55) + '"/>' +
      '<circle class="from" cx="' + x0 + '" cy="' + y0 + '" r="' + (U * .3) + '"/>';
    svg.querySelector('.nodes').before(jumpLine);
    // show both ends: zoom out only as far as needed (never closer than now or the whole-area view)
    const [rx, ry, w, h2] = room(), pad = U * 1.5, bw = Math.abs(dx) + 2 * pad, bh = Math.abs(dy) + 2 * pad;
    const kf = Math.min((w - 2 * PAD) / W, (h2 - 2 * PAD) / H);
    V.k = Math.max(kmin(), Math.min(w / bw, h2 / bh, Math.max(V.k, kf)));
    V.x = rx + w / 2 - (x0 + x1) / 2 * V.k; V.y = ry + h2 / 2 - (y0 + y1) / 2 * V.k; apply();
  }
  function show(v, center) {
    const r = R.rooms[v]; if (!r) return;
    clearJump();
    svg.querySelectorAll('.node.sel').forEach(n => n.classList.remove('sel'));
    nodeOf(v).classList.add('sel');
    pinAt = where(v); pin.hidden = false; placePin();
    pin.classList.remove('drop'); void pin.offsetWidth; pin.classList.add('drop');
    let h = '<h2>' + esc(r.n) + '</h2>';
    const sub = [r.t ? esc(r.t) : '', r.o ? 'lower room' : ''].filter(Boolean).join(' · ');
    if (sub) h += '<p class="sub">' + sub + '</p>';
    if (r.w && r.w.length) h += r.w.map(t => '<p class="av-sub av-wayin">' + esc(t) + '</p>').join('');   // one-way ways in from outside (owner, Nov 3)
    if (r.note) h += '<p class="av-note">' + esc(r.note) + '</p>';     // the room's note from the TinTin map
    // mobs and items: name (Level N), and a sub-line for a note such as 'Area Pop' (owner, Nov 3)
    if (r.m.length) h += '<h3>Mobs and items</h3><ul class="av-mobs">' + r.m.map((m, i) => { const [lv, nt] = (r.mi && r.mi[i]) || ['', ''];
      return '<li><span class="av-mob">' + esc(m) + (lv !== '' && lv != null ? ' <span class="av-lvl">(Level ' + esc(lv) + ')</span>' : '') + '</span>' +
        (nt ? '<span class="av-sub">' + esc(nt) + '</span>' : '') + '</li>'; }).join('') + '</ul>';
    // the shop's list, exactly as the owner gave it; a line too long for the card wraps under the item names
    if (r.shop) h += '<h3>For sale</h3><div class="av-shop">' + r.shop.split('\n').map(l => '<span class="ln">' + (esc(l) || '&nbsp;') + '</span>').join('') + '</div>';
    h += '<h3>Exits</h3><ul class="av-exits">' + r.x.map(e => {
      // direction | room it leads to, with one sub-line for anything special: door, the commands to type (owner, Nov 3)
      const sub = [e[2] ? 'door' : '', e[5] || ''].filter(Boolean).join(' · ');
      return '<li><span class="av-dir">' + esc(e[0]) + '</span><span class="av-to">' +
        (e[3] ? '<button class="av-go" type="button" data-go="' + e[4] + '">' + esc(e[1]) + '</button>'
             : e[6] && linkTo(e[6]) ? '<a class="av-go av-ext" href="' + esc(linkTo(e[6])) + '" data-out="' + e[6] + '">' + esc(e[1]) + '</a>'
             : '<span class="av-ext">' + esc(e[1]) + '</span>') +
        (sub ? '<span class="av-sub">' + esc(sub) + '</span>' : '') + '</span></li>';
    }).join('') + '</ul>';
    if (review && r.u) h += '<p class="av-warn">To check: ' + esc(r.u) + '</p>';
    side.innerHTML = h; $('.av-dnum').textContent = r.mz ? '' : 'dnum: ' + v;   // a maze card has no dnum (owner, Nov 6)
    $('.av-in').scrollTop = 0;
    panel.hidden = false;
    if (o.open !== false && opened) panel.classList.remove('closed');
    if (center) { const [x, y] = where(v); centerOn(x, y, center === true ? null : center); }
    if (!o.onClose) try { history.replaceState(null, '', '#' + v); } catch (_) {}
  }
  stage.addEventListener('click', e => {
    if (moved) return;
    const out = e.target.closest('.stub.live, .stublbl.live');
    if (out) { openLink(out.dataset.to); return; }
    const n = e.target.closest('.node, .call, .jump');
    if (!n) return;
    if (n.classList.contains('jump')) jump(n.dataset.from, n.dataset.to); else show(n.dataset.v);
  });
  stage.addEventListener('keydown', e => { const n = e.target.closest('.node');
    if (n && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); show(n.dataset.v); } });
  root.addEventListener('click', e => {
    const ln = e.target.closest('a[data-out]');
    if (ln && o.openArea) { e.preventDefault(); openLink(ln.dataset.out); return; }    // inside the world page: let it open the map
    const b = e.target.closest('[data-act], [data-go]'); if (!b) return;
    if (b.dataset.go) return show(b.dataset.go, true);
    const [sw, sh] = size();
    if (b.dataset.act === 'sheet') return;
    if (b.dataset.act === 'legend') { const L = $('.av-legend'); L.hidden = !L.hidden; b.setAttribute('aria-expanded', String(!L.hidden)); if (!L.hidden) areasOpen(false); return; }
    if (b.dataset.act === 'areas') { areasOpen(AP.hidden); return; }
    if (b.dataset.act === 'unpick') {                     // close the card: no room selected
      panel.hidden = true; svg.querySelectorAll('.node.sel').forEach(n => n.classList.remove('sel')); pin.hidden = true; pinAt = null; clearJump();
      if (!o.onClose) try { history.replaceState(null, '', location.pathname + location.search); } catch (_) {}
      return;
    }
    if (b.dataset.act === 'in') zoomAt(1.5, sw / 2, sh / 2);
    else if (b.dataset.act === 'out') zoomAt(1 / 1.5, sw / 2, sh / 2);
    else if (b.dataset.act === 'fit') fit();
    else if (b.dataset.act === 'close' && o.onClose) o.onClose();
  });
  const start = (!o.onClose && R.rooms[location.hash.slice(1)]) ? location.hash.slice(1) : (o.room && R.rooms[o.room] ? o.room : null);
  // ---- area search: every word must appear in the room's name, terrain, mobs and items, room number or exits to other areas
  const q = $('.av-q'), hits = $('.av-hits');
  const norm = t => String(t).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const fields = v => { const r = R.rooms[v];
    return [['name', r.n], ['terrain', r.t], ...r.m.map(m => ['here', m]), ['dnum', r.mz ? '' : 'dnum ' + v], ['note', r.note], ['shop', r.shop], ...r.x.filter(e => e[5]).map(e => ['cmd', e[0] + ': ' + e[5]]),
            ...r.x.filter(e => !e[3]).map(e => ['exit', e[0] + ' to ' + e[1]])].filter(f => f[1]); };
  const rx = w => new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
  const mark = (t, words) => { let h = esc(t); for (const w of words) h = h.replace(rx(esc(w)), '<mark>$1</mark>'); return h; };
  let found = [], cur = -1;
  function search() {
    const words = norm(q.value).split(/\s+/).filter(Boolean);
    if (!words.length) { hits.hidden = true; found = []; return; }
    found = Object.keys(R.rooms).filter(v => { const all = norm(fields(v).map(f => f[1]).join(' | ')); return words.every(w => all.includes(w)); })
      .sort((a, b) => R.rooms[a].n.localeCompare(R.rooms[b].n));
    cur = -1;
    const raw = q.value.trim().split(/\s+/);
    hits.innerHTML = '<p class="av-hn">' + (found.length ? found.length + (found.length === 1 ? ' room' : ' rooms') : 'No rooms match') + '</p>' +
      (found.length ? '<ul>' + found.slice(0, 200).map((v, i) => { const r = R.rooms[v];
        const extra = fields(v).filter(f => ['here', 'exit', 'note', 'cmd'].includes(f[0])).filter(f => words.some(w => norm(f[1]).includes(w)));
        return '<li><button type="button" class="av-hit" data-hit="' + v + '" id="av-hit-' + i + '">' +
          '<span class="av-hname">' + mark(r.n, raw) + '</span>' +
          '<span class="av-hsub">' + [r.t ? mark(r.t, raw) : '', ...extra.slice(0, 2).map(f => mark(f[1], raw))].filter(Boolean).join(' · ') + '</span>' +
          (r.mz ? '' : '<span class="av-hnum">dnum: ' + mark(v, raw) + '</span>') + '</button></li>'; }).join('') + '</ul>' : '');
    hits.hidden = false;
  }
  function pickHit(v) { show(v, true); q.blur(); hits.hidden = true; }
  q.addEventListener('input', search);
  q.addEventListener('focus', () => { if (q.value.trim()) search(); });
  q.addEventListener('keydown', e => {
    const n = Math.min(found.length, 200);
    if (e.key === 'Escape') { hits.hidden = true; q.blur(); }
    else if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && n) {
      e.preventDefault(); cur = (cur + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
      hits.querySelectorAll('.av-hit').forEach((b, i) => b.classList.toggle('cur', i === cur));
      hits.querySelector('#av-hit-' + cur).scrollIntoView({block: 'nearest'});
    } else if (e.key === 'Enter' && n) { e.preventDefault(); pickHit(found[cur < 0 ? 0 : cur]); }
  });
  hits.addEventListener('click', e => { const b = e.target.closest('[data-hit]'); if (b) pickHit(b.dataset.hit); });
  document.addEventListener('pointerdown', e => {
    if (!hits.hidden && !e.target.closest('.av-hits, .av-find')) hits.hidden = true;
    const lg = $('.av-legend');
    if (!lg.hidden && !e.target.closest('.av-legend, .av-leg')) { lg.hidden = true; $('.av-leg').setAttribute('aria-expanded', 'false'); }
  });
  root.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('.av-legend').hidden) { $('.av-legend').hidden = true; $('.av-leg').setAttribute('aria-expanded', 'false'); $('.av-leg').focus(); } });

  // ---- Areas menu (owner, Nov 5): every room map, found by name; picking one opens it at its entrance
  const AP = $('.av-areas'), aq = $('.av-aq'), AB = $('.av-areas-btn');
  let aFound = [], aCur = -1;
  function areasOpen(on) {
    AP.hidden = !on; AB.setAttribute('aria-expanded', String(on));
    if (!on) return;
    const L = $('.av-legend'); L.hidden = true; $('.av-leg').setAttribute('aria-expanded', 'false'); hits.hidden = true;
    aq.value = ''; areaFilter(); indexReady.then(areaFilter);
    if (!phone()) aq.focus();
  }
  function areaFilter() {
    const words = norm(aq.value).split(/\s+/).filter(Boolean), raw = aq.value.trim().split(/\s+/).filter(Boolean);
    aFound = areaList.filter(([, a]) => { const t = norm(a.name + ' ' + (a.place || '')); return words.every(w => t.includes(w)); });
    aCur = -1;
    $('.av-areas .av-hn').textContent = !areaList.length ? 'Loading the list of room maps…' : aFound.length ? aFound.length + (aFound.length === 1 ? ' area' : ' areas') : 'No areas match';
    $('.av-areas ul').innerHTML = aFound.map(([slug, a], i) => { const here = a.name === R.name;
      return '<li><button type="button" class="av-hit' + (here ? ' here' : '') + '" data-area="' + esc(slug) + '" id="av-area-' + i + '"' + (here ? ' aria-current="page"' : '') + '>' +
        '<span class="av-hname">' + mark(a.name, raw) + '</span><span class="av-hnum">' + a.nrooms + ' rooms</span>' +
        '<span class="av-hsub">' + [a.lvl ? 'Level ' + esc(a.lvl) : '', a.place ? 'World map: ' + mark(a.place, raw) : '', here ? 'This map' : ''].filter(Boolean).join(' · ') + '</span></button></li>'; }).join('');
  }
  function openArea(slug) {
    const a = areaList.find(e => e[0] === slug); if (!a) return;
    if (a[1].name === R.name) { areasOpen(false); return; }
    if (o.openArea) { areasOpen(false); o.openArea(slug); } else location.href = (o.base || '') + '../' + slug + '/';
  }
  aq.addEventListener('input', areaFilter);
  aq.addEventListener('keydown', e => {
    const n = aFound.length;
    if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && n) {
      e.preventDefault(); aCur = (aCur + (e.key === 'ArrowDown' ? 1 : -1) + n) % n;
      AP.querySelectorAll('.av-hit').forEach((b, i) => b.classList.toggle('cur', i === aCur));
      AP.querySelector('#av-area-' + aCur).scrollIntoView({block: 'nearest'});
    } else if (e.key === 'Enter' && n) { e.preventDefault(); openArea(aFound[aCur < 0 ? 0 : aCur][0]); }
  });
  AP.addEventListener('click', e => { const b = e.target.closest('[data-area]'); if (b) openArea(b.dataset.area); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !AP.hidden) { areasOpen(false); AB.focus(); } });
  document.addEventListener('pointerdown', e => { if (!AP.hidden && !e.target.closest('.av-areas, .av-areas-btn')) areasOpen(false); });

  show(start || String(R.start));
  indexReady.then(() => {
    svg.querySelectorAll('.stub[data-to], .stublbl[data-to]').forEach(g => { const e = elsewhere[g.dataset.to]; if (!e) return;
      g.classList.add('live'); const t = document.createElementNS('http://www.w3.org/2000/svg', 'title'); t.textContent = 'Open the ' + e[1] + ' room map'; g.appendChild(t); });
    const cur = svg.querySelector('.node.sel'); if (cur) show(cur.dataset.v);
  });
  opened = true;
}
window.AreaViewer = {mount};
})();
