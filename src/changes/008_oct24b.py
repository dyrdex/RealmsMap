"""Owner, Oct 24 (second batch):
  - Barren Peaks + Forgotten Woods editor save of Oct 24 15:44Z (`legacy/bp_layout_oct24b.json`): The Narrowings 6731 shown and moved, the new
    rooms The hills 6732, A Narrow Trail 6733 and The hills 6736 placed, Smeared Blood 6824 and The Forests to the South 6825 moved
    (22139, now hidden, was never drawn). New trails, straight room to room (as 2.12/007): 6730 - 6731 - 6732, 6732 - 6733, 6732 - 6736 (an
    end room off every old trail ends on the nearest trail); fwtracks[229] (6822 ... 6830, through 6824 and 6825) redrawn through its rooms'
    spots (it passed up to 0.79 off them), gently rounded (ROUND_D); route lines through the moved rooms follow them;
  - Kingdom of Juargan: the owner's new directions (Oct 24; KJ_ROUTE, numbered form only), its line and marker reach The hills 6736;
  - a new location, Mount Krozloy (A Narrow Trail 6733), the owner's directions (numbered), traced as 2.12/005;
  - Angel's Landing's trail (fwtracks[639], 5667 sw 16226 to the landing) starts where the beach trail (fwtracks[30]) passes 5667, so it no
    longer stops short of it (0.68 off);
  - the long dashed links from the Barren Peaks' east side to the Azure Sea Coast path (seadash longer than LONG): moved to `seadashfaint`
    (template: a darker blue, fainter), the two short links stay as they were;
  - The Grimdog Port Authority's label pinned east of its marker, Old Thalos's west of its marker (template LBL/PINNED); Sesuad'ra Rift's
    marker NUDGE south to make room, its label pinned at the same spot beside it as before;
  - the Lost in the Swamp maze blob drawn over the trails (`top`, as The Wild Woodland; owner: the tightened trails showed over it)."""
import json, math, os
import maplib
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, nearest_points

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
MOVED = [6731, 6824, 6825]
NEW = [6732, 6733, 6736]
EDGES = [(6730, 6731), (6731, 6732), (6732, 6733), (6732, 6736)]
CHAIN229 = [6822, 6823, 6824, 6825, 6826, 6828, 6829, 6830]
ROUND_D, CLEAR, SNAP = 0.3, 0.3, 0.05
KROZLOY = ('Mount Krozloy', 6733, 'n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;sw;sw;s;s;ne;ne;n;nw;w;nw;nw;w;nw;nw;nw;w;w;w;nw;nw;w;w;w;s;e;ne;ne;ne;se;e;e;e;e;se;se;e;e;e;e;e;e;n;e;e;n')
LONG = 10.0
KJ_ROUTE = 'n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;sw;sw;s;s;ne;ne;n;nw;w;nw;nw;w;nw;nw;nw;w;w;w;nw;nw;w;w;w;s;e;ne;ne;ne;se;e;e;e;e;se;se;e;e;e;e;e;e;n;e;e;e'   # (owner, Oct 24; never edited)
NUDGE = (0.0, 0.5)                                   # Sesuad'ra Rift's marker, south
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


def _trace(walk, at, route):
    t = walk(route); segs = [[]]
    for v in t:
        if at(v):
            q = [round(at(v)[0], 3), round(at(v)[1], 3)]
            if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
    return t, [s for s in segs if s]


def apply(town, wild, pos):
    rooms, exits = maplib.world(); out = {}
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct24b.json'))); P = dict(zip(S['ids'], zip(S['xs'], S['ys']))); hidden = set(S['hidden'])
    assert not (set(MOVED) | set(NEW) | set(CHAIN229)) & hidden and 22139 in hidden
    old = {v: tuple(pos[str(v)][:2]) for v in MOVED}
    for v in MOVED + NEW: pos[str(v)] = [round(P[v][0], 2), round(P[v][1], 2)]
    at = lambda v: [round(c, 2) for c in pos[str(v)][:2]]
    fw = wild['fwtracks']
    # ---- fwtracks[229] through its rooms ----
    o229 = fw[229]; assert math.dist(o229[0][:2], at(6822)) < 0.01 and math.dist(o229[-1][:2], at(6830)) < 0.01
    dev0 = round(max(LineString([q[:2] for q in o229]).distance(Point(old.get(v, at(v)))) for v in CHAIN229), 2)
    fw[229] = _soft([at(v) for v in CHAIN229])
    # ---- the new trails ----
    oldnet = unary_union([LineString([q[:2] for q in l]) for l in fw if len(l) > 1])
    new, snapped = [], []
    for a, b in EDGES:
        line = []
        for v in (a, b):
            q = at(v)
            if v not in MOVED + NEW and oldnet.distance(Point(q)) > SNAP:
                n = nearest_points(oldnet, Point(q))[0]; snapped.append((v, round(oldnet.distance(Point(q)), 2))); q = [round(n.x, 2), round(n.y, 2)]
            line.append(q)
        new.append(line)
    fw.extend(new)
    band = unary_union([LineString(l).buffer(CLEAR) for l in new + [fw[229]]]); gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    # ---- route lines through the moved rooms ----
    moved_pts, routes = 0, []
    def fix(line):
        nonlocal moved_pts
        res = []
        for q in line:
            hit = next((v for v in MOVED if math.dist(q[:2], old[v]) < 0.05), None)
            if hit: moved_pts += 1; res.append(at(hit) + list(q[2:]))
            else: res.append(q)
        return res
    for p in wild['places']:
        b0 = moved_pts
        if p.get('path'): p['path'] = fix(p['path'])
        if p.get('segs'): p['segs'] = [fix(s) for s in p['segs']]
        if moved_pts > b0: routes.append(p['name'])
    out['save: rooms moved / placed, trails added (ends snapped), fwtracks[229] max room offset old -> new, sprites cleared, route points moved'] = (
        {v: (old[v], at(v)) for v in MOVED}, {v: at(v) for v in NEW}, (len(new), snapped),
        (dev0, round(max(LineString([q[:2] for q in fw[229]]).distance(Point(at(v))) for v in CHAIN229), 2)), gone, (moved_pts, routes))
    # ---- Kingdom of Juargan to 6736; Mount Krozloy ----
    walk, atw = maplib.tracer(pos, wild)
    kj = next(p for p in wild['places'] if p['name'] == 'Kingdom of Juargan')
    route = maplib.condense(KJ_ROUTE); t, segs = _trace(walk, atw, route)
    assert t[-1] == 6736, t[-3:]
    kj.update(route=route, room=rooms[6736]['name'], dir='here', path=segs[0], segs=segs)
    name, room, raw = KROZLOY
    assert not any(p['name'] == name for p in wild['places'])
    route = maplib.condense(raw); t, segs = _trace(walk, atw, route)
    assert t[-1] == room, t[-3:]
    wild['places'].append(dict(name=name, route=route, room=rooms[room]['name'], dir='here', path=segs[0], segs=segs, group='fw', note=None))
    out['Kingdom of Juargan marker; Mount Krozloy (route, rooms walked, marker)'] = (segs and kj['segs'][-1][-1], (route, len(t) - 1, segs[-1][-1]))
    # ---- Angel's Landing's trail joined to the beach trail ----
    l639 = fw[639]; assert math.dist(l639[0][:2], at(5667)) < 0.01
    beach = LineString([q[:2] for q in fw[30]]); n = nearest_points(beach, Point(at(5667)))[0]
    fw[639] = [[round(n.x, 3), round(n.y, 3)]] + list(l639)
    out["Angel's Landing trail: start joined to the beach trail (gap was)"] = round(beach.distance(Point(at(5667))), 2)
    # ---- the long dashed links: fainter ----
    D = wild['seadash']; faint = [l for l in D if LineString(l).length > LONG]
    wild['seadash'] = [l for l in D if LineString(l).length <= LONG]; wild['seadashfaint'] = list(wild.get('seadashfaint') or []) + faint
    out['dashed links made fainter (kept as they were)'] = (len(faint), len(wild['seadash']))
    # ---- Sesuad'ra Rift's marker ----
    sr = next(p for p in wild['places'] if p['name'] == "Sesuad'ra Rift"); a0 = list(sr['at'])
    sr['at'] = [round(a0[0] + NUDGE[0], 2), round(a0[1] + NUDGE[1], 2)]
    out["Sesuad'ra Rift marker (old -> new)"] = (a0, sr['at'])
    mz = next(m for m in wild['fwmazes'] if m.get('name') == 'Lost in the Swamp'); mz['top'] = True
    out['Lost in the Swamp maze over the trails'] = True
    return out
