"""Scale the Forgotten Woods (down) and the Forest of Tears (up) as whole areas.

Everything with a position in the map data (land outline, terrain shapes, trees, trails, roads, markers, labels, mazes,
mist...) goes through the same smooth warp, so layouts, paths and markers keep their exact arrangement and only the overall
size changes.

  * Forest of Tears: scaled about the Darkguard gate (x = -9), growing from 1.0x at the town side to FOREST_X across and
    FOREST_Y up-and-down over the next BAND_F rooms, then held there.
  * Forgotten Woods: scaled about its way in from the Shadow Grove (y = -17), shrinking from 1.0x there to WOODS over the next
    BAND_W rooms, then held at WOODS.
  * Darkhaven, the Shadow Grove, Miden'nir and the rest are untouched.

Because the size changes, trees and grass are thinned (Woods) or topped up (Forest) so their density looks the same.
"""
import math, random
import numpy as np
from scipy.spatial import cKDTree
from matplotlib.path import Path

FOREST_X, FOREST_Y, WOODS = 1.75, 1.20, 0.80   # the forest is stretched east-west; its height stays as it was
AX_F, BAND_F = -9.0, 12.0
AY_W, BAND_W = -17.0, 10.0

def _ss(t):
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return t * t * (3 - 2 * t)

def T(x, y):
    wW = _ss((AY_W - y) / BAND_W)                    # 0 south of the Woods' way in, 1 well inside the Woods
    tF = _ss((AX_F - x) / BAND_F)                      # 0 at the town side, 1 well inside the forest
    sFx, sFy = 1 + (FOREST_X - 1) * tF, 1 + (FOREST_Y - 1) * tF
    x1, y1 = AX_F + sFx * (x - AX_F), sFy * y
    wF = 1 - wW
    xb, yb = x + wF * (x1 - x), y + wF * (y1 - y)
    sW = 1 + (WOODS - 1) * wW
    return sW * xb, AY_W + sW * (yb - AY_W)

def area_scale(x, y, h=0.05):
    xa, ya = T(x + h, y); xb, yb = T(x - h, y)
    xc, yc = T(x, y + h); xd, yd = T(x, y - h)
    a, b, c, d = (xa - xb) / (2 * h), (ya - yb) / (2 * h), (xc - xd) / (2 * h), (yc - yd) / (2 * h)
    return abs(a * d - b * c)

def _pt(p):
    x, y = T(p[0], p[1]); return [round(x, 3), round(y, 3)] + list(p[2:])

def _is_pt(v):
    return isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(q, (int, float)) for q in v)

def _poly(v):                                       # any nesting of lists of [x, y] points
    if _is_pt(v): return _pt(v)
    if isinstance(v, list): return [_poly(q) for q in v]
    return v

def _label(d):
    if not d: return d
    xa, ya = T(d['x0'], d['y']); xb, yb = T(d['x1'], d['y'])
    return dict(d, x0=round(xa, 2), x1=round(xb, 2), y=round((ya + yb) / 2, 2))

def _vline(v):                                      # [x, y0, y1] vertical strokes (piers, bridges)
    if not v: return v
    x, y0, y1 = v; xa, ya = T(x, y0); xb, yb = T(x, y1)
    return [round((xa + xb) / 2, 3), round(ya, 3), round(yb, 3)]

def _even_odd(polys):
    paths = [Path(np.array(p)) for p in polys if len(p) > 2]
    def inside(pts):
        pts = np.asarray(pts, float).reshape(-1, 2); par = np.zeros(len(pts), bool)
        for pa in paths: par ^= pa.contains_points(pts)
        return par
    return inside

def scale_regions(w, seed=11):
    rng = random.Random(seed)
    old = {k: w[k] for k in ('trees', 'tufts', 'reeds', 'peaks')}
    # ---- plain position changes ----
    w['geo'] = {k: [_poly(p) for p in v] for k, v in w['geo'].items()}
    for k in ('fwtracks', 'swtracks', 'road', 'southpath', 'ribbons', 'ring', 'link', 'bridge', 'midlink', 'trails'):
        if k in w: w[k] = _poly(w[k])
    for k in ('hach',):
        w[k] = [[*(lambda a: (round(a[0], 3), round(a[1], 3)))(T(h[0], h[1])), *(lambda a: (round(a[0], 3), round(a[1], 3)))(T(h[2], h[3]))] for h in w[k]]
    for k in ('mist', 'darkfog'):
        w[k] = [[*_pt(m[:2]), round(m[2] * math.sqrt(area_scale(m[0], m[1])), 3)] for m in w[k]]
    for m in w['fwmazes']:
        m['poly'] = _poly(m['poly']); cx, cy = T(m['cx'], m['cy']); m['cx'], m['cy'] = round(cx, 3), round(cy, 3)
    for b in w['buildings']:
        x, y = T(b['x'], b['y']); b['x'], b['y'] = round(x, 3), round(y, 3)
    mar = w['marina']; x, y = T(mar['x'], mar['y']); mar['x'], mar['y'] = round(x, 3), round(y, 3); mar['pier'] = _vline(mar['pier'])
    mt = w['mountain']; x, y = T(mt['x'], mt['y']); mt['x'], mt['y'] = round(x, 3), round(y, 3); mt['cave'] = _pt(mt['cave'])
    w['crumbling'] = _vline(w['crumbling'])
    for k in ('elm', 'precarious', 'bigtree', 'gallows'):
        if w.get(k): w[k] = _pt(w[k])
    for k in ('label', 'fwlabel', 'sglabel', 'midlabel'):
        w[k] = _label(w[k])
    ll = w['lakelabel']; x, y = T(ll['x'], ll['y']); ll['x'], ll['y'] = round(x, 3), round(y, 3)
    w['track'] = {k: _pt(v) for k, v in (w.get('track') or {}).items()}
    for p in w['places']:
        p['path'] = _poly(p['path'])
        if p.get('segs'): p['segs'] = _poly(p['segs'])
    for k in ('hills', 'thorns'):
        w[k] = [_pt(h) for h in w[k]]

    # ---- sprites: move them, then thin or top up so the density looks the same ----
    lines = []
    for k in ('fwtracks', 'swtracks'):
        lines += w[k]
    lines += [w['road'], w['southpath'], w['link']] + w['ring']
    pts = []
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / 0.25))
            pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    ptree = cKDTree(np.array(pts))
    rib = []
    for r in w['ribbons']:
        for a, b in zip(r[:-1], r[1:]):
            n = max(1, int(math.dist(a, b) / 0.3)); rib += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    rtree = cKDTree(np.array(rib))
    on_land = _even_odd(w['geo']['land']); in_water = _even_odd(w['geo']['water'])
    mazes = [Path(np.array(m['poly'])) for m in w['fwmazes']]
    stats = {}
    for k, items in old.items():
        out, cand = [], []
        for it in items:
            d = area_scale(it[0], it[1])
            nx, ny = T(it[0], it[1]); moved = [round(nx, 3), round(ny, 3)] + list(it[2:])
            if d < 0.98:
                if rng.random() <= d: out.append(moved)
            else:
                out.append(moved)
                if d > 1.02:
                    extra = d - 1; n = int(extra) + (1 if rng.random() < extra - int(extra) else 0)
                    for _ in range(n):
                        r = rng.uniform(0.3, 1.1); a = rng.uniform(0, 2 * math.pi)
                        dup = [round(nx + r * math.cos(a), 3), round(ny + r * math.sin(a), 3), round(it[2] * rng.uniform(0.85, 1.1), 3)] + list(it[3:4]) + [rng.randint(0, 2)]
                        cand.append(dup)
        added = 0
        if cand:
            xy = np.array([c[:2] for c in cand])
            ok = on_land(xy) & ~in_water(xy)
            ok &= ptree.query(xy)[0] > 0.55
            ok &= rtree.query(xy)[0] > 0.9
            for mz in mazes: ok &= ~mz.contains_points(xy)
            out += [c for c, g in zip(cand, ok) if g]; added = int(ok.sum())
        w[k] = out; stats[k] = (len(items), len(out), added)
    pts = np.array([p for poly in w['geo']['land'] for p in poly])
    w['bounds'] = [int(pts[:, 0].min()) - 3, int(pts[:, 1].min()) - 3, int(pts[:, 0].max()) + 3, int(pts[:, 1].max()) + 3]
    return w, stats
