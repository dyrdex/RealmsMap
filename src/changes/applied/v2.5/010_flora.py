# Otherland's plants (owner, Oct 22): snow-laden pines, bare leafless trees, bushes and ground cover, all dusted with snow and looking cold
# (template OLFLORA). Where they grow follows the nearest room's name: tundra and steppe mostly ground cover and low bushes; hills scattered
# pines, bare trees and bushes; the mountains a few stunted pines; near the shore bushes; elsewhere small pine groves among bare trees and
# bushes. Kept clear of the trails, rooms, mazes, clearings, shacks, the gorge, the coast, the drifts and everything else drawn on the snow.
import math, random, sys
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from scipy.spatial import cKDTree
from maplib import world

STEP = 0.32                                     # candidate spots on a jittered grid this fine
# per square room, by the land's kind: pine (times the grove field), bare tree, bush, ground cover
DENS = {'tundra':   (0.006, 0.02, 0.11, 0.55),
        'hills':    (0.28, 0.09, 0.22, 0.18),
        'mountain': (0.12, 0.02, 0.07, 0.09),
        'shore':    (0.0, 0.02, 0.15, 0.25),
        'open':     (0.38, 0.11, 0.18, 0.18)}
SIZE = {'p': (0.8, 1.25), 'b': (0.8, 1.15), 's': (0.6, 0.95), 'g': (0.85, 1.3)}
FOOT = {'p': (.36, .62, .3), 'b': (.3, .58, .2), 's': (.3, .34, .1), 'g': (.18, .14, .08)}   # half width, height up, depth down (at scale 1)
NVAR = {'p': 3, 'b': 3, 's': 2, 'g': 2}


def kind_of(name):
    n = name.lower()
    if any(k in n for k in ('tundra', 'steppe', 'out in the cold', 'calm before')): return 'tundra'
    if any(k in n for k in ('hill', 'ridge', 'foothill', 'maedar')): return 'hills'
    if any(k in n for k in ("morte", 'gods', 'peak', 'spire', 'pass', 'face', 'plateau', 'zenith', 'ledge', 'cliff', 'mountain', 'drop-off', 'sudden',
                            'roof', 'jarl', 'sacrifice', 'gully', 'gullet', 'heart', 'entombed', 'cavern', 'burrow', 'the cave', 'crisp path', 'darkness')): return 'mountain'
    if any(k in n for k in ('shore', 'beach', 'coast', 'harbor', 'dock', 'sea', 'ocean', 'iceberg', 'arctic')): return 'shore'
    return 'open'


def apply(town, wild, pos):
    rooms, _ = world(); rr = random.Random(23240)
    snowp = [Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2]
    main = max(snowp, key=lambda g: g.area)
    named = [(pos[str(v)], kind_of(r['name'])) for v, r in rooms.items() if r['area'] == 'Otherland' and r['name'] and str(v) in pos and main.contains(Point(pos[str(v)]))]
    tree = cKDTree([q for q, _ in named])
    # everything to keep clear of
    L = lambda k: [LineString(l) for l in wild.get(k, []) if len(l) > 1]
    o = wild['olsnow']; G = wild['olgorge']
    block = [g.buffer(0.42) for g in L('oltracks')] + [g.buffer(0.25) for g in L('oltunnels')]
    block += [Point(q).buffer(0.45) for q in pos.values() if main.buffer(1).contains(Point(q))]
    block += [Polygon(m['poly']).buffer(0.3) for m in wild['fwmazes'] if Polygon(m['poly']).intersects(main)]
    block += [Polygon(h).buffer(0.2) for c in wild.get('clearings', []) for h in c['polys'] if Polygon(h).intersects(main)]
    block += [box(x - w / 2, y - h / 2, x + w / 2, y + h / 2).buffer(0.4) for x, y, w, h in wild.get('olshacks', [])]
    if wild.get('olmansion'): x, y, w, h = wild['olmansion']; block.append(box(x - w / 2, y - h / 2, x + w / 2, y + h / 2).buffer(0.5))
    block += [Polygon(p).buffer(0).buffer(0.3) for p in G['band'] if len(p) > 2]
    if wild.get('olledge'): block.append(Polygon(wild['olledge']['face']).buffer(0).buffer(0.3))
    if wild.get('olrunoff'): block.append(LineString(wild['olrunoff']).buffer(0.4))
    block += [Polygon(p).buffer(0).buffer(0.2) for p in wild['olsouth']['beach'] if len(p) > 2]
    block += [Point(d[:2]).buffer(0.55 * d[2]) for d in o['drifts']] + [Polygon(q).buffer(0).buffer(0.12) for q in o['ice'] if len(q) > 2]
    block += [Point(m['cx'], m['cy']).buffer(1.4) for m in wild['fwmazes'] if m.get('name')]                   # (the maze names)
    BL = prep(unary_union(block)); inland = prep(main.buffer(-0.7))
    # the grove field: smooth noise, pines gather where it is high
    ph = [rr.uniform(0, 6.3) for _ in range(6)]
    grove = lambda x, y: (math.sin(x * 0.55 + ph[0]) * math.sin(y * 0.47 + ph[1]) + 0.6 * math.sin((x + y) * 0.31 + ph[2]) + 0.4 * math.sin((x - y) * 0.83 + ph[3])) / 2.0
    x0, y0, x1, y1 = main.bounds
    cell = {}; out = []; cnt = {k: 0 for k in 'pbsg'}; byland = {}
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            px, py = x + rr.uniform(0, STEP), y + rr.uniform(0, STEP)
            x += STEP
            d, i = tree.query((px, py))
            land = named[i][1] if d < 6 else 'open'
            dp, db, ds, dg = DENS[land]
            gv = max(0.0, min(1.0, (grove(px, py) - 0.05) * 2.2))
            probs = {'p': dp * gv * 2.2, 'b': db * (0.6 + 0.8 * (1 - gv)), 's': ds, 'g': dg}
            u = rr.random() / (STEP * STEP); k = None
            for kk, pk in probs.items():
                if u < pk: k = kk; break
                u -= pk
            if not k: continue
            lo, hi = SIZE[k]; s = rr.uniform(lo, hi) * (0.75 if land == 'mountain' and k == 'p' else 1)
            hw, up, dn = FOOT[k]
            fp = box(px - hw * s, py - up * s, px + hw * s, py + dn * s)
            if not inland.contains(fp) or BL.intersects(fp): continue
            near = [q for a in range(int(px) - 1, int(px) + 2) for b in range(int(py) - 1, int(py) + 2) for q in cell.get((a, b), [])]
            if any(math.dist((px, py), q[:2]) < 0.3 * (s + q[2]) + (0.12 if 'p' in (k, q[3]) else 0.04) for q in near): continue
            it = [round(px, 3), round(py, 3), round(s, 3), k, rr.randrange(NVAR[k])]
            out.append(it); cell.setdefault((int(px), int(py)), []).append(it); cnt[k] += 1
            byland.setdefault(land, {kk: 0 for kk in 'pbsg'})[k] += 1
        y += STEP
    wild['olflora'] = out
    return {'Otherland plants (pines, bare trees, bushes, ground cover; by land kind)': (cnt['p'], cnt['b'], cnt['s'], cnt['g'], byland)}
