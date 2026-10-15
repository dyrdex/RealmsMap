"""Miden'nir rooms on the painted Miden'nir (owner's save of Oct 15, 18:41Z: md_layout_final.json; editor tools/midennir_editor/). The painting stays.
Owner's notes (Oct 15):
  - the Forest terrain rooms (except 1051), the 'Stuck in the Brambles' rooms 3417-3422, and 1030 + 1031 (the inn; a graphic will replace them later):
    a faint dashed line only, subtle, semi-transparent and slightly wavy, like a trail marking on an old map (`w.mdfaint`)
  - 1060 Gazing Upon Mount Doom (and its link up to 679, the Southern Mountain room beside it), 1049, 1050, 1051 and the spacers 22569, 22568, 22564:
    a regular pathway (appended to `w.fwtracks`, drawn like the Forgotten Woods' trails)
Decided here: a link between a pathway room and a faint room is faint (the faint rooms' connections are faint); the old fading path from the bridge into
the forest (`midlink`'s second piece, (0,15.2)->(0,16.6)) is replaced by the pathway 22568 -> 22564; the bridge room 1028 stays as the bridge."""
import math, json, os
import ashen_forest as AF

FAINT_EXTRA = {3417, 3418, 3419, 3420, 3421, 3422, 1030, 1031}
PATHWAY = {1060, 1049, 1050, 1051, 22569, 22568, 22564}
EXCEPT = {1051}
BRIDGE = 1028
WAVE_AMP, WAVE_LEN = 0.06, 0.7                                       # the faint lines' gentle wobble (rooms)


def wavy(a, b):
    """points along a -> b with a small sideways sine wobble (ends fixed)"""
    L = math.dist(a, b)
    if L < 1e-6: return [list(a), list(b)]
    n = max(4, int(L / 0.12)); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; px, py = -uy, ux
    k = max(1, round(L / WAVE_LEN)); ph = (a[0] * 1.7 + a[1] * 2.3) % (2 * math.pi)
    out = []
    for i in range(n + 1):
        t = i / n; s = WAVE_AMP * math.sin(math.pi * t) ** .5 * math.sin(2 * math.pi * k * t + ph)
        out.append([round(a[0] + (b[0] - a[0]) * t + px * s, 3), round(a[1] + (b[1] - a[1]) * t + py * s, 3)])
    return out


def merge_md(w, layout, edges):
    rooms, _ = AF._world()
    info = {r['id']: r for r in edges['rooms']}
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys']))); hid = set(layout['hidden'])
    MD = {v for v, r in info.items() if r.get('area') == 'MD'}
    shown = {v for v in MD if v not in hid}
    faint_rooms = {v for v in shown if rooms[v]['terrain'] == 'Forest' and v not in EXCEPT} | (FAINT_EXTRA & shown)
    assert not faint_rooms & PATHWAY and (PATHWAY - shown) == set(), PATHWAY - shown
    faint, path, skipped = [], [], []
    for a, b, kind in edges['edges']:
        if not ({a, b} & shown) or {a, b} & hid: continue
        if BRIDGE in (a, b): skipped.append((a, b, 'the bridge')); continue
        other = ({a, b} - MD)
        if other and not ({a, b} & (faint_rooms | PATHWAY)): skipped.append((a, b)); continue
        if not (a in pos and b in pos): skipped.append((a, b, 'no position')); continue
        pa, pb = pos[a], pos[b]
        if {a, b} & faint_rooms: faint.append(wavy(pa, pb))
        else: path.append([[round(pa[0], 3), round(pa[1], 3)], [round(pb[0], 3), round(pb[1], 3)]])
    ml = w.get('midlink') or []
    old = [L for L in ml if L[0] == [0.0, 15.2] or L[0] == [0, 15.2]]
    assert len(old) == 1, ml
    w['midlink'] = [L for L in ml if L not in old]
    w['fwtracks'] = list(w['fwtracks']) + path
    w['mdfaint'] = list(w.get('mdfaint', [])) + faint
    return w, dict(shown=len(shown), hidden=len(MD & hid), faint_rooms=len(faint_rooms), faint_lines=len(faint), pathway_lines=len(path), skipped=skipped)
