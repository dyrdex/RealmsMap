"""Sub-areas that open off the Northern Trade Route: the City of Salburg, the Keep of Belial and the Wolf's Den.
Each gets a short dirt link from the road (with an off-ramp pad where it leaves), a marker with your directions on its card, and a graphic:
the City of Salburg is drawn with the same walled-town emblem as Ofcol, in forest east of the Maze of Trees (the old indent in the coast is filled with forest, and the coast runs straight down past it to a small bay for Ocean Keep);
the Keep of Belial is a medieval keep tower at the end of the spacer-room stub below the road (the way your directions go)."""
import math
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import arrange_apply as AA
import gap_fill as GF

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8
GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."


def _nearest_on(lines, p):
    best = None
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
            t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
            q = (a[0] + t * dx, a[1] + t * dy); d = math.dist(p, q)
            if best is None or d < best[0]: best = (d, q)
    return best[1]


def _smooth(pts, sigma=0.8):
    if len(pts) < 4: return [list(map(lambda v: round(v, 2), p)) for p in pts]
    xs = ndi.gaussian_filter1d(np.array([p[0] for p in pts]), sigma, mode='nearest'); ys = ndi.gaussian_filter1d(np.array([p[1] for p in pts]), sigma, mode='nearest')
    q = [[float(a), float(b)] for a, b in zip(xs, ys)]; q[0] = list(pts[0]); q[-1] = list(pts[-1])
    return [[round(a, 2), round(b, 2)] for a, b in q]


def _line_samples(pts, step=0.2):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.dist(a, b) / step)); out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    return np.array(out)


def add_ntr_subareas(w, layout, routes, seed=9):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    road = w['ntrroad']
    track = w.get('track', {})
    rng = np.random.default_rng(seed)
    # where the two places sit
    SALBURG = (43.2, -44.6)                                                       # east of the Maze of Trees, in the forest (a little north of where it was)
    s4112 = pos[4112]; BELIAL = (s4112[0] - 1.0, s4112[1] + 1.0)                  # the Belial room lies south-west of the last spacer room of the stub
    WOLF = (8.3, -22.9)                                                            # east of the turn-off room 4065, the way the directions' last step ('e') goes, just south of the road (owner, Oct 15: it sat north of the road before)
    sites = {'City of Salburg': SALBURG, 'Keep of Belial': BELIAL, "The Wolf's Den": WOLF}
    links = {}
    r4098 = pos[4098]
    P = _nearest_on(road, r4098)                                                  # the off-ramp pad: the link starts exactly on it
    # a gentle curve (not a straight line): it leaves the pad heading east, bows a little to the south, then rises to the city
    P1 = (P[0] + 3.4, P[1] + 1.9); P2 = (SALBURG[0] - 3.0, SALBURG[1] + 2.1)
    bez = []
    for k in range(25):
        u = k / 24.0; a_, b_, c_, d_ = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        bez.append([round(a_ * P[0] + b_ * P1[0] + c_ * P2[0] + d_ * SALBURG[0], 2), round(a_ * P[1] + b_ * P1[1] + c_ * P2[1] + d_ * SALBURG[1], 2)])
    links['City of Salburg'] = bez
    links["The Wolf's Den"] = _smooth([pos[4065], (7.6, -23.15), WOLF], 0.7)
    stub = [pos[4104], pos[19637], pos[5297], pos[4112], BELIAL]
    links['Keep of Belial'] = _smooth(stub, 0.9)
    # the coast: it comes straight down from the Forgotten Woods' north-east coast past the City of Salburg, then bends in to a small bay for Ocean Keep.
    # Everything west of it that is now open water is filled with forest (the ground and trees of the land around it).
    import random
    from gap_fill import _populate
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    y, x = GF.WY, GF.WX
    from bay import bay_mask
    wob = 0.28 * np.sin(1.7 * y + 0.4) + 0.18 * np.sin(3.9 * y + 1.1)
    tt = np.clip((y + 43.6) / 1.4, 0, 1); sm = 0.5 - 0.5 * np.cos(np.pi * tt)
    xmax = 53.5 + (51.5 - 53.5) * sm + wob * (1 - sm)                                  # the straight coast (x = 53.5), curving west into the top of the bay
    fill = (x > 38.0) & (x < xmax) & (y > -61.0) & (y < -33.0) & ~bay_mask(x, y) & ~land & ~water   # the indent east of the maze only (x from 38): outside the bay, it becomes forest
    new_land = land | fill
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    touched, added = _populate(w, [('Salburg forest', fill)], land, random.Random(seed))   # ground tints, trees and grass like the land around it
    ash = AA._raster(w['geo']['ash'], X0, Y0, W, H)                                    # the southern part takes on the Ashen Forest's grey ground
    noise = ndi.gaussian_filter(rng.normal(size=(H, W)), 1.6 * R8); noise = (noise - noise.min()) / (noise.max() - noise.min())
    south = fill & (y > -37.6 + 2.4 * (noise - 0.5))                                   # only a soft strip beside the Ashen Forest's own edge
    w['geo']['ash'] = AA._contours(ash | ndi.binary_dilation(south, iterations=2), X0, Y0, sigma=2.0)
    # the links (dirt), the off-ramp pads where they leave the road, and nothing growing on them
    w['fwtracks'] = list(w['fwtracks']) + [links['City of Salburg'], links['Keep of Belial'], links["The Wolf's Den"]]
    joins = list(w.get('ntrjoins', []))
    for r in (4098, 4104, 4065):
        p = _nearest_on(road, pos[r]); joins.append([round(p[0], 2), round(p[1], 2)])
    w['ntrjoins'] = joins
    ls = np.vstack([_line_samples(l) for l in links.values()]); lt = cKDTree(ls)
    for key in ('trees', 'tufts', 'hills', 'thorns'):
        w[key] = [q for q in w[key] if lt.query([q[0], q[1]])[0] > 0.6]
    rs = np.vstack([_line_samples(l) for l in road]); rt = cKDTree(rs)
    sp = np.array(list(sites.values())); st = cKDTree(sp)
    for key in ('trees', 'tufts', 'hills', 'thorns'):
        w[key] = [q for q in w[key] if rt.query([q[0], q[1]])[0] > 1.15 and st.query([q[0], q[1]])[0] > 1.5]
    # the markers, with your directions
    placed = []
    for r in routes:
        name = r['name']; last = r['last_road']
        trail = r['trail']; idx = len(trail) - 1 - [q[0] for q in trail][::-1].index(last); trail = trail[:idx + 1]       # the route as far as the road room where it leaves
        segs = []; cur = []
        for v, area, static in trail:
            p = pos.get(v) or (track.get('cx' + str(v)) and tuple(track['cx' + str(v)][:2])) or static
            if p: cur.append([round(p[0], 3), round(p[1], 3)])
            elif cur: segs.append(cur); cur = []
        link = links[name]
        cur = (cur or []) + [list(q) for q in link]
        segs.append(cur)
        pl = dict(name=name, route=r['route'], room=r.get('room') or 'the road', dir='here', path=[q for s in segs for q in s], segs=segs, group='af',
                  where='off the Northern Trade Route', note=None if len(segs) == 1 else GAP_NOTE)
        if name == 'City of Salburg': pl['kind'] = 'town'                          # drawn with the same walled-town emblem as Ofcol
        w['places'].append(pl); placed.append((name, tuple(round(v, 1) for v in sites[name])))
    w['gfx'] = list(w.get('gfx', [])) + [dict(k='keep', label='Keep of Belial', at='above-pin', w=2.3, h=3.5, dx=-0.95)]
    return w, dict(placed=placed, joins_added=3, forest_filled=round(float(fill.sum()) / R8 / R8, 1), planted=added, tints_extended=touched)
