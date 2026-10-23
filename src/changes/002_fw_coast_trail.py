"""Owner, Oct 23 (Barren Peaks + Forgotten Woods editor save of 22:07Z, `legacy/bp_layout_oct23b.json`): the Woods' coast trail dragged towards
the sea: 31 rooms moved (5484-5496, 5629-5632, 5634-5646, 16224; 5496 and 16224, hidden in the save, are not drawn).
  - fwtracks[16] (5484 ... 5495, 5646 ... 5629, 5628) redrawn through the saved spots, room to room (as the editor draws it; slightly
    rounded, as 2.12/001's _soft); fwtracks[14], [15] end on 5484's new spot;
  - fwtracks[384] (the long trail from the Forest of Tears, 1669 to 5491): its last two points replaced by 5491's new spot (the rest kept);
  - the stairway 5639 d 11745 (descents[0]) starts at 5639's new spot (steps redone, as 2.12/001);
  - room_pos / track: the moved rooms; route lines (Tower of Enlightenment, Knights of the Round) follow them;
  - trees, tufts and other sprites within CLEAR of the redrawn lines cleared (as 2.12/001)."""
import json, math, os
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
CHAIN = [5484, 5485, 5486, 5487, 5488, 5489, 5490, 5491, 5492, 5493, 5494, 5495, 5646, 5645, 5644, 5643, 5642, 5641, 5640, 5639, 5638,
         5637, 5636, 5635, 5634, 5632, 5631, 5630, 5629, 5628]
MOVED = [5484, 5485, 5486, 5487, 5488, 5489, 5490, 5491, 5492, 5493, 5494, 5495, 5496, 5629, 5630, 5631, 5632, 5634, 5635, 5636, 5637, 5638,
         5639, 5640, 5641, 5642, 5643, 5644, 5645, 5646, 16224]
TRAIL, FOT_TRAIL, JOINS = 16, 384, (14, 15)
CLEAR = 0.3
ROUND_D = 0.3
STEP0, STEP1 = 0.34, 0.2                        # (the stairway, as 2.12/001)
HALF0, HALF1 = 0.24, 0.13
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def _soft(p, d=ROUND_D):
    if len(p) < 3: return p
    out = [p[0]]
    for i in range(1, len(p) - 1):
        a, q, b = p[i - 1], p[i], p[i + 1]
        da = min(d, 0.45 * math.dist(a, q)); db = min(d, 0.45 * math.dist(q, b))
        pa = [q[0] + (a[0] - q[0]) * da / math.dist(a, q), q[1] + (a[1] - q[1]) * da / math.dist(a, q)]
        pb = [q[0] + (b[0] - q[0]) * db / math.dist(q, b), q[1] + (b[1] - q[1]) * db / math.dist(q, b)]
        out += [[round(pa[0], 3), round(pa[1], 3)], q, [round(pb[0], 3), round(pb[1], 3)]]
    return out + [p[-1]]


def _steps(a, b):
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    out = []; s = 0.6
    while s < L - 0.45:
        t = s / L; h = HALF0 + (HALF1 - HALF0) * t; x, y = a[0] + ux * s, a[1] + uy * s
        out.append([[round(x - nx * h, 3), round(y - ny * h, 3)], [round(x + nx * h, 3), round(y + ny * h, 3)]])
        s += STEP0 + (STEP1 - STEP0) * t
    return out


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct23b.json'))); P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}
    T = wild['track']
    old = {v: tuple((pos.get(str(v)) or T['cx%d' % v])[:2]) for v in MOVED}
    new = {v: [round(P[v][0], 2), round(P[v][1], 2)] for v in MOVED}
    assert [v for v in (5496, 16224) if v in S['hidden']] == [5496, 16224]
    for v in MOVED:
        if str(v) in pos: pos[str(v)] = list(new[v])
        if 'cx%d' % v in T: T['cx%d' % v] = list(new[v]) + list(T['cx%d' % v][2:])
    fw = wild['fwtracks']
    o16 = fw[TRAIL]; assert math.dist(o16[0][:2], old[5484]) < 0.01 and math.dist(o16[-1][:2], pos['5628'][:2]) < 0.01
    fw[TRAIL] = _soft([list(new[v]) if v in new else [round(c, 2) for c in pos[str(v)][:2]] for v in CHAIN])
    for i in JOINS:
        assert math.dist(fw[i][-1][:2] if math.dist(fw[i][-1][:2], old[5484]) < 0.01 else fw[i][0][:2], old[5484]) < 0.01
        fw[i] = [list(new[5484]) if math.dist(q[:2], old[5484]) < 0.01 else q for q in fw[i]]
    o384 = fw[FOT_TRAIL]; assert math.dist(o384[-1][:2], o16[7][:2]) < 0.01, o384[-1]
    fw[FOT_TRAIL] = list(o384[:-2]) + [list(new[5491])]
    d0 = wild['descents'][0]; assert math.dist(d0['pts'][0], old[5639]) < 0.01
    wild['descents'][0] = {'pts': [list(new[5639]), d0['pts'][1]], 'steps': _steps(new[5639], d0['pts'][1])}
    moved_pts = 0
    def fix(line):
        nonlocal moved_pts
        out = []
        for q in line:
            hit = next((v for v in MOVED if math.dist(q[:2], old[v]) < 0.05), None)
            if hit: moved_pts += 1; out.append(list(new[hit]) + list(q[2:]))
            else: out.append(q)
        return out
    routes = []
    for p in wild['places']:
        b = moved_pts
        if p.get('path'): p['path'] = fix(p['path'])
        if p.get('segs'): p['segs'] = [fix(s) for s in p['segs']]
        if moved_pts > b: routes.append(p['name'])
    lines = [fw[TRAIL], fw[FOT_TRAIL][-2:], wild['descents'][0]['pts']] + [fw[i] for i in JOINS]
    band = unary_union([LineString([q[:2] for q in l]).buffer(CLEAR) for l in lines])
    gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    others = unary_union([LineString([q[:2] for q in l]) for i, l in enumerate(fw) if i not in (TRAIL, FOT_TRAIL) + JOINS and len(l) > 1])
    newl = LineString([q[:2] for q in fw[TRAIL]])
    return {'rooms moved': len(MOVED), 'moved by (min / max)': (round(min(math.dist(old[v], new[v]) for v in MOVED), 2), round(max(math.dist(old[v], new[v]) for v in MOVED), 2)),
            'trail points (old -> new)': (len(o16), len(fw[TRAIL])), 'FoT trail end': (o384[-1], new[5491]), 'stairway steps': len(wild['descents'][0]['steps']),
            'route points moved': (moved_pts, routes), 'sprites cleared': gone, 'new trail to other Woods trails (crossings)': len(newl.intersection(others).geoms) if newl.intersection(others).geom_type.startswith('Multi') else (0 if newl.intersection(others).is_empty else 1)}
