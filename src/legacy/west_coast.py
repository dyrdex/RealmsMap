"""A new, smooth coastline on the west: from the south end of the Forgotten Woods' westernmost edge, curving south-west to the north coast of the Forest of Tears
at about the middle of that forest (east-west). The open water between that curve and the old coast (the lake's narrow west shore, the notches and bulge in the
Woods' coast, the strip north of the Western Trade Route) becomes forest, with the ground and trees of the land around it, so no path runs out over the water
and the trade route has land on both sides."""
import math, random
import numpy as np
from scipy import ndimage as ndi
import arrange_apply as AA
import gap_fill as GF

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8
# the new coast, from the Woods' westernmost edge (x = -60) to the Forest of Tears' north coast at its middle (x about -77)
CURVE = [(-60.0, -64.0), (-62.5, -56.0), (-65.5, -47.0), (-69.0, -38.5), (-72.5, -31.0), (-75.6, -25.5), (-79.0, -21.6)]


def _chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1]); pts = out
    return pts


def smooth_west_coast(w, seed=5):
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    curve = _chaikin(CURVE)
    # a gentle natural wobble along the new coast
    wob = [(x + 0.55 * math.sin(0.55 * y + 0.7), y) for x, y in curve]; wob[0] = curve[0]; wob[-1] = curve[-1]
    poly = wob + [(-82.0, -17.5), (-35.0, -17.5), (-35.0, -64.0)]                      # the curve, then back round through land to the start
    mask = GF._fillpoly(poly) & ~land & ~water
    raw = land | mask
    # round off the new coast (and the Woods' flat west edge just above it)
    ys, xs = np.mgrid[0:H, 0:W]; cx = xs / R8 + X0; cy = ys / R8 + Y0
    cpts = np.array(wob)
    from scipy.spatial import cKDTree
    near = cKDTree(cpts).query(np.stack([cx.ravel(), cy.ravel()], 1))[0].reshape(H, W) < 6.0
    near |= (cx > -63) & (cx < -55) & (cy > -73) & (cy < -60)
    sm = ndi.gaussian_filter(raw.astype(float), 1.6 * R8) > 0.5
    final = np.where(near, sm, raw)                                                   # smoothed near the new coast, untouched everywhere else
    final = final | (land & ~near)
    pockets = ndi.binary_fill_holes(final | water) & ~final & ~water                  # no little pools of water left behind
    final = final | pockets
    new = final & ~land
    w['geo']['land'] = AA._contours(final, X0, Y0)
    touched, added = GF._populate(w, [('west coast', new)], land, rng)
    return w, dict(pockets_filled=round(float(pockets.sum()) / R8 / R8, 2), forest_added=round(float(new.sum()) / R8 / R8, 1), planted=added, tints_extended=touched)
