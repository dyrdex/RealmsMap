# Otherland's plants and drifts evenly everywhere (owner, Oct 22): the bare patches (new land east of Morte's Peak, between the Fissure's
# descents, ...) filled. A drift goes wherever the nearest drift is over DRIFT_GAP away, then a plant wherever the nearest plant is over
# PLANT_GAP away (both about the 90th-percentile spacing where they already grow), kinds by the land as applied/v2.5/010, own random.
import importlib.util, math, os, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from scipy.spatial import cKDTree
from maplib import world

_spec = importlib.util.spec_from_file_location('ol_flora', os.path.join(os.path.dirname(__file__), 'applied', 'v2.5', '010_flora.py'))
FL = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(FL)
PLANT_GAP, DRIFT_GAP, TRY = 1.6, 3.3, 0.35          # rooms; candidate spots on a jittered grid this fine


def polys(x, out):
    if isinstance(x, list) and len(x) > 2 and all(isinstance(q, list) and len(q) == 2 and isinstance(q[0], (int, float)) for q in x): out.append(Polygon(x).buffer(0))
    elif isinstance(x, list): [polys(y, out) for y in x]
    elif isinstance(x, dict): [polys(y, out) for y in x.values()]
    return out


def apply(town, wild, pos):
    rooms, _ = world(); rr = random.Random(2215)
    main = max((Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2), key=lambda g: g.area)
    named = [(pos[str(v)], FL.kind_of(r['name'])) for v, r in rooms.items() if r['area'] == 'Otherland' and r['name'] and str(v) in pos and main.contains(Point(pos[str(v)]))]
    ktree = cKDTree([q for q, _ in named])
    L = lambda k: [LineString(l) for l in wild.get(k, []) if len(l) > 1]
    o = wild['olsnow']; G = wild['olgorge']
    block = [g.buffer(0.42) for g in L('oltracks')] + [g.buffer(0.25) for g in L('oltunnels')]
    block += [Point(q[:2]).buffer(0.45) for q in pos.values() if main.buffer(1).contains(Point(q[:2]))]
    block += [Polygon(m['poly']).buffer(0.3) for m in wild['fwmazes'] if Polygon(m['poly']).intersects(main)]
    block += [Point(m['cx'], m['cy']).buffer(1.4) for m in wild['fwmazes'] if m.get('name')]
    block += [Polygon(h).buffer(0.2) for c in wild.get('clearings', []) for h in c['polys'] if Polygon(h).intersects(main)]
    block += [box(x - w / 2, y - h / 2, x + w / 2, y + h / 2).buffer(0.4) for x, y, w, h in wild.get('olshacks', [])]
    x, y, w, h = wild['olmansion'][:4]; block.append(box(x - w / 2, y - h / 2, x + w / 2, y + h / 2).buffer(0.5))
    block += [g.buffer(0.3) for g in polys(G['band'], [])] + [g.buffer(0.2) for g in polys(wild.get('olfissure'), [])]
    block += [g.buffer(0.3) for g in polys(wild.get('olcliff', {}).get('face'), [])]
    if wild.get('olledge'): block.append(Polygon(wild['olledge']['face']).buffer(0).buffer(0.3))
    if wild.get('olrunoff'): block.append(LineString(wild['olrunoff']).buffer(0.4))
    block += [g.buffer(0.2) for g in polys(wild['olsouth']['beach'], [])]
    block += [Polygon(M['levels'][1]['ledge'][0]).buffer(0.5) for M in wild.get('olmassif', []) if len(M['levels']) > 1]   # bare terraces
    block += [Polygon(q).buffer(0).buffer(0.12) for q in o['ice'] if len(q) > 2]
    BL = prep(unary_union(block)); inland = prep(main.buffer(-0.7))
    x0, y0, x1, y1 = main.bounds
    spots = [(gx + rr.uniform(0, TRY), gy + rr.uniform(0, TRY)) for gy in [y0 + j * TRY for j in range(int((y1 - y0) / TRY) + 1)]
             for gx in [x0 + i * TRY for i in range(int((x1 - x0) / TRY) + 1)]]
    rr.shuffle(spots)
    # drifts first (the plants keep clear of them)
    D = o['drifts']; dcell = {}
    for q in D: dcell.setdefault((int(q[0] // DRIFT_GAP), int(q[1] // DRIFT_GAP)), []).append(q)
    near = lambda cell, p, g: [q for a in (-1, 0, 1) for b in (-1, 0, 1) for q in cell.get((int(p[0] // g) + a, int(p[1] // g) + b), [])]
    nd = 0
    for px, py in spots:
        s = rr.uniform(0.7, 1.25)
        if any(math.dist((px, py), q[:2]) < DRIFT_GAP for q in near(dcell, (px, py), DRIFT_GAP)): continue
        fp = Point(px, py).buffer(0.8 * s)
        if not inland.contains(fp) or BL.intersects(fp): continue
        it = [round(px, 3), round(py, 3), round(s, 2), round(rr.uniform(-0.35, 0.35), 3)]
        D.append(it); dcell.setdefault((int(px // DRIFT_GAP), int(py // DRIFT_GAP)), []).append(it); nd += 1
    DB = prep(unary_union([Point(q[:2]).buffer(0.55 * q[2]) for q in D]))
    F = wild['olflora']; fcell = {}
    for q in F: fcell.setdefault((int(q[0] // PLANT_GAP), int(q[1] // PLANT_GAP)), []).append(q)
    cnt = {k: 0 for k in 'pbsg'}
    for px, py in spots:
        if any(math.dist((px, py), q[:2]) < PLANT_GAP for q in near(fcell, (px, py), PLANT_GAP)): continue
        dk, i = ktree.query((px, py)); land = named[i][1] if dk < 6 else 'open'
        wts = FL.DENS[land]; u = rr.random() * sum(wts); k = 'g'
        for kk, wk in zip('pbsg', wts):
            if u < wk: k = kk; break
            u -= wk
        lo, hi = FL.SIZE[k]; s = rr.uniform(lo, hi) * (0.75 if land == 'mountain' and k == 'p' else 1)
        hw, up, dn = FL.FOOT[k]; fp = box(px - hw * s, py - up * s, px + hw * s, py + dn * s)
        if not inland.contains(fp) or BL.intersects(fp) or DB.intersects(fp): continue
        it = [round(px, 3), round(py, 3), round(s, 3), k, rr.randrange(FL.NVAR[k])]
        F.append(it); fcell.setdefault((int(px // PLANT_GAP), int(py // PLANT_GAP)), []).append(it); cnt[k] += 1
    return {'Otherland filled evenly (drifts added; plants added: pines, bare trees, bushes, ground cover)': (nd, cnt['p'], cnt['b'], cnt['s'], cnt['g'])}
