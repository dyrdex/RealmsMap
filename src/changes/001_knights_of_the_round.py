"""The rooms west of the Forgotten Woods from the owner's Barren Peaks editor save of Oct 23 19:33Z (18:56Z; 19:08Z 11745 moved 3.5 north; 19:33Z 18 more shown) (legacy/bp_layout_oct23.json; the editor's
rooms and exits then: legacy/bp_editor_edges_oct23.json): 11745, 11744, 11743 below 5639 (area 'BS'), the Knights of the Round (area 'KR')
and 21075 The Royal Jetty of Camelot. Only the rooms the owner left shown are drawn (48; the other 47 hidden; save of Oct 23 19:33Z: 18 more shown).
  - trails: every flat exit between two shown new rooms is an ordinary Woods dirt trail (fwtracks), straight room to room, the bends only
    slightly rounded (as applied/v2.10/001's _soft);
  - the exits of the 18 rooms shown on Oct 23 19:33Z and 11740 south to 14070 (DASH_CHAIN): thin dashed lines (owner, Oct 23; `smrdash`); their one-way exits longer than LONG_ONE not drawn (owner);
  - 5639 d 11745 (owner, Oct 23: "make it look like it goes down"): a stairway (`descents`, template DESCENT): the dirt trail with steps across
    it, the steps closer together and narrower further down, the trail darkening towards 11745;
  - trees and tufts cleared within CLEAR of the new trails (the Woods' trails keep about that much clear);
  - room_pos: the 30 shown new rooms. The Woods rooms stay where the map has them (the save has 5634-5638
    0.08 off, and 4017-4019 off as in the save before)."""
import json, math, os
from collections import defaultdict
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
NEW_AREAS = ('BS', 'KR')
TOP, BOTTOM = 5639, 11745                       # the way down
ROUND_D = 0.3                                   # the trails' bends rounded over the last 0.3 rooms either side
CLEAR = 0.3                                     # sprites cleared this close to a new trail (the 5th percentile of the Woods' own trees)
STEP0, STEP1 = 0.34, 0.2                        # steps apart: at the top, at the bottom
HALF0, HALF1 = 0.24, 0.13                       # steps' half width: at the top, at the bottom
DASH_ROOMS = {14053, 14054, 14055, 14056, 14057, 14058, 14059, 14060, 14061, 20146, 21061, 21062, 21063, 21064, 21065, 21066, 21067, 21068}   # unhidden Oct 23 19:33Z
DASH_ALSO = {11741, 11742,                      # (owner, Oct 23: their exits dashed too)
             14071, 14072, 14073, 14074, 14075, 14076, 14077}   # (and The Wild Woodland: in from 14070, the maze, out to 14078)
DASH_CHAIN = [11740, 11738, 11737, 14062, 14065, 14066, 14068, 14069, 14070]   # (owner, Oct 23: 11740 south to 14070)
LONG_ONE = 2.0                                  # owner, Oct 23: no long one-way links from the rooms shown that day (not drawn past this length)
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')   # (not peaks: the stairway starts at 5639's own)


def _chains(G):
    chains = []; seen = set()
    for v in [v for v in G if len(G[v]) != 2] + sorted(G):
        for u in sorted(G[v]):
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    return chains


def _soft(p, d=ROUND_D):
    """each inner room flanked by a point d before and after it, so the template's curve runs straight from room to room (applied/v2.10/001)"""
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
    """steps across the line a -> b, from just below a to just above b: spacing and width shrink linearly going down"""
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    out = []; s = 0.6
    while s < L - 0.45:
        t = s / L; h = HALF0 + (HALF1 - HALF0) * t; x, y = a[0] + ux * s, a[1] + uy * s
        out.append([[round(x - nx * h, 3), round(y - ny * h, 3)], [round(x + nx * h, 3), round(y + ny * h, 3)]])
        s += STEP0 + (STEP1 - STEP0) * t
    return out


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct23.json'))); E = json.load(open(os.path.join(LEG, 'bp_editor_edges_oct23.json')))
    info = {r['id']: r for r in E['rooms']}
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; hidden = set(S['hidden'])
    NEW = {v for v, r in info.items() if r.get('area') in NEW_AREAS or v == 21075}
    shown = sorted(v for v in NEW if v not in hidden)
    assert len(NEW) == 95 and len(shown) == 48 and all(str(v) not in pos for v in NEW), (len(NEW), len(shown))
    assert math.dist(P[TOP], pos[str(TOP)][:2]) < 0.01
    PO = {v: tuple(pos[str(v)][:2]) for v, r in info.items() if r.get('src') == 'FW' and str(v) in pos}      # the Woods' rooms where the map has them
    nudged = sorted(v for v in PO if math.dist(P[v], PO[v]) > 0.01)
    # ---- rooms ----
    for v in shown: pos[str(v)] = [P[v][0], P[v][1]]
    # ---- trails ----
    G = defaultdict(set); GD = defaultdict(set); ud = []; dropped = []
    chain = {(min(a, b), max(a, b)) for a, b in zip(DASH_CHAIN, DASH_CHAIN[1:])}
    for a, b, k in E['edges']:
        if not (a in NEW or b in NEW) or a in hidden or b in hidden: continue
        if k == 'ud': ud.append((a, b)); continue
        assert a in NEW and b in NEW, (a, b)
        if k == 'one' and (a in DASH_ROOMS or b in DASH_ROOMS) and math.dist(P[a], P[b]) > LONG_ONE: dropped.append((a, b, round(math.dist(P[a], P[b]), 2))); continue
        H = GD if (a in DASH_ROOMS or b in DASH_ROOMS or a in DASH_ALSO or b in DASH_ALSO or (min(a, b), max(a, b)) in chain) else G
        H[a].add(b); H[b].add(a)
    assert ud == [(TOP, BOTTOM)], ud
    assert all(b in GD[a] for a, b in zip(DASH_CHAIN, DASH_CHAIN[1:]))
    new = [_soft([[round(P[v][0], 2), round(P[v][1], 2)] for v in ch]) for ch in _chains(G)]
    wild['fwtracks'] = list(wild['fwtracks']) + new
    dash = []                                                   # owner, Oct 23: thin dashed lines in the trails' colour (template smrdash), straight room to room
    for ch in _chains(GD):
        l = [[round(P[v][0], 2), round(P[v][1], 2)] for v in ch]; l = [l[0]] + [q for o, q in zip(l, l[1:]) if q != o]
        if len(l) > 1: dash.append(l)
    wild['smrdash'] = list(wild.get('smrdash') or []) + dash
    a, b = [round(c, 2) for c in P[TOP]], [round(c, 2) for c in P[BOTTOM]]
    steps = _steps(a, b)
    wild['descents'] = list(wild.get('descents') or []) + [{'pts': [a, b], 'steps': steps}]
    # ---- sprites off the new trails ----
    band = unary_union([LineString(l).buffer(CLEAR) for l in new + dash + [[a, b]]])
    gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    # ---- checks ----
    old = unary_union([LineString(l) for l in wild['fwtracks'][:-len(new)] if len(l) > 1])
    mine = [LineString(l) for l in new + dash + [[a, b]]]
    cross = sum(1 for l in mine if l.crosses(old))
    others = [(v, round(min(l.distance(Point(q[:2])) for l in mine), 2)) for v, q in pos.items() if int(v) not in NEW and int(v) != TOP
              and min(l.distance(Point(q[:2])) for l in mine) < 0.5]
    return {'rooms placed (shown of new; hidden)': (len(shown), len(NEW) - len(shown)), 'trails added (lines, exits)': (len(new), sum(len(G[v]) for v in G) // 2),
            'long one-way links not drawn': dropped, 'thin dashed lines (lines, exits, longest exit)': (len(dash), sum(len(GD[v]) for v in GD) // 2, max(round(math.dist(P[a_], P[b_]), 2) for a_ in GD for b_ in GD[a_])),
            'stairway 5639-11745 (length, steps)': (round(math.dist(a, b), 2), len(steps)), 'sprites cleared': gone,
            'new lines crossing old trails': cross, 'other rooms within 0.5 of a new line': others,
            'Woods rooms the save has off their map spots, not drawn (max distance)': (nudged, round(max([math.dist(P[v], PO[v]) for v in nudged] or [0]), 3))}
