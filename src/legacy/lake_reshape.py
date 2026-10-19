"""Reshape the Lake of Tich'Pyga ("lake tich").

In the real game the lake is big and runs a long way north. On the map it was a small blue lake beside Darkhaven, with a pond
and a wide bay of open sea to the north of it. This joins them into one lake:

  * the south-east tip of the old lake is trimmed back so it sits further from Darkhaven;
  * a short channel joins it to the pond near Keep of Lomar (the pond's east end reaches toward Tullfuhrzky Manor);
  * the pond joins the bay through its narrow gap, and the bay fills the space between the Forest of Tears and the Forgotten
    Woods, its north-east corner reaching the Lost in the Swamp maze;
  * the west end of the bay is closed with a strip of woodland so it reads as a lake and not as sea.

Everything is done on the final (already scaled) map data.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure
from matplotlib.path import Path

X0, X1, Y0, Y1, RES = -135.0, 70.0, -115.0, 45.0, 8

# the strip of land that closes the bay's west end, and the part of the bay (and pond) that becomes lake. Both follow the same
# gently wandering west shore, so neither has a ruler-straight edge.
def _shore(y):                      # x of the lake's west shore at height y
    return -47.0 + 1.7 * math.sin(0.30 * (y + 22)) + 1.1 * math.sin(0.71 * y + 0.8) + 0.6 * math.sin(1.37 * y + 2.0)
def _coast(y):                      # x of the strip's outer (west) coast
    return -54.5 + 1.5 * math.sin(0.23 * (y + 9)) + 1.0 * math.sin(0.61 * y + 1.9) + 0.5 * math.sin(1.21 * y)
_YS = [y / 2 for y in range(-106, -44)]            # -53 .. -22.5 in half steps
STRIP = [(_shore(y), y) for y in _YS] + [(_coast(y), y) for y in reversed(_YS)]
BAY = [(_shore(y), y) for y in _YS] + [(-20, -22.5), (-20, -53)]
POND = [(-37, -27), (-12, -27), (-12, -14.5), (-37, -14.5)]
OLD_AXIS = (0.634, 0.773)          # the old lake runs north-west to south-east
OLD_CENTRE = (-16.2, -6.7)
TRIM_T = 0.2                       # keep the old lake only up to this far along its axis (the SE end is cut back)
CHANNEL = ((-19.6, -12.8), (-21.2, -17.6), 1.8)   # old lake -> pond


def _px(pts):
    return [((x - X0) * RES, (y - Y0) * RES) for x, y in pts]


def _fill(polys, W, H):
    img = Image.new('L', (W, H), 0); d = ImageDraw.Draw(img)
    for p in polys: d.polygon(_px(p), fill=255)
    return np.array(img) > 0


def _contours(mask, sigma, tol=0.5, minarea=1.0):
    m = ndi.gaussian_filter(mask.astype(float), sigma)
    out = []
    for c in measure.find_contours(m, 0.5):
        if len(c) < 8: continue
        c = measure.approximate_polygon(c, tol)
        pts = [[round(x / RES + X0, 3), round(y / RES + Y0, 3)] for y, x in c[:-1]]
        a = 0.5 * abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))))
        if a >= minarea: out.append(pts)
    return out


def reshape_lake(w, seed=5):
    rng = random.Random(seed)
    W, H = int((X1 - X0) * RES), int((Y1 - Y0) * RES)
    land = _fill(w['geo']['land'], W, H)
    strip = _fill([STRIP], W, H)
    sea = ~land
    yy, xx = np.mgrid[0:H, 0:W]; wx = xx / RES + X0; wy = yy / RES + Y0

    # --- the sea that becomes lake: the pond and the bay (only the parts that connect through the pond's gap) ---
    allowed = _fill([BAY, POND], W, H)
    cand = sea & allowed & ~strip
    lab, n = ndi.label(cand)
    keep = set()
    for sx, sy in ((-25, -20), (-35, -36)):
        v = lab[int((sy - Y0) * RES), int((sx - X0) * RES)]
        if v: keep.add(v)
    lake_sea = np.isin(lab, list(keep))

    # --- the old lake, with its south-east end cut back ---
    old = _fill(w['geo']['water'], W, H)
    t = (wx - OLD_CENTRE[0]) * OLD_AXIS[0] + (wy - OLD_CENTRE[1]) * OLD_AXIS[1]
    old_trim = old & (t <= TRIM_T)

    # --- the channel joining the old lake to the pond ---
    (ax, ay), (bx, by), r = CHANNEL
    px, py = bx - ax, by - ay; L2 = px * px + py * py
    u = np.clip(((wx - ax) * px + (wy - ay) * py) / L2, 0, 1)
    chan = ((wx - (ax + u * px)) ** 2 + (wy - (ay + u * py)) ** 2) <= r * r

    lake = lake_sea | old_trim | chan
    # widen the pond's narrow gap into the bay a little
    gap = ((wx + 26.6) ** 2 + (wy + 24.3) ** 2) <= 2.0 ** 2
    lake |= gap & ~strip
    # keep clear of every road and trail
    rb = Image.new('L', (W, H), 0); rd = ImageDraw.Draw(rb)
    lines = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + list(w['ribbons'])
    for ln in lines:
        if len(ln) > 1: rd.line(_px(ln), fill=255, width=int(3.4 * RES))
    roadbuf = np.array(rb) > 0
    # take the lake a little over the shore, by an amount that wanders, so straight coasts become natural shores
    rng_np = np.random.default_rng(seed)
    noise = ndi.gaussian_filter(rng_np.normal(size=(H, W)), 2.2 * RES)
    n01 = (noise - noise.min()) / (noise.max() - noise.min())
    dist = ndi.distance_transform_edt(~lake)
    expand = (dist <= (2.0 + 11.0 * n01)) & ~strip & ~roadbuf
    lake = lake | expand
    lake = ndi.binary_fill_holes(ndi.binary_closing(lake, iterations=4)) & ~strip

    water = _contours(lake, sigma=3.0, tol=0.6, minarea=3.0)
    # --- the land, with the closing strip added ---
    land2 = land | strip
    land_polys = _contours(land2, sigma=2.0, tol=0.5, minarea=3.0)

    # --- sprites: nothing grows in the lake; the new strip gets woodland ---
    lake_paths = [Path(np.array(p)) for p in water]
    def in_lake(pts, margin=0.0):
        pts = np.asarray(pts, float).reshape(-1, 2); res = np.zeros(len(pts), bool)
        for pa in lake_paths: res |= pa.contains_points(pts, radius=-margin)
        return res
    removed = {}
    for k in ('trees', 'tufts', 'reeds', 'hills', 'thorns', 'peaks'):
        arr = w[k]
        if not arr: continue
        m = in_lake([[a[0], a[1]] for a in arr], 0.6)
        removed[k] = int(m.sum()); w[k] = [a for a, g in zip(arr, m) if not g]
    # woodland on the strip, matching the density and mix of the trees just south of it
    ref = [a for a in w['trees'] if -62 < a[0] < -35 and -23 < a[1] < -12]
    area_ref = 27 * 11
    dens = len(ref) / area_ref if ref else 0.6
    sx0, sx1, sy0, sy1 = -55, -46, -53, -22
    n_new = int(dens * (sx1 - sx0) * (sy1 - sy0) * 0.9)
    added = 0
    near_lake = ndi.binary_dilation(lake, iterations=5)
    for _ in range(n_new * 3):
        x = rng.uniform(sx0, sx1); y = rng.uniform(sy0, sy1)
        j, i = int((y - Y0) * RES), int((x - X0) * RES)
        if not strip[j, i] or lake[j, i] or not land2[j, i]: continue
        if near_lake[j, i]: continue
        a = rng.choice(ref) if ref else [0, 0, 1, 'w', 0]
        w['trees'].append([round(x, 3), round(y, 3), round(a[2] * rng.uniform(0.9, 1.1), 3), a[3], rng.randint(0, 2)])
        added += 1
        if added >= n_new: break

    w['geo']['land'] = land_polys
    w['geo']['water'] = water

    # --- the lake's name: placed in the middle of the bay, along its long direction ---
    big = max(water, key=lambda p: len(p))
    dist = ndi.distance_transform_edt(lake)
    jy, ix = np.unravel_index(int(np.argmax(np.where(wy < -26, dist, 0))), dist.shape)
    cx, cy = float(wx[jy, ix]), float(wy[jy, ix])
    sel = lake & ((wx - cx) ** 2 + (wy - cy) ** 2 < 14 ** 2)
    ys, xs = np.nonzero(sel)
    pts = np.column_stack([xs / RES + X0, ys / RES + Y0]); pts -= pts.mean(0)
    ev, evec = np.linalg.eigh(np.cov(pts.T)); v = evec[:, 1]
    ang = math.degrees(math.atan2(v[1], v[0]))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    ang = -7.0
    w['lakelabel'] = dict(x=round(cx + 0.8, 2), y=round(cy, 2), a=ang, size=2.0, ls=0.5, half=11.5)
    return w, dict(lake_polys=len(water), land_polys=len(land_polys), removed=removed, trees_added=added, label=w['lakelabel'],
                   lake_area=round(float(lake.sum()) / RES / RES, 1))
