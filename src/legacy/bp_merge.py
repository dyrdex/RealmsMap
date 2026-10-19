"""Puts the Barren Peaks you arranged in the layout editor on the map (bp_layout_final.json, bp_editor_edges.json).
- The Northern Trade Route past the long bridge is the same formal road as the rest of it, carried on from the bridge (room 4135).
- The Peaks' own exits are dirt trails; where a Peaks room meets the road or a Forgotten Woods room, a short dirt connector joins them.
- Hidden rooms get nothing, up/down exits are not drawn, and spacer rooms that only lead off toward unmapped areas are left off.
- New land is grown around the Peaks (north of the old coast), with a pale barren tint and mountain peaks; field rooms get grass,
  forest rooms pines, hill rooms hills.
The bridge rooms 4133-4135 are moved by build.py itself (their new spots are copied into the Northern Trade Route layout before it is merged).
Runs after every other change to the land, because the shared raster grid (gap_fill) stops at y = -118; this module uses a taller grid
with the same x origin and pixel size, so the old coast is re-traced on an aligned grid (gotcha 2: a few specks at most)."""
import math, random
import numpy as np
from collections import defaultdict
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _nearest_on

R8 = GF.R8
X0, X1, Y0, Y1 = GF.X0, GF.X1, -170.0, GF.Y1            # same x origin and pixel size as gap_fill; 52 rooms taller to the north
W, H = int((X1 - X0) * R8), int((Y1 - Y0) * R8)
BRIDGE_END = 4135
ROAD_SKIP = {4133, 4134}                                  # the bridge itself is drawn by the Northern Trade Route merge
EXTRA_TRAILS = [(7077, 7139), (7125, 18139)]              # drawn as trails anyway (owner's request): an up/down exit; a spacer stub toward the Slime Pit
EXTRA_LINES = [[(-5.26, -90.48), (-5.17, -89.30)],                                  # 6652 - 18145 (owner's request)
               [(5.38, -87.33), (6.40, -88.20), (7.61, -87.17)]]                    # 5570 - 5571 - 5772 (rooms not otherwise on the map; owner's coordinates)
TAGS = [(-37.23, -118.98, 'The Lost City of Tahjliera', 0.55), (21.67, -128.18, 'The Keep of the Huitz', 0.55)]   # map-only names: x, y, text, size
MAZES = [('Valley of Mists Maze', [21625, 7355, 21626, 18831, 21627, 21628, 21624]),
         ('Where Power & Sorcery Collide Maze', [7645, 21777])]


def _components(G, nodes):
    seen = set(); out = []
    for s in nodes:
        if s in seen: continue
        q = [s]; seen.add(s)
        for x in q:
            for u in G[x]:
                if u not in seen: seen.add(u); q.append(u)
        out.append(q)
    return out


def merge_bp(w, layout, edges, seed=29, plains_road=(), absorb=None):
    """plains_road: road rooms that now lie in the Northern Plains (moved in the Plains editor); the Plains merge grows their land, so the Peaks' land is not grown around them."""
    plains_road = dict(plains_road) if isinstance(plains_road, dict) else {v: None for v in plains_road}   # {room: its position in the Peaks save}
    rng = random.Random(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info[v].get('void'))
    road = {v for v, r in info.items() if r.get('area') == 'RD' and shown(v) and v not in ROAD_SKIP}
    peaks = {v for v, r in info.items() if r.get('area') == 'BP' and shown(v)}
    fixed = {v for v, r in info.items() if r.get('fixed')}
    flat = [(a, b) for a, b, k in edges['edges'] if k != 'ud' and shown(a) and shown(b)]
    skipped = sum(1 for a, b, k in edges['edges'] if k != 'ud' and (a in hidden or b in hidden))

    # ---- the road past the bridge: road rooms, plus spacer rooms that sit between road rooms ----
    GR = defaultdict(set)
    rn = lambda v: v in road or v == BRIDGE_END or (v in peaks and void(v))
    for a, b in flat:
        if rn(a) and rn(b): GR[a].add(b); GR[b].add(a)
    for c in _components(GR, sorted(GR)):                                 # only spacer rooms joined to the road itself
        if not any(v in road for v in c):
            for v in c: del GR[v]
    keep = road | {BRIDGE_END}
    pruned_road = set()
    while True:                                                           # spacer spurs off the road (toward unmapped areas) are left off
        sp = [v for v in GR if len(GR[v]) <= 1 and v not in keep]
        if not sp: break
        for v in sp:
            for u in list(GR[v]): GR[u].discard(v)
            del GR[v]; pruned_road.add(v)
    comps = _components(GR, sorted(GR))
    main = next(c for c in comps if BRIDGE_END in c)
    road_nodes = set(main)
    loose_road = sorted(v for c in comps if BRIDGE_END not in c for v in c)
    road_lines = _chains({v: GR[v] for v in road_nodes}, pos, {BRIDGE_END}, 0.8)
    stray = [c for c in comps if BRIDGE_END not in c]
    for c in stray: road_lines += _chains({v: GR[v] for v in c}, pos, set(), 0.8)   # pieces of road the save does not join to the bridge
    road_used = {v for c in comps for v in c}

    # ---- the Peaks' trails: Peaks rooms and the spacer rooms between them ----
    GT = defaultdict(set); LINKS = []
    for a, b in flat:
        ia, ib = a in peaks and a not in road_used, b in peaks and b not in road_used
        if ia and ib: GT[a].add(b); GT[b].add(a)
        elif ia or ib:
            p, o = (a, b) if ia else (b, a)
            if o in road_used or o in fixed: LINKS.append((p, o))
    linked = {p for p, o in LINKS}
    # the Peaks rooms joined to the Plains' wide dirt road (owner, Oct 12): the road stands for all their little trails, so the trails
    # between two of them are left off and every other trail from one of them runs on to the road (absorb = (rooms, the road's lines))
    dpos = dict(pos); absorbed = 0
    if absorb:
        K, droad = absorb
        for v in K:
            if v in pos: q = _nearest_on(droad, pos[v]); dpos[v] = (q[0], q[1])
        for v in [v for v in GT if v in K]:
            for u in [u for u in GT[v] if u in K]: GT[v].discard(u); GT[u].discard(v); absorbed += 1
        for u in [u for u in GT if u not in K and len(GT[u]) == 1 and next(iter(GT[u])) in K]:   # one-room stubs off the road go too
            v = next(iter(GT[u])); GT[v].discard(u); GT[u].discard(v); absorbed += 1
        for v in [v for v in GT if not GT[v]]: del GT[v]
    pruned = set()
    while True:                                                           # dead-end spacer stubs are left off
        sp = [v for v in GT if len(GT[v]) <= 1 and void(v) and v not in linked]
        if not sp: break
        for v in sp:
            for u in list(GT[v]): GT[u].discard(v)
            del GT[v]; pruned.add(v)
    trails = _chains(GT, dpos, linked | set(absorb[0] if absorb else ()), 0.6)
    for a, b in EXTRA_TRAILS:
        if shown(a) and shown(b): trails.append([[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]])
    conn = []; joins = []
    for p, o in LINKS:
        if void(p) and p not in GT: continue
        if o in road_used:
            q = _nearest_on(road_lines, pos[p]); conn.append([[round(dpos[p][0], 2), round(dpos[p][1], 2)], [round(q[0], 2), round(q[1], 2)]])
            joins.append([round(q[0], 2), round(q[1], 2)])
        else:
            conn.append([[round(dpos[p][0], 2), round(dpos[p][1], 2)], [round(pos[o][0], 2), round(pos[o][1], 2)]])
    w['etrtracks'] = list(w.get('etrtracks', [])) + road_lines
    w['ntrjoins'] = list(w.get('ntrjoins', [])) + joins
    w['fwtracks'] = list(w['fwtracks']) + trails + conn

    # ---- new land around every shown room and trail, with a wandering edge ----
    pts = np.array([pos[v] for v in (peaks | road_used) if not void(v) and v not in plains_road] + [pos[v] for v in road_used if v not in plains_road], float)
    if plains_road:                                                       # only the runs of road that are nearer a Peaks-side road room
        rr = sorted(road_used); rk = cKDTree([pos[v] for v in rr]); land_road = []
        for ln in road_lines:
            run = []
            for q in ln:
                if rr[rk.query(q)[1]] in plains_road:
                    if len(run) > 1: land_road.append(run)
                    run = []
                else: run.append(q)
            if len(run) > 1: land_road.append(run)
    else: land_road = road_lines
    lines = land_road + trails + conn
    op = lambda v: plains_road.get(v) or pos[v]
    box = np.array([op(v) for v in (peaks | road_used) if not void(v)] + [op(v) for v in road_used], float)   # the grid box (and so the noise) as before the Plains moved the road
    lo, hi = box.min(0) - 9, box.max(0) + 9
    assert lo[1] > Y0 and hi[0] < X1 and lo[0] > X0, 'the Peaks reach past the edge of the grid'
    ix0, ix1 = int((lo[0] - X0) * R8), int((hi[0] - X0) * R8); iy0, iy1 = int((lo[1] - Y0) * R8), int((hi[1] - Y0) * R8)
    sub = (slice(iy0, iy1), slice(ix0, ix1)); hh, ww = iy1 - iy0, ix1 - ix0
    img = Image.new('L', (ww, hh), 0); dr = ImageDraw.Draw(img)
    px = lambda x, y: ((x - X0) * R8 - ix0, (y - Y0) * R8 - iy0)
    Rd = 3.0
    for x, y in pts: cx, cy = px(x, y); dr.ellipse([cx - Rd * R8, cy - Rd * R8, cx + Rd * R8, cy + Rd * R8], fill=255)
    for t in lines:
        if len(t) > 1: dr.line([px(*q) for q in t], fill=255, width=int(2 * Rd * R8), joint='curve')
    m0 = np.array(img) > 0
    Rc = 3.5 * R8
    m = ndi.distance_transform_edt(~m0) <= Rc
    m = ndi.distance_transform_edt(m) > Rc
    m = ndi.binary_fill_holes(m | m0)
    nrng = np.random.default_rng(seed)
    noise = ndi.gaussian_filter(nrng.normal(size=m.shape), 2.4 * R8); n01 = (noise - noise.min()) / (noise.max() - noise.min())
    soft = ndi.gaussian_filter(m.astype(float), 1.3 * R8)
    mask = np.zeros((H, W), bool); mask[sub] = soft > (0.5 + 0.22 * (n01 - 0.5) * 2)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    peaks_area = mask & ~water
    # the Peaks' own ground, with its natural edge (no coasts, no land beyond it: owner's call, Oct 10)
    new_land = land | peaks_area
    holes = ndi.binary_fill_holes(new_land) & ~new_land & ~water
    lab, nh = ndi.label(holes); filled = 0
    for k in range(1, nh + 1):
        hm = lab == k
        if hm.sum() / R8 / R8 < 60: new_land |= hm; filled += 1             # only small pockets of sea trapped between the Peaks and the old coast
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    grown = new_land & ~land
    beach = np.zeros((H, W), bool)
    tint = ndi.binary_erosion(grown, iterations=int(0.6 * R8)) & ~beach
    w['geo']['barren'] = AA._contours(tint, X0, Y0, sigma=2.0)
    nz = ndi.gaussian_filter(nrng.normal(size=(H, W))[sub], 3.0 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    dark = np.zeros((H, W), bool); dark[sub] = nz > 0.58                # darker patches of dirt
    w['geo']['barren2'] = AA._contours(ndi.binary_erosion(tint & dark, iterations=R8 // 2), X0, Y0, sigma=2.5)

    # ---- boulders here and there (in small clusters), clear of the paths ----
    cleared = 0; rs = _samples(lines)
    if len(rs):
        rt = cKDTree(rs)
        for key in ('trees', 'tufts', 'hills', 'thorns', 'peaks'):
            kept = [q for q in w[key] if rt.query([q[0], q[1]])[0] > 0.8]; cleared += len(w[key]) - len(kept); w[key] = kept
    inner = ndi.binary_erosion(grown & ~beach, iterations=int(0.6 * R8))
    ys, xs = np.nonzero(inner); area = float(inner.sum()) / R8 / R8
    ptree = cKDTree(rs) if len(rs) else None
    boulders = []; centres = int(area / 22)
    for _ in range(centres * 6):
        if len(boulders) >= centres * 3: break
        j = rng.randrange(len(xs)); cx = xs[j] / R8 + X0; cy = ys[j] / R8 + Y0
        if ptree is not None and ptree.query([cx, cy])[0] < 1.2: continue
        for _k in range(rng.choice((1, 1, 2, 3, 3, 4))):
            x = cx + rng.uniform(-0.7, 0.7); y = cy + rng.uniform(-0.5, 0.5)
            r_, c_ = int((y - Y0) * R8), int((x - X0) * R8)
            if not inner[r_, c_] or (ptree is not None and ptree.query([x, y])[0] < 0.8): continue
            if any(math.hypot(x - b[0], y - b[1]) < 0.45 for b in boulders[-6:]): continue
            boulders.append([round(x, 3), round(y, 3), round(rng.uniform(0.6, 1.25), 2)])
    w['boulders'] = sorted(boulders, key=lambda b: b[1])
    w['tags'] = list(w.get('tags', [])) + [list(x) for x in TAGS]          # map-only names (no marker, no card)
    w['fwtracks'] = list(w['fwtracks']) + [[list(p) for p in ln] for ln in EXTRA_LINES]
    w['arealabels'] = list(w.get('arealabels', [])) + [dict(x=-0.03, y=-121.44, lh=2.6, sag=1.0, hw=9, lines=['Barren Peaks', 'of Tahjliera'])]   # centred at (-0.03,-120.14)
    added = {'boulders': len(boulders)}
    # ---- the mazes, drawn like the Woods' maze blobs ----
    from scipy.spatial import ConvexHull
    for name, vs in MAZES:
        P = np.array([pos[v] for v in vs if v in pos])
        ring = np.array([[x + 1.0 * math.cos(a), y + 0.85 * math.sin(a)] for x, y in P for a in np.linspace(0, 2 * math.pi, 20, endpoint=False)])
        hull = ring[ConvexHull(ring).vertices]
        cx, cy = float(P[:, 0].mean()), float(P[:, 1].mean())
        m = dict(name=name, cx=round(cx, 3), cy=round(cy, 3), poly=[[round(float(a), 3), round(float(b), 3)] for a, b in hull], style='dark')   # the Woods' maze blob, in a dark, ominous version
        if len(P) < 4: m.update(lx=round(cx, 2), ly=round(float(P[:, 1].max()) + 1.75, 2), fs=0.5)  # a small maze: its name sits just below it (owner's choice)
        w['fwmazes'] = list(w['fwmazes']) + [m]
    pts_ = np.array([q for poly in w['geo']['land'] for q in poly])
    w['bounds'] = [int(pts_[:, 0].min()) - 3, int(pts_[:, 1].min()) - 3, int(pts_[:, 0].max()) + 3, int(pts_[:, 1].max()) + 3]
    return w, dict(road_rooms=len(road_nodes), road_lines=len(road_lines), road_spacers=sum(1 for c in comps for v in c if void(v)), loose_road_rooms=loose_road, road_spurs_left_off=len(pruned_road),
                   peak_rooms_on_trails=len(GT), trails_absorbed_by_dirt_road=absorbed, trail_lines=len(trails), connectors=len(conn), off_ramps=len(joins),
                   spacer_stubs_left_off=len(pruned), hidden_trails_skipped=skipped, sprites_cleared=cleared,
                   new_land_sq=round(float(grown.sum()) / R8 / R8, 1), sea_pockets_filled=filled, shown_rooms_in_sea=sum(1 for v in peaks | road_used if not new_land[int((pos[v][1] - Y0) * R8), int((pos[v][0] - X0) * R8)]), glyphs_added=dict(added), bounds=w['bounds'])
