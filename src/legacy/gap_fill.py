"""Fill the gaps that moving the pieces left behind.

Each gap is a region of sea. It becomes either lake water or land, and land gets the same ground tints, trees and grass as the
land around it (taken from a ring just outside the gap), so it reads as ordinary forest or grassland.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure
from matplotlib.path import Path
import partition as P
import arrange_apply as AA

R8 = 8
X0, X1, Y0, Y1 = -130.0, 96.0, -118.0, 42.0          # (the east edge was 66; the merged Ashen Forest reaches x = 73)
W, H = int((X1 - X0) * R8), int((Y1 - Y0) * R8)
yy, xx = np.mgrid[0:H, 0:W]; WX = xx / R8 + X0 + .5 / R8; WY = yy / R8 + Y0 + .5 / R8

TINTS = ['meadow1', 'meadow2', 'meadow3', 'fill', 'fill2', 'sparse', 'deep', 'bog', 'sg', 'sg2', 'fwwood', 'fwplain', 'sand']


def _wave(x, a, k, ph): return a * math.sin(k * x + ph)


# the line where the lake meets the Woods: the lake's north shore, at the bottom of the Lost in the Swamp maze
def north_shore(x): return -40.7 + _wave(x, 0.8, 0.55, 0.4) + _wave(x, 0.5, 1.3, 2.0)


def _line(f, x0, x1, step=1.0):
    n = int((x1 - x0) / step); return [(x0 + i * step, f(x0 + i * step)) for i in range(n + 1)]


def regions():
    ns = _line(north_shore, -42, -19.3)
    return [
        # --- lake water ---
        dict(name='lake: its north and north-east, up to the maze and the Woods trail', kind='water',
             poly=ns + [(-19.3, -24), (-42, -24)]),
        dict(name='lake: its south-west corner, toward Ezard\'s Fields and The Shire', kind='water',
             poly=[(-35, -14.2), (-20.2, -14.2), (-20.2, -2.0), (-35, -2.0)]),
        # --- ground ---
        dict(name='the bay north of the lake (Woods ground)', kind='land',
             poly=[(-41.4, -51.5), (-19.3, -51.5)] + list(reversed(ns)) + [(-41.4, -40.7)]),
        dict(name='the gap by Keep of Lomar and Ofcol', kind='land',
             poly=[(-21.5, -25), (-13.5, -25), (-13.5, -15.5), (-21.5, -15.5)]),
        dict(name='between the lake and Darkhaven', kind='land',
             poly=[(-16, -13), (-8.3, -13), (-8.3, 3.9), (-16, 3.9)]),
        dict(name='between Along the Forest Path and the forest', kind='land',
             poly=[(-25, 3.8), (-17.3, 3.8), (-17.3, 15.5), (-14.2, 15.5), (-14.2, 25.3), (-17, 26.6), (-21, 26.4), (-25, 25.8)]),
    ]


def _fillpoly(poly):
    img = Image.new('1', (W, H), 0)
    ImageDraw.Draw(img).polygon([((x - X0) * R8, (y - Y0) * R8) for x, y in poly], fill=1)
    return np.array(img, bool)



def _populate(w, fills, land, rng):
    """Give new patches of land the ground tints, trees and grass of the land around them. Returns (tints, sprites_added)."""
    # --- ground tints: extend the tints that surround each new patch of land into it ---
    geo = dict(w['geo']); touched = set()
    layer_masks = {k: AA._raster(geo[k], X0, Y0, W, H) for k in TINTS if geo.get(k)}
    for name, m in fills:
        ring = ndi.binary_dilation(m, iterations=12) & ~ndi.binary_dilation(m, iterations=2) & land
        if not ring.any(): continue
        for k, lm in layer_masks.items():
            if lm[ring].mean() >= 0.35:
                layer_masks[k] = lm | ndi.binary_dilation(m, iterations=3); touched.add(k)
    for k in touched: geo[k] = AA._contours(layer_masks[k], X0, Y0)
    w['geo'] = geo

    # --- trees and grass in the new ground, matching what is around it ---
    lines = []
    for k in ('fwtracks', 'swtracks'): lines += w[k]
    lines += [w['road'], w['southpath'], w['link']] + list(w['ring'])
    pts = []
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / 0.25)); pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    from scipy.spatial import cKDTree
    ptree = cKDTree(np.array(pts))
    added = {}
    for key in ('trees', 'tufts'):
        arr = w[key]; xy = np.array([[a[0], a[1]] for a in arr]); new = []
        ix = ((xy[:, 0] - X0) * R8).astype(int); iy = ((xy[:, 1] - Y0) * R8).astype(int)
        okc = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
        for name, m in fills:
            ring = ndi.binary_dilation(m, iterations=20) & ~ndi.binary_dilation(m, iterations=2) & land
            area = m.sum() / R8 / R8
            if area < 1 or not ring.any(): continue
            near = np.zeros(len(arr), bool); near[okc] = ring[iy[okc], ix[okc]]
            ref = [arr[i] for i in np.nonzero(near)[0]]
            if not ref: continue
            n_new = int(len(ref) / (ring.sum() / R8 / R8) * area)           # same density as the land around it
            inner = m & ~ndi.binary_dilation(~m, iterations=2)
            ys, xs = np.nonzero(inner)
            if not len(xs): continue
            got = 0
            for _ in range(n_new * 4):
                if got >= n_new: break
                j = rng.randrange(len(xs)); x = xs[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = ys[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
                if ptree.query([x, y])[0] < 0.55: continue
                a = rng.choice(ref); sc = round(a[2] * rng.uniform(0.9, 1.1), 3)
                new.append([round(x, 3), round(y, 3), sc] + (list(a[3:4]) + [rng.randint(0, 2)] if key == 'trees' else []))
                got += 1
        added[key] = len(new); w[key] = arr + new
    return sorted(touched), added


def fill_gaps(w, seed=21):
    rng = random.Random(seed)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    sea = ~land & ~water
    new_land, new_water = land.copy(), water.copy()
    info = []
    fills = []
    for r in regions():
        m = _fillpoly(r['poly']) & sea
        if r['kind'] == 'water':
            new_water |= ndi.binary_dilation(m, iterations=3)       # a touch over the shore, so the old coast line is covered
        else:
            new_land |= m; fills.append((r['name'], m))
        info.append((r['name'], r['kind'], round(float(m.sum()) / R8 / R8, 1)))
    new_land |= ndi.binary_dilation(new_water, iterations=2)                                       # the lake's shore is always land
    new_water = ndi.binary_fill_holes(ndi.binary_closing(new_water, iterations=5))        # no thin ridges of land inside the lake

    touched, added = _populate(w, fills, land, rng)
    geo = dict(w['geo'])
    geo['land'] = AA._contours(new_land, X0, Y0)
    geo['water'] = AA._contours(new_water, X0, Y0, sigma=2.0)
    w['geo'] = geo
    # --- nothing grows (or hangs) on the water ---
    wpaths = [Path(np.array(p)) for p in w['geo']['water']]
    def on_water(pt_list, margin=0.3):
        pts_ = np.asarray(pt_list, float).reshape(-1, 2); res = np.zeros(len(pts_), bool)
        for pa in wpaths: res |= pa.contains_points(pts_, radius=-margin)
        return res
    cleared = {}
    for key in ('trees', 'tufts', 'reeds', 'hills', 'thorns', 'peaks', 'darkfog', 'mist'):
        arr = w[key]
        if not arr: continue
        m = on_water([[a_[0], a_[1]] for a_ in arr]); cleared[key] = int(m.sum()); w[key] = [a_ for a_, g_ in zip(arr, m) if not g_]
    # --- the lake's name, now in the middle of the bigger lake ---
    dist = ndi.distance_transform_edt(new_water)
    jy, ix = np.unravel_index(int(np.argmax(np.where(WY < -26, dist, 0))), dist.shape)
    ll = w['lakelabel']; ll['x'], ll['y'] = round(float(WX[jy, ix]) + 0.8, 2), round(float(WY[jy, ix]), 2)
    pts_ = np.array([q for poly in w['geo']['land'] for q in poly])
    w['bounds'] = [int(pts_[:, 0].min()) - 3, int(pts_[:, 1].min()) - 3, int(pts_[:, 0].max()) + 3, int(pts_[:, 1].max()) + 3]
    return w, dict(regions=info, tints_extended=touched, sprites_added=added, cleared_from_water=cleared)


def trim_lake_from_road(w, min_dist=3.2, box=(-38.0, -14.0, -18.0, 3.5), seed=33):
    """Between Ezard's Fields and The Shire the lake came right up to the Western Trade Route. Pull the shore back so it is at
    least `min_dist` rooms from the road there, and give the freed ground the forest terrain around it."""
    rng = random.Random(seed)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    img = Image.new('L', (W, H), 0)
    ImageDraw.Draw(img).line([((x - X0) * R8, (y - Y0) * R8) for x, y in w['road']], fill=255, width=int(2 * min_dist * R8), joint='curve')
    buf = np.array(img) > 0
    inbox = (WX >= box[0]) & (WX <= box[2]) & (WY >= box[1]) & (WY <= box[3])
    trim = water & buf & inbox
    if not trim.any(): return w, dict(trimmed_area=0)
    new_water = water & ~trim
    near = ndi.binary_dilation(trim, iterations=14)                       # smooth the new shore, only close to the trim
    new_water = np.where(near, ndi.binary_opening(new_water, iterations=3), new_water)
    lab, n = ndi.label(new_water)
    if n > 1:                                                             # the lake stays in one piece
        sizes = ndi.sum(new_water, lab, range(1, n + 1)); new_water = lab == (1 + int(np.argmax(sizes)))
    removed = water & ~new_water
    touched, added = _populate(w, [('freed from the lake', removed)], land & ~new_water, rng)
    w['geo']['water'] = AA._contours(new_water, X0, Y0, sigma=2.0)
    return w, dict(trimmed_area=round(float(removed.sum()) / R8 / R8, 1), tints_extended=touched, sprites_added=added)


def _clear_sprites(w, mask, margin_px=2):
    """Remove trees, grass and the like that sit on cells that have become water."""
    m = ndi.binary_dilation(mask, iterations=margin_px)
    for key in ('trees', 'tufts', 'reeds', 'hills', 'thorns', 'peaks', 'darkfog', 'mist'):
        arr = w.get(key) or []
        if not arr: continue
        ix = ((np.array([a[0] for a in arr]) - X0) * R8).astype(int); iy = ((np.array([a[1] for a in arr]) - Y0) * R8).astype(int)
        ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H); hit = np.zeros(len(arr), bool); hit[ok] = m[iy[ok], ix[ok]]
        w[key] = [a for a, h in zip(arr, hit) if not h]


def smooth_lake_sw_shore(w, a=(-29.6, -9.5), b=(-13.6, -2.5), seed=44):
    """The lake's south-west shore, from Ezard's Fields down and east to the lake's south-east tip, is one relatively direct line
    running north-west to south-east (no lobe poking toward The Shire), with natural waviness. The tip reaches a little further
    south. Water lost becomes forest."""
    rng = random.Random(seed)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    t_ = np.clip((WX - a[0]) / (b[0] - a[0]), 0, 1)
    wob = 0.55 * np.sin(0.42 * WX + 0.7) + 0.38 * np.sin(0.97 * WX + 2.1) + 0.2 * np.sin(1.9 * WX + 0.3)       # natural variance
    line = a[1] + (b[1] - a[1]) * t_ + 0.9 * np.sin(np.pi * t_) + wob * np.sin(np.pi * t_) ** 0.5            # a slight outward bow, and waviness
    section = (WX >= a[0] - 1.0) & (WX <= b[0] - 0.8) & (WY > line) & (WY < line + 10)
    removed = water & section
    new_water = water & ~removed
    # the south-east tip, a little further south: a rounded point where the line meets the east shore
    tip = _fillpoly([(-14.8, -3.9), (-14.0, -2.9), (-13.0, -2.35), (-12.2, -2.9), (-11.8, -4.0), (-12.0, -5.4), (-13.4, -5.2)]) & ~new_water
    new_water |= tip
    near = ndi.binary_dilation(removed | tip, iterations=14)                      # even out the shore, only close to the changes
    new_water = np.where(near, ndi.binary_closing(ndi.binary_opening(new_water, iterations=3), iterations=2), new_water)
    lab, n = ndi.label(new_water)
    if n > 1:
        sizes = ndi.sum(new_water, lab, range(1, n + 1)); new_water = lab == (1 + int(np.argmax(sizes)))
    removed = water & ~new_water; added = new_water & ~water
    touched, pop = _populate(w, [("the lake's old south-west lobe", removed)], land & ~new_water, rng)
    _clear_sprites(w, added)
    w['geo']['water'] = AA._contours(new_water, X0, Y0, sigma=2.0)
    return w, dict(removed_area=round(float(removed.sum()) / R8 / R8, 1), added_area=round(float(added.sum()) / R8 / R8, 1), tints_extended=touched, sprites_added=pop)


def bulge_lake_toward_tull(w):
    """Push the lake's east shore out toward Tullfuhrzky Manor and the Woods trail beside it, as a rounded bulge that stays about
    two rooms from the trail and three from the manor."""
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    lobe = _fillpoly([(-21.0, -23.6), (-18.0, -23.4), (-15.6, -23.0), (-13.6, -22.2), (-12.2, -21.0), (-11.5, -19.6), (-12.0, -18.3),
                      (-13.4, -17.4), (-15.2, -16.8), (-17.5, -16.6), (-21.0, -16.6)])
    new_water = ndi.binary_closing(water | lobe, iterations=3)
    new_water = ndi.binary_opening(new_water, iterations=4)                          # round off the corners of the bulge
    added = new_water & ~water
    _clear_sprites(w, added)
    w['geo']['water'] = AA._contours(new_water, X0, Y0, sigma=2.5)
    return w, dict(added_area=round(float(added.sum()) / R8 / R8, 1))


def remove_village_buildings(w, names, seed=61):
    """Take small buildings off the map entirely, and let trees and grass grow back where they were."""
    rng = random.Random(seed)
    gone = [b for b in w['buildings'] if b.get('name') in names]
    if not gone: return w, dict(removed=[])
    w['buildings'] = [b for b in w['buildings'] if b.get('name') not in names]
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    fills = []
    for b in gone:
        m = ((WX - b['x']) ** 2 + (WY - b['y']) ** 2 <= 1.3 ** 2) & land & ~water
        fills.append((b['name'], m))
    touched, added = _populate(w, fills, land & ~water, rng)
    return w, dict(removed=[b['name'] for b in gone], sprites_added=added)


def round_tavern_bend(w, tavern='Falcon\'s Nest Tavern'):
    """Where the Western Trade Route passes the tavern it ran north and then turned sharply west. Replace that corner with a wide
    arc around the tavern (about 3 rooms in radius) so the road sweeps from north to north-west to west."""
    tb = next(b for b in w['buildings'] if b.get('name') == tavern)
    road = [list(p) for p in w['road']]
    near = [i for i, p in enumerate(road) if math.hypot(p[0] - tb['x'], p[1] - tb['y']) < 4.5]
    seg = [road[i] for i in near]
    rx = float(np.median([p[0] for p in seg if abs(p[1] - tb['y']) < 1.5]))           # the road's x as it passes beside the tavern
    top = min(p[1] for p in seg)                                                        # the height of the westward stretch
    ay = tb['y'] + 0.8; ry = ay - top; R = ry; cx, cy = rx - R, ay                       # arc: north-going at (rx, ay), west-going at (rx - R, top)
    i0 = max(i for i, p in enumerate(road) if p[1] > ay and abs(p[0] - rx) < 2.0)       # last point before the arc
    i1 = min(i for i, p in enumerate(road) if i > i0 and p[0] <= cx and p[1] < top + 0.9)   # first point after it
    arc = [[round(cx + R * math.cos(math.radians(a)), 3), round(cy - R * math.sin(math.radians(a)), 3)] for a in range(0, 91, 6)]
    w['road'] = road[:i0 + 1] + arc + road[i1:]
    return w, dict(radius=round(R, 2), centre=(round(cx, 2), round(cy, 2)), replaced_points=i1 - i0 - 1, arc_points=len(arc))
