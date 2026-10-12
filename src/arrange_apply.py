"""Apply an arrangement made in the map arranger (move / resize whole pieces) to the finished map data.

Every point, trail, marker and label goes with the piece it sits in. Painted ground that spans several pieces (the land, the
big terrain shapes) is split by piece, moved, and joined again so there are no seams. Trees, grass and the like keep their
size; where a piece is made smaller or larger they are thinned or topped up so the woods keep the same look.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure
from matplotlib.path import Path
import partition as P, lake_reshape as L

R8 = 8


class Arr:
    def __init__(self, w, arr):
        self.strip = w.get('strip') or L.STRIP
        self.pieces, self.owner = P.build(w, self.strip)                  # same pieces as the arranger shows
        self.ids = [p[0] for p in self.pieces]
        pj = {p['id']: p for p in P.pieces_json(w, self.strip)}
        self.tf = {}
        for i, pid in enumerate(arr['ids']):
            if pid not in pj: continue
            b = pj[pid]['box']; ax, ay = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            self.tf[pid] = dict(ax=ax, ay=ay, tx=arr['tx'][i], ty=arr['ty'][i], s=arr['s'][i])
        self.moved = {pid: t for pid, t in self.tf.items() if abs(t['tx']) + abs(t['ty']) > 1e-6 or abs(t['s'] - 1) > 1e-6}

    def piece_at(self, x, y):
        ix, iy = int((x - P.X0) * P.RES), int((y - P.Y0) * P.RES)
        if 0 <= ix < P.W and 0 <= iy < P.H:
            k = self.owner[iy, ix]
            if k >= 0: return self.ids[k]
        return None

    def own(self, x, y, kind):
        pid = self.piece_at(x, y)
        if pid == 'lake': pid = {'fw': 'woods', 'forest': 'forest'}.get(kind, pid)
        return pid

    def T(self, x, y, pid=None):
        pid = pid or self.piece_at(x, y)
        t = self.moved.get(pid)
        if not t: return x, y
        return t['ax'] + t['tx'] + t['s'] * (x - t['ax']), t['ay'] + t['ty'] + t['s'] * (y - t['ay'])

    def scale_at(self, x, y):
        t = self.moved.get(self.piece_at(x, y)); return t['s'] if t else 1.0


def _pt(A, p):
    x, y = A.T(p[0], p[1]); return [round(x, 3), round(y, 3)] + list(p[2:])


def _is_pt(v): return isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(q, (int, float)) for q in v)


def _poly(A, v, kind=None):
    if _is_pt(v):
        x, y = A.T(v[0], v[1], A.own(v[0], v[1], kind) if kind else None); return [round(x, 3), round(y, 3)] + list(v[2:])
    if isinstance(v, list): return [_poly(A, q, kind) for q in v]
    return v


# ---------- painted ground: split by piece, move, join ----------
def _raster(polys, x0, y0, W, H):
    m = np.zeros((H, W), bool)
    for poly in polys:
        pts = [((x - x0) * R8, (y - y0) * R8) for x, y in poly]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        bx0, by0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1); bx1, by1 = min(W, int(max(xs)) + 2), min(H, int(max(ys)) + 2)
        if bx1 <= bx0 or by1 <= by0: continue
        img = Image.new('1', (bx1 - bx0, by1 - by0), 0)
        ImageDraw.Draw(img).polygon([(x - bx0, y - by0) for x, y in pts], fill=1)
        m[by0:by1, bx0:bx1] ^= np.array(img, bool)
    return m


def _contours(mask, x0, y0, sigma=1.5, tol=0.5, minarea=0.4):
    out = []
    for c in measure.find_contours(ndi.gaussian_filter(np.pad(mask.astype(float), 1), sigma), 0.5):
        if len(c) < 6: continue
        c = measure.approximate_polygon(c, tol)
        pts = [[round((x - 1) / R8 + x0, 3), round((y - 1) / R8 + y0, 3)] for y, x in c[:-1]]
        a = 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))))
        if a >= minarea: out.append(pts)
    return out


def _layer(A, polys, seal=False):
    allp = np.array([q for p in polys for q in p])
    lo, hi = allp.min(0) - 3, allp.max(0) + 3
    box = [lo[0], lo[1], hi[0], hi[1]]
    for pid, t in A.moved.items():                                # leave room for where the moved pieces end up
        b = [(0, 0)]
    xs, ys = [box[0], box[2]], [box[1], box[3]]
    for pid, t in A.moved.items():
        pj = next(p for p in A._pj if p['id'] == pid)
        for cx, cy in ((pj['box'][0], pj['box'][1]), (pj['box'][2], pj['box'][3])):
            nx, ny = t['ax'] + t['tx'] + t['s'] * (cx - t['ax']), t['ay'] + t['ty'] + t['s'] * (cy - t['ay'])
            xs += [nx - 3, nx + 3]; ys += [ny - 3, ny + 3]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    W, H = int((x1 - x0) * R8) + 2, int((y1 - y0) * R8) + 2
    mask = _raster(polys, x0, y0, W, H)
    yy, xx = np.mgrid[0:H, 0:W]; wx = xx / R8 + x0 + .5 / R8; wy = yy / R8 + y0 + .5 / R8
    ix = ((wx - P.X0) * P.RES).astype(int); iy = ((wy - P.Y0) * P.RES).astype(int)
    ok = (ix >= 0) & (ix < P.W) & (iy >= 0) & (iy < P.H)
    own = np.full((H, W), -1, int); own[ok] = A.owner[iy[ok], ix[ok]]
    out = np.zeros((H, W), bool)
    for k, pid in enumerate(A.ids):
        part = mask & (own == k)
        if pid not in A.moved or not part.any():
            out |= part; continue
        t = A.moved[pid]
        sx = t['ax'] + (wx - t['ax'] - t['tx']) / t['s']; sy = t['ay'] + (wy - t['ay'] - t['ty']) / t['s']      # where each new cell came from
        c = (sx - x0) * R8 - .5; r = (sy - y0) * R8 - .5
        src = np.zeros((H, W), bool)
        # the old cells of this piece, kept in a copy that is zero everywhere else
        warped = ndi.map_coordinates(part.astype(float), [r, c], order=1, mode='constant', cval=0.0) > 0.5
        out |= warped
    out |= mask & (own < 0)
    if seal == 'land': out = ndi.binary_closing(np.pad(out, 10), iterations=8)[10:-10, 10:-10]      # seal hairline gaps where pieces meet (up to 2 rooms wide)
    elif seal: out = ndi.binary_closing(out, iterations=2)
    return _contours(out, x0, y0)


def apply_arrangement(w, arr, seed=7):
    A = Arr(w, arr); A._pj = P.pieces_json(w, A.strip)
    if not A.moved: return w, {'moved': {}}
    rng = random.Random(seed)
    stats = {'moved': {k: (round(t['tx'], 2), round(t['ty'], 2), round(t['s'], 3)) for k, t in A.moved.items()}, 'layers': {}}

    # ---- painted ground ----
    new_geo = {}
    for key, polys in w['geo'].items():
        if not polys: new_geo[key] = polys; continue
        owners = {A.piece_at(x, y) for p in polys for x, y in p[::max(1, len(p) // 40)]}
        hit = [o for o in owners if o in A.moved]
        if not hit: new_geo[key] = polys; continue
        if len(owners - {None}) == 1:                              # sits wholly inside one piece: just move it
            pid = next(iter(owners - {None})); new_geo[key] = [[list(A.T(x, y, pid)) for x, y in p] for p in polys]
        else:
            new_geo[key] = _layer(A, polys, seal=('land' if key == 'land' else key == 'water'))
        stats['layers'][key] = len(new_geo[key])
    w['geo'] = new_geo

    # ---- everything drawn as points, lines and shapes goes with its piece ----
    for k in ('fwtracks', 'swtracks', 'road', 'southpath', 'ribbons', 'ring', 'link', 'bridge', 'midlink', 'trails'):
        if k in w: w[k] = _poly(A, w[k], 'fw' if k == 'fwtracks' else 'forest')
    w['hach'] = [[*[round(v, 3) for v in A.T(h[0], h[1], A.own(h[0], h[1], 'forest'))], *[round(v, 3) for v in A.T(h[2], h[3], A.own(h[2], h[3], 'forest'))]] for h in w['hach']]
    for k in ('mist', 'darkfog'):
        w[k] = [[*[round(v, 3) for v in A.T(m[0], m[1], A.own(m[0], m[1], 'forest'))], round(m[2] * A.scale_at(m[0], m[1]), 3)] for m in w[k]]
    for m in w['fwmazes']:
        pid = A.own(m['cx'], m['cy'], 'fw'); m['poly'] = [list(A.T(x, y, pid)) for x, y in m['poly']]; m['cx'], m['cy'] = (round(v, 3) for v in A.T(m['cx'], m['cy'], pid))
    for b in w['buildings']:
        b['x'], b['y'] = (round(v, 3) for v in A.T(b['x'], b['y'], A.own(b['x'], b['y'], 'forest')))
    mar = w['marina']; pid = A.piece_at(mar['x'], mar['y']); mar['x'], mar['y'] = (round(v, 3) for v in A.T(mar['x'], mar['y'], pid))
    px, p0, p1 = mar['pier']; a = A.T(px, p0, pid); b = A.T(px, p1, pid); mar['pier'] = [round((a[0] + b[0]) / 2, 3), round(a[1], 3), round(b[1], 3)]
    mt = w['mountain']; pid = A.piece_at(mt['x'], mt['y']); mt['x'], mt['y'] = (round(v, 3) for v in A.T(mt['x'], mt['y'], pid)); mt['cave'] = [round(v, 3) for v in A.T(*mt['cave'], pid)]
    cr = w['crumbling']
    if cr: a = A.T(cr[0], cr[1]); b = A.T(cr[0], cr[2]); w['crumbling'] = [round((a[0] + b[0]) / 2, 3), round(a[1], 3), round(b[1], 3)]
    for k in ('elm', 'precarious', 'bigtree', 'gallows'):
        if w.get(k): w[k] = _pt(A, w[k])
    for k in ('label', 'fwlabel', 'sglabel', 'midlabel'):
        d = w.get(k)
        if d:
            pid = A.own((d['x0'] + d['x1']) / 2, d['y'], 'fw' if k == 'fwlabel' else 'forest'); a = A.T(d['x0'], d['y'], pid); b = A.T(d['x1'], d['y'], pid)
            w[k] = dict(d, x0=round(a[0], 2), x1=round(b[0], 2), y=round((a[1] + b[1]) / 2, 2))
    ll = w['lakelabel']; ll['x'], ll['y'] = (round(v, 3) for v in A.T(ll['x'], ll['y']))
    w['track'] = {k: _pt(A, v) for k, v in (w.get('track') or {}).items()}
    for p in w['places']:
        kind = 'fw' if p.get('group') == 'fw' else ('lake' if p['name'] == "Lake of Tich'Pyga" else 'forest')
        p['path'] = _poly(A, p['path'], kind)
        if p.get('segs'): p['segs'] = _poly(A, p['segs'], kind)
    for k in ('hills', 'thorns'):
        w[k] = [_pt(A, h) for h in w[k]]

    # ---- trees, grass and the like: move them, then thin or top them up to keep the same density ----
    for k in ('trees', 'tufts', 'reeds', 'peaks'):
        out = []
        for it in w[k]:
            pid = A.piece_at(it[0], it[1]); t = A.moved.get(pid)
            x, y = A.T(it[0], it[1], pid); moved = [round(x, 3), round(y, 3)] + list(it[2:])
            d = (t['s'] ** 2) if t else 1.0
            if d < 0.98:
                if rng.random() <= d: out.append(moved)
            else:
                out.append(moved)
                if d > 1.02:
                    extra = d - 1; n = int(extra) + (1 if rng.random() < extra - int(extra) else 0)
                    for _ in range(n):
                        r = rng.uniform(0.3, 1.1); an = rng.uniform(0, 2 * math.pi)
                        out.append([round(x + r * math.cos(an), 3), round(y + r * math.sin(an), 3), round(it[2] * rng.uniform(0.85, 1.1), 3)] + list(it[3:4]) + [rng.randint(0, 2)])
        w[k] = out

    w['strip'] = [[round(v, 3) for v in A.T(x, y, 'lake')] for x, y in A.strip]
    pts = np.array([q for poly in w['geo']['land'] for q in poly])
    w['bounds'] = [int(pts[:, 0].min()) - 3, int(pts[:, 1].min()) - 3, int(pts[:, 0].max()) + 3, int(pts[:, 1].max()) + 3]
    return w, stats
