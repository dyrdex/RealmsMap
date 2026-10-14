"""The sea along the whole west coast (owner, Oct 13): open water west of every west-facing coast of the map, from the Forest of Tears
up round the Forgotten Woods, the Barren Peaks and the Northern Plains, joined to the sea that is already there; and a small wooden
shack with a dock reaching out into it at about (-94.3, -16.4).
Bounded (gotcha 1): only non-land cells connected to the map's edge, within REACH rooms of the land, that lie WEST of the nearest land point, clear of
markers, paths and the other drawings; smoothed so it tapers where a coast turns away. It is united with the water it touches so no seam line is drawn.
Runs last of the land changes (after ft_merge) on the taller grid (Y0 -215) the Plains and Azure merges use."""
import math
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _samples

X0, W, R8 = GF.X0, GF.W, GF.R8
YN = -215.0; HN = int((GF.Y1 - YN) * R8)
REACH = 9.0                                  # rooms of sea off the coast (the Azure and Plains seas reach 8-9)
DOCK_AT = (-94.3, -16.4)                     # owner: the small wooden marina


def add_west_sea(w, seed=61):
    nrng = np.random.default_rng(seed)
    HN = int((max(GF.Y1, w['bounds'][3]) - YN) * R8)                    # (the grid reaches the map's south edge: the Southern Mountain Range's west coast gets its sea too)
    land = AA._raster(w['geo']['land'], X0, YN, W, HN)
    water = AA._raster(w['geo']['water'], X0, YN, W, HN)
    xs = (np.arange(W) + .5) / R8 + X0; ys = (np.arange(HN) + .5) / R8 + YN
    SX = np.broadcast_to(xs[None, :], (HN, W))
    # open water: non-land connected to the edge of the grid
    lab, n = ndi.label(~land)
    border = np.unique(np.r_[lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]); border = border[border > 0]
    ext = np.isin(lab, border)
    d, (iy, ix) = ndi.distance_transform_edt(~land, return_indices=True)
    d = d / R8
    west_of = SX < (xs[ix] - 0.15)                                            # west of the nearest land point: only coasts that face west
    reach = np.full(d.shape, REACH)
    # the region of west-facing coast, smoothed (so no ragged fingers where a coast turns), then bounded to REACH rooms off the land
    core = ext & west_of & (d <= REACH) & (d >= 0.15)
    region = ndi.gaussian_filter(core.astype(float), 2.0 * R8) > 0.30
    bw = ndi.gaussian_filter(nrng.normal(size=d.shape), 4.0 * R8); bw = (bw - bw.min()) / (bw.max() - bw.min())
    reach = REACH * (0.85 + 0.3 * bw)                                         # the sea is 7.6 to 10.4 rooms wide, gently varying
    sea = ext & region & (d >= 0.15) & (d <= reach)
    # keep clear of markers and of every drawn path and building
    keep = []
    for p in w['places']:
        keep.append(p['path'][-1][:2])
    keep += [[b['x'], b['y']] for b in w.get('buildings', [])]
    pts = np.array(keep, float)
    lines = []
    for key in ('fwtracks', 'swtracks', 'etrtracks', 'dirtroads', 'ashtracks'):
        lines += [t for t in (w.get(key) or []) if len(t) > 1]
    blocked = np.zeros(d.shape, bool)
    def stamp(P, r):
        for x, y in P:
            cx, cy = int((x - X0) * R8), int((y - YN) * R8)
            if not (0 <= cx < W and 0 <= cy < HN): continue
            rr = int(r * R8) + 1; y0, y1, x0, x1 = max(0, cy - rr), min(HN, cy + rr + 1), max(0, cx - rr), min(W, cx + rr + 1)
            yy, xx = np.ogrid[y0:y1, x0:x1]; blocked[y0:y1, x0:x1] |= ((yy - cy) ** 2 + (xx - cx) ** 2) <= rr * rr
    stamp(pts, 1.3); stamp(_samples(lines, 0.35), 0.7) if lines else None
    sea &= ~blocked
    sea = (ndi.gaussian_filter(sea.astype(float), 0.8 * R8) > 0.5) & ext & (d >= 0.15) & ~blocked
    lab2, n2 = ndi.label(sea)
    if n2:                                                                    # one sea along the coast: no stray pools (a piece stays if it is big or touches the water already there)
        sz = ndi.sum(sea, lab2, range(1, n2 + 1)) / R8 / R8
        touch = ndi.sum(ndi.binary_dilation(water, iterations=3), lab2, range(1, n2 + 1)) > 0
        sea = np.isin(lab2, [i + 1 for i, s in enumerate(sz) if s >= 300.0 or (touch[i] and s >= 4.0)])
    new = sea & ~water
    # unite with the water it touches (one shape: no seam line between old and new water)
    polys = w['geo']['water']; near = ndi.binary_dilation(new, iterations=4)
    sel, keepp = [], []
    for p in polys:
        r = AA._raster([p], X0, YN, W, HN)
        (sel if (r & near).any() else keepp).append(p)
    merged = (AA._raster(sel, X0, YN, W, HN) if sel else np.zeros((HN, W), bool)) | new
    w['geo']['water'] = keepp + AA._contours(merged, X0, YN, sigma=1.5)
    # nothing stands in the new water, and no ground tint runs out over it
    m = ndi.binary_dilation(new, iterations=int(0.25 * R8))
    cleared = {}
    for key in ('trees', 'tufts', 'reeds', 'hills', 'thorns', 'boulders', 'peaks', 'crags', 'ripples', 'wheattufts', 'brush'):
        arr = w.get(key) or []; kept = []
        for q in arr:
            ix_, iy_ = int((q[0] - X0) * R8), int((q[1] - YN) * R8)
            if 0 <= ix_ < W and 0 <= iy_ < HN and m[iy_, ix_]: continue
            kept.append(q)
        if len(kept) != len(arr): cleared[key] = len(arr) - len(kept); w[key] = kept
    for key, ps in list(w['geo'].items()):
        if key in ('land', 'water') or not ps: continue
        r = AA._raster(ps, X0, YN, W, HN)
        if (r & new).any(): w['geo'][key] = AA._contours(r & ~new, X0, YN, sigma=1.0)
    info = dict(sea_new_sq=round(float(new.sum()) / R8 / R8, 1), bodies=int(ndi.label(new)[1]), joined_water_polys=len(sel), cleared=cleared)

    # ---- the shack and dock at DOCK_AT: the shore point is the land edge nearest it; the dock reaches out along the way to the sea
    px, py = DOCK_AT
    cx, cy = int((px - X0) * R8), int((py - YN) * R8)
    rr = int(3.5 * R8); y0, y1, x0, x1 = cy - rr, cy + rr + 1, cx - rr, cx + rr + 1
    seg = sea[y0:y1, x0:x1]
    if seg.any():
        sy, sx = np.nonzero(seg)
        scx, scy = sx.mean() + x0, sy.mean() + y0                             # where the sea lies, round the spot
        vx, vy = (scx - cx), (scy - cy); L = math.hypot(vx, vy) or 1.0; vx, vy = vx / L, vy / L
        # walk from the spot toward the sea until the first sea cell: that is the shore
        t = 0.0; shore = None
        while t < 6.0:
            x_, y_ = px + vx * t, py + vy * t; ix_, iy_ = int((x_ - X0) * R8), int((y_ - YN) * R8)
            if sea[iy_, ix_]: shore = (x_, y_); break
            t += 0.05
        if shore:
            length = 0.0
            while length < 3.4:                                              # as far out as the sea goes (keeping 0.7 rooms in hand)
                x_, y_ = shore[0] + vx * (length + 0.05), shore[1] + vy * (length + 0.05)
                ix_, iy_ = int((x_ - X0) * R8), int((y_ - YN) * R8)
                if not sea[iy_, ix_]: break
                length += 0.05
            length = max(1.6, min(3.4, length - 0.7))
            sx_, sy_ = shore[0] - vx * 0.15, shore[1] - vy * 0.15            # the dock starts just on land
            w['docks'] = list(w.get('docks', [])) + [dict(x=round(sx_, 3), y=round(sy_, 3), a=round(math.degrees(math.atan2(vy, vx)), 1), len=round(length, 2))]
            info['dock'] = w['docks'][-1]
            hx, hy = shore[0] - vx * 1.3, shore[1] - vy * 1.3                     # nothing grows under the shack or on the dock's landing
            for key in ('trees', 'tufts'):
                w[key] = [q for q in w[key] if not (abs(q[0] - hx) < 0.9 and abs(q[1] - hy) < 0.8)]
    return w, info
