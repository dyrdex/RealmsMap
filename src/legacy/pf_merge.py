"""The Pixie Forest rooms (owner's save of Oct 15, 21:26Z: pf_layout_final.json; editor tools/pixie_forest_editor/). Owner's notes:
  - the Forgotten Woods rooms (4017, 4018, 4019, moved in the editor) are drawn as the usual pathway: the Woods' main trail (`fwtracks[0]`) now bends
    through their new spots, and every place's line through them follows (their `cx` track spots move too, so later tracing uses them)
  - the Pixie Forest / Asgard Nexus rooms needn't really show (the owner packed them very close together): only a very faint trail, fainter than
    Miden'nir's (`w.pffaint`), between the listed rooms and from them to the Woods rooms they open off (4019, 4015)
The saved spots are also given to the route tracers (build.py), so the A'enari and Reomyr Village routes run through these rooms in full."""
import math
from md_merge import wavy

FW = (4017, 4018, 4019)


def merge_pf(w, layout, edges):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys']))); hid = set(layout['hidden'])
    info = {r['id']: r for r in edges['rooms']}
    PF = {v for v, r in info.items() if r.get('area') == 'PF' and r.get('grp') in ('pf', 'an') and v not in hid}
    tr = w['track']; old = {v: tuple(tr['cx%d' % v][:2]) for v in FW}; new = {v: (round(pos[v][0], 3), round(pos[v][1], 3)) for v in FW}
    rep = dict(track=0, place_points=0, trail_points=[], trees=0, tufts=0)
    for v in FW:
        t = list(tr['cx%d' % v]); t[0], t[1] = new[v]; tr['cx%d' % v] = t; rep['track'] += 1
    def swap(L):
        n = 0
        for q in L:
            for v in FW:
                if math.dist(q[:2], old[v]) < 0.05: q[0], q[1] = new[v]; n += 1
        return n
    for p in w['places']:
        rep['place_points'] += swap(p['path'])
        for s in p.get('segs') or []: rep['place_points'] += swap(s)
    T = w['fwtracks'][0]                                                         # the Woods' main trail: its bends at the three rooms (smoothed, < 1 room off)
    for v in FW:
        i = min(range(len(T)), key=lambda i: math.dist(T[i], old[v])); assert math.dist(T[i], old[v]) < 1.0, (v, T[i])
        T[i] = list(new[v]); rep['trail_points'].append(i)
    seg = [T[i] for i in range(min(rep['trail_points']) - 1, min(len(T), max(rep['trail_points']) + 2))]
    def near(q, d):
        for a, b in zip(seg, seg[1:]):
            ax, ay = b[0] - a[0], b[1] - a[1]; L2 = ax * ax + ay * ay or 1e-9
            t = max(0, min(1, ((q[0] - a[0]) * ax + (q[1] - a[1]) * ay) / L2))
            if math.dist(q[:2], (a[0] + t * ax, a[1] + t * ay)) < d: return True
        return False
    for k, d in (('trees', 0.55), ('tufts', 0.4)):                              # the trail's new course: nothing grows on it
        n0 = len(w[k]); w[k] = [q for q in w[k] if not near(q, d)]; rep[k] = n0 - len(w[k])
    at = lambda v: pos[v] if v in pos else (tuple(tr['cx%d' % v][:2]) if ('cx%d' % v) in tr else None)
    faint = []
    for a, b, kind in edges['edges']:
        if not ({a, b} & PF) or {a, b} & hid: continue
        pa, pb = at(a), at(b)
        if pa and pb: faint.append(wavy(pa, pb))
    w['pffaint'] = list(w.get('pffaint', [])) + faint
    rep['faint_lines'] = len(faint); rep['moved'] = {v: (old[v], new[v]) for v in FW}
    return w, rep
