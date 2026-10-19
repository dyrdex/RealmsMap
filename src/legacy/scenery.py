"""Final visual additions around the Ashen Forest and the Eastern Trade Route (kept separate so each can be changed on its own)."""
import math, random
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import arrange_apply as AA
import gap_fill as GF

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8


def add_drawings(w, layout):
    """A castle above the King's Castle name, a windmill above the Glimwinkle's Windmill name, a town above the Ocean Keep marker,
    and a little inn on the room of The Ashen Forest Inn (vnum 2991)."""
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    ix, iy = pos[2991]
    w['gfx'] = list(w.get('gfx', [])) + [dict(k='castle', label="King's Castle", at='above-text', w=3.7, h=3.05),
                dict(k='windmill', label="Glimwinkle's Windmill", at='above-text', w=2.15, h=2.9),
                dict(k='town', label='Ocean Keep', at='above-pin', w=4.2, h=2.65),
                dict(k='inn', at='xy', x=round(ix, 3), y=round(iy - 0.5, 3), w=2.3, h=2.0),                                # halfway between the two rows of road
                dict(k='text', at='xy', x=round(ix, 3), y=round(iy + 2.4, 3), text='The Ashen Forest Inn')]               # just south of the road in front of the inn
    return w, dict(drawings=len(w['gfx']), inn_at=(round(ix, 2), round(iy, 2)))


def _pin_of(w, name):
    """Where a marker is drawn: the end of its traced route, nudged a little in the direction of its exit."""
    p = next(q for q in w['places'] if q['name'] == name)
    off = {'n': (0, -.62), 's': (0, .62), 'e': (.62, 0), 'w': (-.62, 0), 'ne': (.44, -.44), 'nw': (-.44, -.44), 'se': (.44, .44), 'sw': (-.44, .44), 'here': (0, 0)}[p['dir']]
    x, y = p['path'][-1]; return x + off[0], y + off[1]


def add_north_coast(w, seed=11):
    """Ocean Keep sits on the water of a small bay (and has a marina): the bay's south shore runs right along the north side of the town.
    Then the pale shallows along the north coast, running east round the corner to meet the water along the east beach."""
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    from bay import bay_mask
    sx, sy = GF.WX, GF.WY
    carve = bay_mask(sx, sy) & land & ~water                                        # land inside the bay becomes water: one smooth rounded bowl, the town at its south end
    new_land = land & ~carve
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    from gap_fill import _clear_sprites
    _clear_sprites(w, carve)                                                         # no trees standing in the bay
    for k in list(w['geo']):                                                          # the ground colours stop at the new shore too
        if k in ('land', 'water') or not w['geo'][k]: continue
        r = AA._raster(w['geo'][k], X0, Y0, W, H)
        if (r & carve).any(): w['geo'][k] = AA._contours(r & ~carve, X0, Y0)
    cx, cy = _pin_of(w, 'Ocean Keep')
    # the pale water along the north coast, joined (as one shape) to what is already along the east beach
    dist = ndi.distance_transform_edt(~new_land) / R8
    west = np.clip((GF.WX - 45.5) / 3.5, 0, 1)                      # it fades in from the west
    north = np.clip((GF.WY + 64.0) / 4.0, 0, 1)                      # and fades in from the north end of the new straight coast
    band = (~new_land) & ~water & (GF.WX > 45.5) & (GF.WX < 68) & (GF.WY < -26.5) & (GF.WY > -64) & (dist <= 2.6 * west * north) & (west * north > 0.05)
    old = AA._raster(w['geo']['shallows'], X0, Y0, W, H) if w['geo'].get('shallows') else np.zeros((H, W), bool)
    w['geo']['shallows'] = AA._contours((old | band) & ~new_land, X0, Y0, sigma=2.0)
    return w, dict(keep_at=(round(cx, 1), round(cy, 1)), bay_cut=round(float(carve.sum()) / R8 / R8, 1), shallows_added=round(float((band & ~old).sum()) / R8 / R8, 1))


def add_dread(w, layout, seed=3):
    """Shadar Logoth and Shai'ghool are places of ominous dark evil: the ground around them is a little darker and the trees closer and darker."""
    rng = np.random.default_rng(seed); rnd = random.Random(seed)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    sand = AA._raster(w['geo']['sand'], X0, Y0, W, H)
    noise = ndi.gaussian_filter(rng.normal(size=(H, W)), 1.8 * R8); noise = (noise - noise.min()) / (noise.max() - noise.min())
    mask = np.zeros((H, W), bool); outer = np.zeros((H, W), bool); inner_d = np.zeros((H, W), bool)
    centers = []
    for name, shift, R in (('Shadar Logoth', (-0.7, 0.0), 3.9), ("Shai'ghool", (0.0, 0.0), 4.1)):      # kept close to the markers
        x, y = _pin_of(w, name); x += shift[0]; y += shift[1]; centers.append((name, x, y, R))
        d = np.hypot(GF.WX - x, GF.WY - y); wob = 1 + 0.30 * (noise - 0.5) * 2
        mask |= d < R * wob; outer |= d < R * 1.3 * wob; inner_d |= d < R * 0.62 * wob
    ok = land & ~water & ~sand
    mask &= ok
    w['geo']['dread'] = AA._contours(outer & ok, X0, Y0, sigma=2.8)        # a wide faint shadow ...
    w['geo']['dread2'] = AA._contours(inner_d & ok, X0, Y0, sigma=2.8)     # ... darker toward the middle
    # more trees, and darker kinds: dark pines and dead pines mostly
    lines = []
    for k in ('fwtracks', 'swtracks', 'ashtracks'): lines += w.get(k, [])
    road = list(w.get('etrtracks', []))
    def pts_of(ls):
        out = []
        for ln in ls:
            for a, b in zip(ln[:-1], ln[1:]):
                n = max(1, int(math.dist(a, b) / 0.2)); out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
        return np.array(out) if out else np.zeros((0, 2))
    tt = cKDTree(pts_of(lines)); rt = cKDTree(pts_of(road)) if road else None
    ex = cKDTree(np.array([[t[0], t[1]] for t in w['trees']]))
    pins = np.array([_pin_of(w, p['name']) for p in w['places'] if p.get('group') == 'af'])
    pt = cKDTree(pins)
    inner = ndi.binary_erosion(mask, iterations=int(0.3 * R8))
    ys, xs = np.nonzero(inner); area = float(inner.sum()) / R8 / R8
    want = int(area * 0.62); new = []; tries = 0; placed = []
    mix = ['d'] * 58 + ['x'] * 14 + ['w'] * 28
    while len(new) < want and tries < want * 18:
        tries += 1
        j = rnd.randrange(len(xs)); x = xs[j] / R8 + X0 + rnd.uniform(0, 1 / R8); y = ys[j] / R8 + Y0 + rnd.uniform(0, 1 / R8)
        if tt.query([x, y])[0] < 0.55 or ex.query([x, y])[0] < 0.42 or pt.query([x, y])[0] < 0.7: continue
        if rt is not None and rt.query([x, y])[0] < 1.15: continue
        if placed and np.min(np.hypot(*(np.array(placed) - [x, y]).T)) < 0.45: continue
        new.append([round(x, 3), round(y, 3), round(rnd.uniform(0.9, 1.2), 3), rnd.choice(mix), rnd.randint(0, 2)]); placed.append((x, y))
    w['trees'] = list(w['trees']) + new
    return w, dict(centres=[(n, round(x, 1), round(y, 1), R) for n, x, y, R in centers], dark_ground_area=round(area, 1), trees_added=len(new))


RETIRED_BUILDINGS = ("The Hermit's Hut",)       # buildings (drawing and name) taken off the map at your request


def remove_retired_buildings(w):
    before = len(w['buildings'])
    w['buildings'] = [b for b in w['buildings'] if b['name'] not in RETIRED_BUILDINGS]
    return w, dict(removed=before - len(w['buildings']))


ASHEN_LABEL = dict(x=40.25, y=-24.0, lh=2.6, sag=1.0, lines=['Ashen', 'Forest'])      # the middle of the open ground north of Shai'ghool; each line on a gentle arc      # (position set below once the open space has been found)


def add_ashen_label(w, x=None, y=None):
    L = dict(ASHEN_LABEL)
    if x is not None: L['x'], L['y'] = x, y
    w['ashlabel'] = L
    return w, dict(ashen_label=(L['x'], L['y']))
