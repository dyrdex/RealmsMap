"""The far east of the Ashen Forest turns into a beach and then the ocean.

Where the shore lies comes from your layout: the east-west paths that run out from the long north-south beach path (around x = 61) to
dead-ends. Midway along each of those paths the land becomes water. Between those midpoints the shoreline is smooth, with a little
natural wobble, and it eases back into the existing coast at its north and south ends.
 * the land east of the shoreline is cut away (it is the ocean);
 * a strip of sand runs along the shore on the land side (your north-south paths lie on it);
 * the forest thins out over the last few rooms before the sand, and no trees grow on the sand or in the water;
 * a pale wash of shallow water lies along the shore.
Trails and rooms are left exactly as they are.
"""
import math, random
import numpy as np
from collections import defaultdict
from scipy import ndimage as ndi
import arrange_apply as AA
import gap_fill as GF

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8
BEACH_W = 3.4          # width of the sand
THIN_W = 5.8           # width of the band where the forest thins out
SHALLOWS_W = 2.8       # the pale water along the shore
BEACH_PATH_X = 60.5    # the east-west paths that count start from the north-south beach path, at or east of this x


def shore_points(layout, edges):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys']))); hid = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    G = defaultdict(set)
    for a, b, k in edges['edges']:
        if k == 'ud' or a in hid or b in hid or a not in pos or b not in pos: continue
        G[a].add(b); G[b].add(a)
    seen = set(); out = []
    for v in [v for v in G if len(G[v]) != 2] + list(G):
        for u in G[v]:
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            for a, b in ((ch[0], ch[-1]), (ch[-1], ch[0])):                  # b is the dead end
                if len(G[b]) == 1 and not info[b]['fixed'] and pos[b][0] > 58 and pos[a][0] >= BEACH_PATH_X:
                    pa, pb = pos[a], pos[b]
                    if abs(pb[0] - pa[0]) >= abs(pb[1] - pa[1]): out.append(((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, b))
    uniq = {}
    for x, y, b in out: uniq[b] = (x, y)
    return sorted((y, x) for x, y in uniq.values())


def add_east_beach(w, layout, edges, seed=5):
    rng = random.Random(seed)
    pts = shore_points(layout, edges)                                    # (y, x) midpoints, north to south
    ys = np.array([p[0] for p in pts]); xs = np.array([p[1] for p in pts])
    y0, y1 = float(ys.min()), float(ys.max())
    # the shoreline x at every row: the midpoints, joined smoothly, a gentle wobble, easing out to the old coast at both ends
    gy = np.arange(Y0, Y0 + H / R8, 1 / R8) + 0.5 / R8
    sx = np.interp(gy, ys, xs)
    sx = ndi.gaussian_filter1d(sx, 1.1 * R8, mode='nearest')
    sx = sx + 0.30 * np.sin(1.9 * gy + 0.6) + 0.20 * np.sin(4.1 * gy + 2.0)
    out = np.where(gy < y0, (y0 - gy) * 1.0, np.where(gy > y1, (gy - y1) * 1.0, 0.0))
    shore = sx + out                                                     # the shoreline x for each row (it runs off to the east at the ends)
    SHORE = np.broadcast_to(shore[:, None], (H, W))
    region = (GF.WX > 55) & (GF.WY > y0 - 9) & (GF.WY < y1 + 9)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    cut = region & (GF.WX > SHORE) & land
    new_land = land & ~cut
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    # sand along the shore, on the land side
    beach = new_land & region & (GF.WX > SHORE - BEACH_W - 0.35 * np.sin(2.3 * GF.WY + 1.0))
    w['geo']['sand'] = list(w['geo']['sand']) + AA._contours(beach, X0, Y0, sigma=1.5)
    # the grey tint and the shallows
    ash = AA._raster(w['geo']['ash'], X0, Y0, W, H) & new_land & ~beach
    w['geo']['ash'] = AA._contours(ash, X0, Y0, sigma=2.0)
    dist = ndi.distance_transform_edt(~new_land) / R8                      # rooms from the nearest land
    beyond = np.where(GF.WY < y0, y0 - GF.WY, np.where(GF.WY > y1, GF.WY - y1, 0.0))
    fade = np.clip(1 - beyond / 4.0, 0, 1)                                  # the wash fades out over 4 rooms past the last path, so it never trails off into open sea
    shallow = region & ~new_land & ~water & (dist <= SHALLOWS_W * fade) & (GF.WX > SHORE - 0.6) & (fade > 0.05)
    w['geo']['shallows'] = AA._contours(shallow, X0, Y0, sigma=2.0)
    # the forest thins out toward the sand; nothing grows on the sand or in the water
    def thin(arr, keep_prob_fn):
        keep = []
        for q in arr:
            if not (55 < q[0] < 100 and y0 - 9 < q[1] < y1 + 9): keep.append(q); continue
            i = int((q[1] - Y0) * R8); s = shore[i] if 0 <= i < len(shore) else 99
            d = s - q[0]                                                  # rooms from the shoreline (negative = in the water)
            if d < BEACH_W: continue                                      # on the sand or in the water: removed
            if d < BEACH_W + THIN_W and rng.random() > keep_prob_fn((d - BEACH_W) / THIN_W): continue
            keep.append(q)
        return keep
    n_before = {k: len(w[k]) for k in ('trees', 'tufts', 'hills', 'thorns')}
    for k in n_before: w[k] = thin(w[k], lambda t: t ** 1.4)              # t = 0 at the sand, 1 at the inland edge of the band
    return w, dict(stubs=len(pts), shoreline_x=(round(float(shore[int((y0 - Y0) * R8)]), 1), round(float(sx.min()), 1), round(float(sx.max()), 1)), land_cut=round(float(cut.sum()) / R8 / R8, 1),
                   sand=round(float(beach.sum()) / R8 / R8, 1), removed={k: n_before[k] - len(w[k]) for k in n_before})
