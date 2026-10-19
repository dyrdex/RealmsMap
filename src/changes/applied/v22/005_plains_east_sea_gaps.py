"""Owner, Oct 19: after the Plains saves of Oct 19 the sea south and east of the Plains had gaps (the map's empty ground showing through)
between the new coast and the water. Inside a fixed box (east of the Plains), every empty pocket that is enclosed by land and sea (none
that touches the box's edge, so the open ground beyond the sea's east edge stays as it is) is filled with sea. The fill is its own layer
(`geo.seafill`, drawn over the sea, no outline, reaching a little into the sea to hide the old shore line), never over land; a shore line
(`seashore`) is drawn only where it meets land."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure

BOX = (15.0, -205.0, 78.0, -125.0)                                 # x0, y0, x1, y1
S = 8                                                              # raster cells per room


def _raster(polys):
    W, H = int((BOX[2] - BOX[0]) * S), int((BOX[3] - BOX[1]) * S); acc = np.zeros((H, W), bool)
    for P in polys:
        for r in ([P] if P and isinstance(P[0][0], (int, float)) else P):
            if len(r) < 3: continue
            im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon([((q[0] - BOX[0]) * S, (q[1] - BOX[1]) * S) for q in r], fill=1)
            acc ^= np.array(im)
    return acc


def _pts(c):
    return [[round(x / S + BOX[0], 3), round(y / S + BOX[1], 3)] for y, x in c]


def apply(town, wild, pos):
    land, sea = _raster(wild['geo']['land']), _raster(wild['geo']['water'])
    empty = ~land & ~sea
    lab, n = ndi.label(empty)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    pockets = np.isin(lab, [i for i in range(1, n + 1) if i not in edge])
    sizes = sorted((round(float(ndi.sum(pockets, lab, [i])[0]) / S / S, 2) for i in range(1, n + 1) if i not in edge), reverse=True)
    fill = (ndi.binary_dilation(pockets, iterations=3) & sea | pockets) & ~land            # (a little into the sea, never onto land)
    polys = []
    for c in measure.find_contours(np.pad(fill.astype(float), 1), 0.5):
        c = measure.approximate_polygon(c - 1, .6)
        if len(c) >= 4: polys.append(_pts(c[:-1]))
    wild['geo']['seafill'] = list(wild['geo'].get('seafill') or []) + polys
    near_land = ndi.binary_dilation(land, iterations=2)                                     # the shore line: the fill's edge where it meets land
    lines = []
    for c in measure.find_contours(np.pad(pockets.astype(float), 1), 0.5):
        cur = []
        for y, x in c - 1:
            iy, ix = min(max(int(round(y)), 0), land.shape[0] - 1), min(max(int(round(x)), 0), land.shape[1] - 1)
            if near_land[iy, ix]: cur.append((y, x))
            elif len(cur) > 2: lines.append(cur); cur = []
            else: cur = []
        if len(cur) > 2: lines.append(cur)
    wild['seashore'] = list(wild.get('seashore') or []) + [_pts(measure.approximate_polygon(np.array(l), .5)) for l in lines]
    return dict(pockets_filled=len(sizes), sq=round(sum(sizes), 1), largest=sizes[:5], fill_polygons=len(polys), shore_lines=len(lines))
