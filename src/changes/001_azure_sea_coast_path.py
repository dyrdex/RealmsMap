"""The Azure Sea Coast path redrawn from the owner's Azure Sea Coast editor save of Oct 23 (16:48Z, `legacy/az_layout_oct23.json`; editor data with
the 26 rooms added that day, `legacy/az_editor_edges_oct23.json`). Owner (Oct 23): only the coastal sea path's rooms change, nothing on the
mainland; near Ocean Keep the on-land stream may change.
  - the old path lines go: every type B route (`seawaysfaint`) through a moved or newly shown path room (the long coast line and the Ocean Keep
    stream); the lines through unmoved rooms only (4317 - 14314 - 22557, 4317 to Edo, Edo's own) stay as they are;
  - every exit between two shown path rooms is drawn again, as a standard water path: straight room to room, in maplib.warpline's bend (joined
    into lines between junctions, so no seams);
  - the small dashed links to the mainland (`seadash`) follow their moved path room (the mainland end stays);
  - the name 'Azure Sea Coastal Path' moves beside the new path (LABEL; same size and style);
  - the stream by Ocean Keep: sprites within CLEAR of its new line cleared (as az_merge did; owner allowed changes there);
  - land, sea, cliffs and every other mainland drawing untouched."""
import json, math, os
from collections import defaultdict
from maplib import warp, warpline

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
LABEL = [42.0, -201.6, 0]                           # [x, y, rotation]: north of the long straight 14315 - 4317 (text 13.7 rooms long, measured once;
                                                    #   0.7 from the path, 2.3 from any room, 3.9 from land, no other name within 20)
STREAM_BOX = (53.0, -38.0, 64.0, -27.0)             # the on-land stream by Ocean Keep (14257 .. 14263): nothing grows within CLEAR of it
CLEAR = 0.35
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'peaks', 'boulders', 'reeds', 'wheattufts', 'brush', 'crags', 'ripples')


def _chains(G, pins=()):
    chains = []; seen = set()
    for v in [v for v in sorted(G) if len(G[v]) != 2 or v in pins] + sorted(G):
        for u in sorted(G[v]):
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2 and ch[-1] not in pins:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    return chains


def apply(town, wild, pos):
    old = json.load(open(os.path.join(LEG, 'az_layout_final.json'))); new = json.load(open(os.path.join(LEG, 'az_layout_oct23.json')))
    E = json.load(open(os.path.join(LEG, 'az_editor_edges_oct23.json')))
    P0 = dict(zip(old['ids'], zip(old['xs'], old['ys']))); P1 = dict(zip(new['ids'], zip(new['xs'], new['ys'])))
    info = {r['id']: r for r in E['rooms']}; az = {v for v, r in info.items() if r.get('area') == 'AZ'}
    h0, h1 = set(old['hidden']), set(new['hidden'])
    moved = {v for v in az if v in P0 and math.dist(P0[v], P1[v]) > 1e-3}
    changed = moved | {v for v in az if (v not in P0 or v in h0) and v not in h1}     # moved, new, or shown again
    keep = {v for v in az if v not in changed and v not in h1}                         # (unmoved, shown before and now)

    # ---- the old lines through a changed room ----
    oldpts = [warp(*P0[v]) for v in changed if v in P0]
    hit = lambda l: any(math.dist(q[:2], p) < 0.05 for q in l for p in oldpts)
    F = wild['seawaysfaint']; gone = [i for i, l in enumerate(F) if len(l) > 1 and hit(l)]
    gone_pts = sum(len(F[i]) for i in gone)
    wild['seawaysfaint'] = [l for i, l in enumerate(F) if i not in gone]
    kept_pts = [q[:2] for l in wild['seawaysfaint'] for q in l]
    onkept = lambda v: any(math.dist(warp(*P1[v]), q) < 0.4 for q in kept_pts)            # (the kept lines were smoothed: up to 0.3 off a room)
    covered = set()                                                                    # (exits already in the kept lines: both rooms unmoved)
    G = defaultdict(set); n_ex = 0
    for a, b, k in E['edges']:
        if a not in az or b not in az or a in h1 or b in h1 or a == b: continue
        if a in keep and b in keep and onkept(a) and onkept(b): covered.add((a, b)); continue
        G[a].add(b); G[b].add(a); n_ex += 1
    joined = 0
    lines = [warpline([list(P1[v]) for v in ch]) for ch in _chains(G, {v for v in G if v in keep and onkept(v)})]   # (lines end at rooms on a kept line)
    for l in lines:                                                                    # a new line meeting a kept one ends on it (as changes/006, BLEND 0.6)
        for end in (0, -1):
            q = l[end][:2]; near = min(kept_pts, key=lambda k: math.dist(k, q))
            if not 0.01 < math.dist(near, q) < 0.4: continue
            dx, dy = near[0] - q[0], near[1] - q[1]; run = 0.0; prev = None
            for i in (range(len(l)) if end == 0 else range(len(l) - 1, -1, -1)):
                if prev is not None: run += math.dist(l[i][:2], l[prev][:2])
                if run >= 0.6: break
                f = 1 - run / 0.6; l[i] = [round(l[i][0] + dx * f, 3), round(l[i][1] + dy * f, 3)]; prev = i
            joined += 1
    wild['seawaysfaint'] += lines

    # ---- nothing grows in the stream (by Ocean Keep only) ----
    x0, y0, x1, y1 = STREAM_BOX
    segs = [(p, q) for l in lines for p, q in zip(l, l[1:]) if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
    def dseg(c, p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((c[0] - p[0]) * dx + (c[1] - p[1]) * dy) / L))
        return math.dist(c, (p[0] + t * dx, p[1] + t * dy))
    cleared = {}
    for k in SPRITES:
        L0 = wild.get(k) or []
        kept = [q for q in L0 if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and any(dseg(q[:2], p, r) < CLEAR for p, r in segs))]
        if len(kept) != len(L0): cleared[k] = len(L0) - len(kept); wild[k] = kept

    # ---- the dashed links to the mainland ----
    D = wild['seadash']; nd = 0
    for a, b, k in E['edges']:
        if (a in az) == (b in az): continue
        v, f = (a, b) if a in az else (b, a)
        if v not in moved and v not in G: continue                                     # (a room whose line was redrawn: its link ends on the new line)
        near = lambda e: math.dist(e, P0[v]) < 0.3 or math.dist(e, warp(*P0[v])) < 0.3
        for l in D:
            for j, o in ((0, -1), (-1, 0)):
                if near(l[j][:2]) and str(f) in pos and math.dist(l[o][:2], pos[str(f)][:2]) < 0.05:
                    q = warp(*P1[v]); l[j] = [round(q[0], 3), round(q[1], 3)]; nd += 1; break

    # ---- the name ----
    tag = [t for t in wild['seatags'] if t[2] == 'Azure Sea Coastal Path']
    assert len(tag) == 1
    was = list(tag[0])
    if LABEL: tag[0][0], tag[0][1], tag[0][4] = LABEL

    return {'old lines removed (lines, points)': (len(gone), gone_pts),
            'path rooms (moved, newly shown, hidden now)': (len(moved), len(changed - moved), len(h1 & az)),
            'new lines (lines, exits, rooms); exits kept in old lines': (len(lines), n_ex, len(G), len(covered)),
            'new line ends moved onto kept lines': joined, 'dashed links moved': nd, 'sprites cleared off the stream': cleared, 'label': (was[:2], tag[0][:2], tag[0][4])}
