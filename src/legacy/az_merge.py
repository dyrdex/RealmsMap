"""Puts the Azure Sea Coast on the map (az_layout_final.json, az_editor_edges.json): the owner's name (Oct 12) for the Azure Sea rooms
arranged in the Azure Sea editor. Owner's instructions (Oct 12):
- The route is a coastline: a rugged beach and at times open water, at the foot of a giant cliff; the mainland is up the cliff to the west.
  It is drawn in its own style, a dark blue line ('seaways'), as a largely aquatic, sea-side route.
- The land is NOT grown to meet it. Where the route lies on land, the land is cut back to a strong edge just west of it (a cliff: dark band
  and hachures along the new coast). Water is drawn east from the mainland far enough to take in the route and some open sea beyond it.
- Exception: 14257 to 14265 (the south end, by the Ashen beach) is a small stream winding over the land, a little wider than a path; the land
  there is not changed. From 14265 on it is the water route.
- Links between the coast and the mainland (from shown and hidden rooms alike): small dashed lines, and nothing else is dashed; other links
  of hidden rooms are not drawn (owner, Oct 12, revised).
- A marker for the Village of Edo at 7746 (where the route leaves for Edo), with the owner's directions traced on the card.
Runs after the Northern Plains merge and markers: it is now the LAST land change. Same raster grid as np_merge.
"""
import math, random, re
import numpy as np
from collections import defaultdict, deque
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import arrange_apply as AA
import np_merge as NM
from ntr_merge import _chains, _samples

R8 = NM.R8
X0, X1, Y0, Y1, W, H = NM.X0, NM.X1, NM.Y0, NM.Y1, NM.W, NM.H
STREAM = [14257, 14293, 14259, 14295, 14261, 14262, 14263, 14264, 14265]     # the small stream (owner, Oct 12)
SEA_END = 14265                     # where the stream meets the sea
EDO_DOOR = 7746                     # 'Adrift off the Coast': nw -> Village of Edo 7747
REACH = 8.0                         # open sea drawn up to this far from the water route ('some space further east')
BETWEEN = 30.0                      # and everything between the mainland's coast and the route, up to this far from the route
CUT = 1.0                           # land within this of the water route is cut away (the cliff stands just west of the route)
KEEP = 1.2                          # ... but never within this of a room already on the map
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'peaks', 'boulders', 'reeds', 'wheattufts', 'brush', 'crags', 'ripples')
LAYERS_KEEP = {'land', 'water'}     # every other geo layer is clipped off the new sea (gotcha 2)
GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
PORTAL = {4222}
NORTH_X, NORTH_Y, NORTH_TOP, NORTH_W = (-30.0, 24.0), -185.0, -215.0, 11.0   # the band (NORTH_W rooms wide, off the coast) north of the Plains that joins the two seas
EAST_X, EAST_Y, EAST_W, EAST_END = (45.0, 80.0), (-50.0, 26.0), 9.0, 18.0   # the band of sea down the Ashen Forest's east coast, fading out by y EAST_END
ISLAND = None                       # (was (2.0, 1.4): a small island north of the Village of Edo marker; removed on the owner's request, Oct 16: na_merge draws Edo's island)
LABEL_Y, LABEL_OFF, LABEL_SIZE = -143.0, 2.4, 1.25   # the route's name: beside the stretch 14285 -> 14286 at this y, this far toward the mainland


def _trace(route):
    """Follow the owner's directions from Darkhaven Square through the TinTin map (as np_marker_routes.py does)."""
    import io, contextlib
    g = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open('np_marker_routes.py').read().split('# (name on the map')[0], g)
    return g['walk'](route), g['rooms']


def merge_az(w, layout, edges, np_layout, seed=91):
    rng = random.Random(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    az = {v for v, r in info.items() if r.get('area') == 'AZ'}
    fixed = {v for v, r in info.items() if r.get('fixed')}
    stream_e = {(min(a, b), max(a, b)) for a, b in zip(STREAM, STREAM[1:])}

    # ---- the lines ----
    GS = defaultdict(set); GW = defaultdict(set); trails = []; dashed = []; links = []
    for a, b, k in edges['edges']:
        if a not in az and b not in az: continue
        if a in fixed or b in fixed:                                       # a link to the mainland (shown or hidden room): a small dashed line (owner, Oct 12)
            dashed.append([[round(pos[a][0], 3), round(pos[a][1], 3)], [round(pos[b][0], 3), round(pos[b][1], 3)]])
            links.append((a, b, round(math.dist(pos[a], pos[b]), 1))); continue
        if a in hidden or b in hidden: continue                            # any other link of a hidden room: not drawn (owner, Oct 12)
        (GS if (min(a, b), max(a, b)) in stream_e else GW)[a].add(b); (GS if (min(a, b), max(a, b)) in stream_e else GW)[b].add(a)
    assert set(GS) == set(STREAM), sorted(set(GS) ^ set(STREAM))
    stream = _chains(GS, pos, {STREAM[0], STREAM[-1]}, 0.7)
    pins = {SEA_END, EDO_DOOR}
    seaways = _chains(GW, pos, pins, 0.6)
    w['seaways'] = seaways; w['streams'] = stream; w['seadash'] = dashed
    w['fwtracks'] = list(w['fwtracks']) + trails

    # ---- the sea: land within CUT of the water route is cut away (never near a room on the map), the scraps of land left east of the
    #      route go too, and open water is drawn out to REACH beyond the route (narrowing to nothing toward the stream's mouth) ----
    land = AA._raster(w['geo']['land'], X0, Y0, W, H)
    ws = _samples(seaways, 0.1); wt = cKDTree(ws)
    onmap = np.array([pos[v] for v in pos if v not in az and v not in hidden], float)
    bx0 = max(0, int((ws[:, 0].min() - BETWEEN - 2 - X0) * R8)); bx1 = min(W, int((ws[:, 0].max() + REACH + 2 - X0) * R8))
    by0 = max(0, int((ws[:, 1].min() - REACH - 2 - Y0) * R8)); by1 = min(H, int((ws[:, 1].max() + REACH + 2 - Y0) * R8))
    yy, xx = np.mgrid[by0:by1, bx0:bx1]; P = np.c_[(xx.ravel() + .5) / R8 + X0, (yy.ravel() + .5) / R8 + Y0]
    d_route = wt.query(P)[0].reshape(yy.shape)
    d_fix = cKDTree(onmap).query(P)[0].reshape(yy.shape)
    d_mouth = np.hypot(P[:, 0] - pos[SEA_END][0], P[:, 1] - pos[SEA_END][1]).reshape(yy.shape)
    sub = (slice(by0, by1), slice(bx0, bx1))
    lsub = land[sub].copy()
    cut = lsub & (d_route <= CUT) & (d_fix > KEEP) & (d_mouth > 1.5)
    lnew = lsub & ~cut
    lab, n = ndi.label(lnew)                                            # scraps of land cut off from the mainland by the route go too
    main_ids = set(np.unique(lab[d_fix <= 0.5])) - {0}                  # every piece that holds a room on the map stays
    scraps = lnew & ~np.isin(lab, list(main_ids)) & (d_route <= REACH)
    lnew &= ~scraps
    newland = land.copy(); newland[sub] = lnew
    srng = np.random.default_rng(seed)
    reach = np.minimum(REACH, 0.6 + 0.7 * d_mouth)
    wob = ndi.gaussian_filter(srng.normal(size=yy.shape), 1.6 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    d_land = ndi.distance_transform_edt(~lnew) / R8
    sea_s = ((d_route <= reach * (0.85 + 0.3 * wob)) | ((d_land < d_route) & (d_route <= BETWEEN) & (d_mouth > 6) & (xx >= int((ws[:, 0].min() - 2 - X0) * R8)) & (yy < int((pos[14268][1] - 5 - Y0) * R8)))) & ~lnew   # (the sea runs from the coast out past the route; not west of the route's west end)
    sea_s = ndi.gaussian_filter(sea_s.astype(float), 0.8 * R8) > 0.5
    sea_s = ndi.binary_fill_holes(sea_s)
    sea_s &= ~lnew & (d_fix > 0.6)
    lab, n = ndi.label(sea_s)
    if n: sz = ndi.sum(sea_s, lab, range(1, n + 1)); sea_s = lab == (int(np.argmax(sz)) + 1)     # one body of water
    sea = np.zeros((H, W), bool); sea[sub] = sea_s
    gone = land & ~newland
    coastsea = sea.copy()                                               # (the cliff follows this sea only)

    # ---- later on Oct 12 (owner): (a) the small bay just north of Ocean Keep is part of the sea; (b) the sea runs along the whole north edge
    #      of the Plains, joining the north-west sea to this one; (c) a small island just north of the Village of Edo marker ----
    import bay as BY
    r0, r1 = int((BY.CY - 8 - Y0) * R8), int((BY.CY + 8 - Y0) * R8); c0, c1 = int((BY.CX - 9 - X0) * R8), int((BY.CX + 9 - X0) * R8)
    gy_, gx_ = np.mgrid[r0:r1, c0:c1]; bx_, by_ = (gx_ + .5) / R8 + X0, (gy_ + .5) / R8 + Y0
    baysea = np.zeros((H, W), bool)
    baysea[r0:r1, c0:c1] = (((bx_ - BY.CX) / (BY.A * 1.8)) ** 2 + ((by_ - BY.CY) / (BY.B * 1.8)) ** 2 < 1) & ~newland[r0:r1, c0:c1]
    nr0, nr1 = int((NORTH_TOP - Y0) * R8), int((NORTH_Y - Y0) * R8); nc0, nc1 = int((NORTH_X[0] - X0) * R8), int((NORTH_X[1] - X0) * R8)
    gy_, gx_ = np.mgrid[nr0:nr1, nc0:nc1]
    d_fn = cKDTree(onmap).query(np.c_[(gx_.ravel() + .5) / R8 + X0, (gy_.ravel() + .5) / R8 + Y0])[0].reshape(gx_.shape)
    d_cn = ndi.distance_transform_edt(~newland[nr0:, nc0:nc1])[:nr1 - nr0] / R8
    nwob = ndi.gaussian_filter(np.random.default_rng(seed + 2).normal(size=d_cn.shape), 1.6 * R8); nwob = (nwob - nwob.min()) / (nwob.max() - nwob.min())
    north = np.zeros((H, W), bool); north[nr0:nr1, nc0:nc1] = ~newland[nr0:nr1, nc0:nc1] & (d_fn > 1.0) & (d_cn <= NORTH_W * (0.85 + 0.3 * nwob))
    north = ndi.binary_opening(north, iterations=R8 // 2)
    er0, er1 = int((EAST_Y[0] - Y0) * R8), min(H, int((EAST_Y[1] - Y0) * R8)); ec0, ec1 = int((EAST_X[0] - X0) * R8), min(W, int((EAST_X[1] - X0) * R8))
    d_ce = ndi.distance_transform_edt(~newland[er0:er1, ec0:ec1]) / R8
    gy_, gx_ = np.mgrid[er0:er1, ec0:ec1]; ey_ = (gy_ + .5) / R8 + Y0
    d_fe = cKDTree(onmap).query(np.c_[(gx_.ravel() + .5) / R8 + X0, ey_.ravel()])[0].reshape(gx_.shape)
    ewob = ndi.gaussian_filter(np.random.default_rng(seed + 3).normal(size=d_ce.shape), 1.6 * R8); ewob = (ewob - ewob.min()) / (ewob.max() - ewob.min())
    fade = np.clip((EAST_END - ey_) / 8.0, 0, 1)
    east = np.zeros((H, W), bool); east[er0:er1, ec0:ec1] = ~newland[er0:er1, ec0:ec1] & (d_ce <= EAST_W * (0.85 + 0.3 * ewob) * fade)
    east = ndi.binary_opening(east, iterations=R8 // 2)
    keep_w, old_n = [], np.zeros((H, W), bool)                          # the north-west sea's water (np_merge) is redrawn as one body with this one
    for poly in w['geo']['water']:                                      #   (water is drawn even-odd: overlapping pieces would cancel)
        if max(q[1] for q in poly) < -150: old_n ^= AA._raster([poly], X0, Y0, W, H)
        else: keep_w.append(poly)
    ex, ey = pos[EDO_DOOR][0] - 0.5, pos[EDO_DOOR][1] - 1.9
    iy_, ix_ = np.mgrid[int((ey - 3 - Y0) * R8):int((ey + 3 - Y0) * R8), int((ex - 4 - X0) * R8):int((ex + 4 - X0) * R8)]
    ixx, iyy = (ix_ + .5) / R8 + X0, (iy_ + .5) / R8 + Y0
    wob = 1 + 0.08 * np.sin(2.3 * ixx + 1.1) + 0.07 * np.sin(2.9 * iyy + 0.3)
    island = np.zeros((H, W), bool)
    if ISLAND: island[iy_, ix_] = ((ixx - ex) / (ISLAND[0] * wob)) ** 2 + ((iyy - ey) / (ISLAND[1] * wob)) ** 2 < 1
    old_sh = AA._raster(w['geo'].get('shallows', []), X0, Y0, W, H) & ~newland   # (all of the old shallows' water is sea now too)
    sand_ = AA._raster(w['geo'].get('sand', []), X0, Y0, W, H)         # the beach stays (owner, Oct 12)
    allsea = (sea | baysea | north | east | old_n | old_sh) & ~island & ~sand_
    lab, n = ndi.label(allsea)
    bodies = {int(i) for i in np.unique(lab[sea | old_n]) if i}
    allsea = np.isin(lab, list(bodies))
    newland |= island
    w['geo']['land'] = AA._contours(newland, X0, Y0)
    w['geo']['water'] = keep_w + AA._contours(allsea, X0, Y0, sigma=1.5)
    extra = dict(bay_sq=round(float((allsea & baysea & ~sea).sum()) / R8 / R8, 1), east_sq=round(float((allsea & (east | old_sh) & ~sea).sum()) / R8 / R8, 1), shallows_only_sq=round(float((old_sh & ~east & ~sea & ~baysea).sum()) / R8 / R8, 1), north_gap_sq=round(float((allsea & north & ~sea & ~old_n).sum()) / R8 / R8, 1),
                 island_sq=round(float(island.sum()) / R8 / R8, 1), bodies=len(bodies))
    sea = allsea & ~old_n                                               # (what is new water here: clipped below)
    clipped = {}
    shallows_dropped = len(w['geo'].get('shallows', []))                # the old pale shallows tint along the Ashen coast: the sea replaces it, so the
    w['geo']['shallows'] = []                                           #   sea looks the same everywhere (owner, Oct 12); the beach stays
    for key, polys in list(w['geo'].items()):                          # tints and ground layers stop at the new coast (gotcha 2)
        if key in LAYERS_KEEP or not polys: continue
        m = AA._raster(polys, X0, Y0, W, H); hit = m & (gone | sea)
        if hit.any():
            w['geo'][key] = AA._contours(m & ~(gone | sea), X0, Y0, sigma=1.0); clipped[key] = round(float(hit.sum()) / R8 / R8, 1)
    wet = gone | sea
    stream_pts = _samples(stream, 0.1); st = cKDTree(stream_pts)
    def off(q):
        x, y = q[0], q[1]; r_, c_ = int((y - Y0) * R8), int((x - X0) * R8)
        if 0 <= r_ < H and 0 <= c_ < W and wet[r_, c_]: return False
        return st.query([x, y])[0] > 0.35                             # nothing grows in the stream
    cleared = {}
    for key in SPRITES:
        if key in w:
            kept = [q for q in w[key] if off(q)]; cleared[key] = len(w[key]) - len(kept); w[key] = kept

    # ---- the cliff: a dark band on the land side of the coast and hachures down to the water, all along the coast that faces the new sea ----
    edge = newland & ~ndi.binary_erosion(newland, iterations=int(0.55 * R8))
    ys_, xs_ = np.nonzero(edge)
    PE = np.c_[(xs_ + .5) / R8 + X0, (ys_ + .5) / R8 + Y0]
    d_sea = ndi.distance_transform_edt(~coastsea) / R8
    isl_ = ndi.binary_dilation(island, iterations=R8)                   # no cliff round the little island
    seaside = lambda x, y: d_sea[min(H - 1, max(0, int((y - Y0) * R8))), min(W - 1, max(0, int((x - X0) * R8)))] <= 1.2
    near = (d_sea[ys_, xs_] <= 1.2) & ~isl_[ys_, xs_] & (cKDTree(onmap).query(PE)[0] > 0.5) & (np.hypot(PE[:, 0] - pos[SEA_END][0], PE[:, 1] - pos[SEA_END][1]) > 2.0)
    band = np.zeros((H, W), bool); band[ys_[near], xs_[near]] = True
    band = ndi.binary_opening(band, iterations=1)
    w['geo']['cliff'] = list(w['geo'].get('cliff', [])) + AA._contours(band, X0, Y0, sigma=1.0)
    coast = []
    for c in AA._contours(newland, X0, Y0, sigma=1.5):
        for p in c:
            r_, c_ = int((p[1] - Y0) * R8), int((p[0] - X0) * R8)
            if 0 <= r_ < H and 0 <= c_ < W and isl_[r_, c_]: continue
            if seaside(*p) and cKDTree(onmap).query(p)[0] > 0.8 and math.dist(p, pos[SEA_END]) > 2.0: coast.append(p)
    hach = []; last = None
    dist_in = ndi.distance_transform_edt(newland)
    gy, gx = np.gradient(ndi.gaussian_filter(dist_in, 2.0))
    for x, y in coast:
        if last and math.dist((x, y), last) < 0.3: continue
        r_, c_ = int((y - Y0) * R8), int((x - X0) * R8)
        if not (0 <= r_ < H and 0 <= c_ < W): continue
        vx, vy = gx[r_, c_], gy[r_, c_]; L = math.hypot(vx, vy)
        if L == 0: continue
        vx, vy = vx / L, vy / L; ln = rng.uniform(0.45, 0.7)                 # (pointing inland)
        hach.append([round(x, 3), round(y, 3), round(x + vx * ln, 3), round(y + vy * ln, 3)]); last = (x, y)
    w['hach'] = list(w['hach']) + hach

    # ---- the name of the route (owner, Oct 12): 'Azure Sea Coastal Path', on the water between the route and the mainland beside the long
    #      stretch 14285 -> 14286 (north-east of the City of Iniquity), along that stretch. Map only: no card, no sidebar entry ----
    a_, b_ = pos[14285], pos[14286]; dx_, dy_ = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(dx_, dy_)
    f_ = (LABEL_Y - a_[1]) / dy_; px_, py_ = a_[0] + f_ * dx_, a_[1] + f_ * dy_
    nx_, ny_ = dy_ / L_, -dx_ / L_                                      # (the side toward the mainland, west)
    lx, ly = px_ + nx_ * LABEL_OFF, py_ + ny_ * LABEL_OFF
    w['seatags'] = list(w.get('seatags', [])) + [[round(lx, 2), round(ly, 2), 'Azure Sea Coastal Path', LABEL_SIZE, round(math.degrees(math.atan2(dy_, dx_)), 1)]]

    # ---- the Village of Edo marker at 7746, with the owner's directions traced ----
    import data as DT
    route = next(l.split('|', 1)[1].strip().rstrip(';') for l in (DT.AREAS + '\n' + DT.HOMETOWNS + '\n' + DT.MORE_DIRECTIONS).split('\n') if l.startswith('Village of Edo|'))
    (trail, fail), rooms = _trace(route)
    npos = {v: p for v, p in zip(np_layout['ids'], zip(np_layout['xs'], np_layout['ys'])) if v not in set(np_layout['hidden'])}
    track = w.get('track') or {}
    def at(v):
        if v in az: return pos[v]
        if v in npos: return npos[v]
        t = track.get('cx' + str(v)); return tuple(t[:2]) if t else None
    upto = trail[:trail.index(EDO_DOOR) + 1]
    segs = []; cur = []; gaps = 0; skipped = []
    for i, v in enumerate(upto):
        p = at(v)
        if p: cur.append([round(p[0], 3), round(p[1], 3)]); continue
        if v in PORTAL or (rooms[v]['area'] == 'Azure Sea' and i and at(upto[i - 1]) and i + 1 < len(upto) and at(upto[i + 1])):
            skipped.append(v); continue                              # (a coast room left out of the editor between two drawn ones: the line joins straight across)
        if cur: segs.append(cur); cur = []; gaps += 1
    segs.append(cur)
    site = pos[EDO_DOOR]
    w['places'].append(dict(name='Village of Edo', route=route, room='the Azure Sea Coast', dir='here', path=[q for s in segs for q in s], segs=segs,
                            group='af', where='off the Azure Sea Coast', note=GAP_NOTE if gaps else None))

    pts_ = np.array([q for k in ('land', 'water') for poly in w['geo'][k] for q in poly] + [pos[v] for v in az if v not in hidden])
    w['bounds'] = [min(w['bounds'][0], int(pts_[:, 0].min()) - 2), max(int(Y0), min(w['bounds'][1], int(pts_[:, 1].min()) - 2)),
                   max(w['bounds'][2], int(pts_[:, 0].max()) + 2), max(w['bounds'][3], int(pts_[:, 1].max()) + 2)]
    shown_az = [v for v in az if v not in hidden]
    return w, dict(seaway_lines=len(seaways), seaway_rooms=len(GW), stream_rooms=len(GS), mainland_links=links, dashed=len(dashed),
                   land_cut_sq=round(float(gone.sum()) / R8 / R8, 1), scraps_sq=round(float(scraps.sum()) / R8 / R8, 1),
                   sea_sq=round(float(sea.sum()) / R8 / R8, 1), sea_on_old_land_sq=round(float((sea & land).sum()) / R8 / R8, 1),
                   clipped=clipped, sprites_cleared=cleared, cliff_sq=round(float(band.sum()) / R8 / R8, 1), hachures=len(hach),
                   edo=dict(site=[round(site[0], 2), round(site[1], 2)], trace_failed=fail, segs=len(segs), gaps=gaps, joined_across=skipped),
                   rooms_in_sea=[v for v in shown_az if sea[int((pos[v][1] - Y0) * R8), int((pos[v][0] - X0) * R8)]].__len__(),
                   rooms_on_land=sorted(v for v in shown_az if newland[int((pos[v][1] - Y0) * R8), int((pos[v][0] - X0) * R8)]),
                   label=w['seatags'][-1], shallows_dropped=shallows_dropped, **extra, bounds=w['bounds'])
