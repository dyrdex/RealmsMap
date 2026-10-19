"""Owner, Oct 19: clearings in the older areas drawn before the idea existed (Forgotten Woods, Ashen Forest, Barren Peaks), only the clear-cut ones
the owner picked from the assessment. A clearing is the Southern Mountain Range's rule: every cell of mutually exit-joined rooms (3 rooms all joined
to each other, or the 4 corners of a square) is filled, cells sharing rooms run together, widened by half a room. Each one is drawn in the ground of
its own spot, a little lighter (an opening), over the dirt trails inside it (trade roads stay on top); trees and other sprites in it are cleared."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import ConvexHull
from skimage import measure
from skimage.morphology import disk
from maplib import world, tracer

R8, PAD, CELL_MAX = 8, .55, 6.0                                  # (as the Southern Mountain Range)
DIRS = ('n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw')
# fill, edge: the ground under each spot (sampled from the map) a little lighter, and darker for the rim
WOODS, ASH, PEAKS, PEAKWOOD = ('#33432F', '#1E281F'), ('#484C43', '#2A2D27'), ('#5D4E39', '#352C20'), ('#33452F', '#1E281F')
CLEARINGS = {
    'FW-1 Flowing Plains of Grass': ([5078, 5182, 5315] + list(range(5386, 5400)), WOODS),
    'FW-2 Wandering Aimlessly through the Forest': (list(range(5947, 5957)), WOODS),
    'AF-1 In an Open Clearing (Bald Hillock)': ([2924, 2925, 2926, 2928, 2929, 2930, 2931, 2932, 2933, 2936, 2937], ASH),
    'AF-2 In an Open Clearing (Eastern Trade Route)': ([1241, 1242, 1245, 1249, 1250], ASH),
    'BP-1 The Keep of the Huitz': ([18832, 18833, 18834, 18835, 18836, 18837, 18838, 18840, 18841, 18843, 18844, 18845, 18847], PEAKS),
    'BP-2 An Old Mining Camp': ([6722, 6723, 6724, 6867, 6868, 6869, 6870], PEAKS),
    'BP-3 Border Guard Base': ([6917, 6918, 6919, 6920, 6921, 6922, 5789, 5790, 5791], PEAKWOOD),   # (with the Forgotten Woods rooms joined to it: owner, Oct 19)
    'BP-4 A Deserted Route': ([7046, 7047, 7048, 7059, 7060], PEAKS),
    'BP-5 The Supply Post and Campside (Woods border)': ([5733, 5734, 5735, 5736, 5737, 7038, 7039, 7040, 7041, 7042, 7043, 7044], WOODS),   # (owner, Oct 19: one clearing)
}
BRIDGES = {'BP-5 The Supply Post and Campside (Woods border)': [(5734, 5735, 7040, 7043), (7043, 7042, 7040)]}   # (7042 Burning Ashes, the V north of the hovel: owner, Oct 19)   # cells filled to join two clumps into one (owner's choice), over 908 and 7041
HUTS = [7041]                                                   # Setgro's Hovel: the map's small hut drawing on its room (owner, Oct 19)
EXTRA = {5399: 5394}                                            # rooms joined to their clearing by one exit only, taken in along it (owner, Oct 19: 5399, the last Flowing Plains of Grass room, NW)
SPRITES = ('trees', 'tufts', 'brush', 'boulders', 'crags', 'hills', 'peaks', 'wheattufts', 'thorns', 'reeds')


def apply(town, wild, pos):
    rooms, exits = world(); _, at = tracer(pos, wild)
    isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    def nb(v, d):                                                # the real room an exit leads to, through spacers
        for e in exits.get(v, []):
            if e['name'] == d:
                u = e['to']; k = 0
                while isspacer(u) and k < 40:
                    c = [x['to'] for x in exits.get(u, []) if x['name'] == d]
                    if not c: return None
                    u = c[0]; k += 1
                return u
    out, report, masks = [], {}, []
    for name, (ids, (fill, edge)) in CLEARINGS.items():
        P = {v: at(v) for v in ids}
        G = {v: set() for v in ids}
        for v in ids:
            for d in DIRS + tuple(e['name'] for e in exits.get(v, []) if e['name'] not in DIRS + ('u', 'd')):
                u = nb(v, d)
                if u in G and math.dist(P[u], P[v]) <= CELL_MAX: G[v].add(u); G[u].add(v)
        cells = set()
        for a in ids:
            for b in G[a]:
                for c in G[a] & G[b]: cells.add(frozenset((a, b, c)))
                for c in G[a]:
                    for d in (G[b] & G[c]) - {a}: cells.add(frozenset((a, b, c, d)))
        xs = [p[0] for p in P.values()]; ys = [p[1] for p in P.values()]
        x0, y0 = math.floor(min(xs)) - 2, math.floor(min(ys)) - 2; ww, hh = int((max(xs) + 2 - x0) * R8) + 1, int((max(ys) + 2 - y0) * R8) + 1
        px = lambda p: ((p[0] - x0) * R8, (p[1] - y0) * R8)
        im = Image.new('L', (ww, hh), 0); dr = ImageDraw.Draw(im); used = 0
        for cell in cells:
            pts = np.array([P[v] for v in cell])
            try: hull = ConvexHull(pts)
            except Exception: continue                           # (three in a line: no area)
            if hull.volume < .45: continue
            dr.polygon([px(p) for p in pts[hull.vertices]], fill=255, outline=255); used += 1
        for cell in BRIDGES.get(name, []):
            dr.polygon([px(P[v]) for v in cell], fill=255, outline=255); used += 1
        for a, b in EXTRA.items():
            if a in P and b in P: dr.line([px(P[a]), px(P[b])], fill=255, width=3); used += 1
        m = ndi.binary_dilation(np.array(im, bool), structure=disk(int(PAD * R8)))
        m = ndi.gaussian_filter(m.astype(float), .45 * R8) > .5
        polys = []
        for c in measure.find_contours(ndi.gaussian_filter(np.pad(m.astype(float), 1), 1.0), .5):
            c = measure.approximate_polygon(c, .35)
            polys.append([[round((x - 1) / R8 + x0, 3), round((y - 1) / R8 + y0, 3)] for y, x in c[:-1]])
        out.append({'polys': polys, 'fill': fill, 'edge': edge})
        masks.append((m, x0, y0))
        inside = sum(1 for p in P.values() if m[int((p[1] - y0) * R8), int((p[0] - x0) * R8)])
        report[name] = dict(rooms=len(ids), rooms_inside=inside, cells=used, sq=round(float(m.sum()) / R8 / R8, 1))
    wild['clearings'] = list(wild.get('clearings') or []) + out

    near = []                                                    # sprites in a clearing, or close enough above its edge to stand over it
    for m, x0, y0 in masks:
        g = ndi.binary_dilation(m, structure=disk(2))
        near.append((g, x0, y0))
    def hit(x, y):
        for g, x0, y0 in near:
            for yy in (y, y - .35):                              # (its foot, and a little up: a tree's crown)
                r, c = int((yy - y0) * R8), int((x - x0) * R8)
                if 0 <= r < g.shape[0] and 0 <= c < g.shape[1] and g[r, c]: return True
        return False
    cleared = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not hit(q[0], q[1])]
        if len(keep) != len(L): cleared[k] = len(L) - len(keep); wild[k] = keep
    tt = wild.get('talltrees') or []; keep = [q for q in tt if not hit(q[0], q[1])]
    if len(keep) != len(tt): cleared['talltrees'] = len(tt) - len(keep); wild['talltrees'] = keep
    report['sprites cleared'] = cleared
    for v in HUTS:
        x, y = at(v); wild['gfx'].append({'k': 'hut', 'at': 'xy', 'x': round(x, 2), 'y': round(y, 2), 'w': .72, 'h': .62})
    report['huts'] = len(HUTS)
    return report
