"""Puts the Southern Mountain Range, its Southern Mountain Trade Route and the moved Sparse Woodlands trail on the map
(smr_layout_final.json, smr_editor_edges.json: the owner's layout from tools/southern_mountain_range_editor).
Owner's rules (Oct 14):
1. Paths are drawn with respect to their neighbouring rooms: wherever rooms are directly adjacent, the path widens into one pathway that takes in
   several rooms.
2. A clump of rooms that all touch one another is not a path but a clearing: one open dirt patch made of those rooms (4 rooms in a square = a
   square patch). Both rules come from one shape: every cell of mutually exit-joined rooms (3 rooms all joined to each other, or the 4 corners of a
   square) is filled, cells that share rooms run together, and the patch is widened by half a room. A string of rooms with no such cells is a plain
   trail. It follows the exits, not the distance between rooms (the owner spread some blocks out to ~2.7 rooms apart).
Decided here (not in the owner's rules): the Trade Route is a formal road like the other trade routes (same widening, road colours, off-ramp pads
where the route meets other rooms); everything else is dirt. Terrain comes from the rooms' TinTin terrain. The land grows round the rooms (the map
now reaches south). Spacer rooms are drawn only between two real rooms (dead-end stubs left off); rooms and links of hidden rooms are not drawn.
The Sparse Woodlands trail (the Forest of Tears rooms the owner moved in this editor) is drawn by ft_merge from the moved positions (build.py
passes them in); this module only draws the links between it and the range.
Runs after ft_merge on a grid that reaches from the map's north edge (y -215) to the new south edge; the land is traced again from it."""
import math, random, re
import numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree, ConvexHull
from skimage.morphology import disk
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _nearest_on

R8 = GF.R8
X0, X1 = GF.X0, GF.X1
YN = -215.0
W = int((X1 - X0) * R8)
SQ = 1.1             # a room's square (rooms are 1 x 1; a little more so that neighbours merge)
MIN_STUB = 0.4       # a path that leads into a clearing but would vanish (outside part < VANISH) is still shown this much, so it is seen to lead in
VANISH = 0.12
CELL_MAX = 6.0       # exits longer than this do not make a cell (they are links, not neighbours)
PAD = 0.55           # a clearing reaches half a room beyond the outer rooms
MIN_PATCH = 3.0      # smallest clearing / wide pathway kept (sq rooms)
LAND_R = 4.2         # land reaches this far from a path
TERR_R = 3.8         # a room's terrain tint reaches this far
CLEAR = 1.0          # sprites keep this far from a path or patch
BAND = 2.4           # standard forest reaches this far (wobbled) from the connection to the Ashen Forest
SPRITE = {'m': 2.0, 'h': 1.7, 'd': 0.95}   # minimum spacing: peaks, hills, trees


def _hash(x, y, salt=0):
    """a number in [0, 1) that depends only on a position (and a salt): sprites are ordered and sized by it, so changing the mask in one place never re-rolls the ones elsewhere"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = (np.round(x * 1000).astype(np.int64) * 73856093 ^ np.round(y * 1000).astype(np.int64) * 19349663 ^ (salt * 83492791)) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def _drawn(p, n=14):
    """the line the template draws for a polyline p (its curve(): quadratic pieces with the points as controls, joined at the mid-points)"""
    if len(p) < 3: return [list(q) for q in p]
    out = [list(p[0])]; start = list(p[0])
    for i in range(1, len(p) - 1):
        m = [(p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2]
        for k in range(1, n + 1):
            t = k / n; out.append([(1 - t) ** 2 * start[0] + 2 * (1 - t) * t * p[i][0] + t * t * m[0], (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * p[i][1] + t * t * m[1]])
        start = m
    out.append(list(p[-1])); return out


def _paint(img, a, b, win, wpx):
    ImageDraw.Draw(img).line([a, b], fill=255, width=wpx)


def merge_smr(w, layout, edges, seed=71):
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    mov = {v for v, r in info.items() if not r.get('fixed') and v in pos}
    shown = lambda v: v in mov and v not in hidden
    void = lambda v: bool(info[v].get('void'))
    grp = lambda v: info[v].get('grp')
    DOM = {v for v in mov if shown(v) and grp(v) in ('sm', 'ug', 'tr')}        # what this module draws (the trail is ft_merge's)
    TRT = {v for v in DOM if grp(v) == 'tr'}
    report = {}

    # ---------------------------------------------------------------- the graphs
    GS = defaultdict(set); GT = defaultdict(set); links = []; uds = []
    NO_UD = {frozenset((291, 292))}                                    # the one up/down exit that is not drawn (owner, Oct 14)
    for a, b, k in edges['edges']:
        if a not in pos or b not in pos: continue
        if grp(a) == 'af' or grp(b) == 'af': continue                    # the visual-only link to the Ashen Forest (room 670): not drawn yet (owner, Oct 14)
        ina, inb = a in DOM, b in DOM
        if not (ina or inb): continue
        if (a in mov and a in hidden) or (b in mov and b in hidden): continue
        if k == 'ud':                                                  # up/down exits (owner, Oct 14): small dirt lines; they join different levels, so they make no wide path or clearing
            if frozenset((a, b)) not in NO_UD: uds.append((a, b))
            continue
        if ina and inb:
            if (a in TRT) and (b in TRT): GT[a].add(b); GT[b].add(a)
            elif (a not in TRT) and (b not in TRT): GS[a].add(b); GS[b].add(a)
            else: links.append((a, b))
        else: links.append((a, b))                                      # to the Sparse Woodlands trail or to a fixed room on the map
    import json as _js, os as _os
    CL = _js.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'smr_clearings.json')))      # clearings the owner marks by hand (Oct 14)
    in_box = lambda v, bx: bx[0] <= pos[v][0] <= bx[2] and bx[1] <= pos[v][1] <= bx[3]
    boxed = {}; faintG = defaultdict(set); inner_e = defaultdict(set)                                       # box index -> the shown rooms inside it
    for i, c in enumerate(CL.get('boxes', []) + CL.get('towns', [])):
        boxed[i] = {v for v in DOM if in_box(v, c['box'])}
        for G in (GS,):
            for a in list(G):
                for b in list(G[a]):
                    if a in boxed[i] and b in boxed[i]:
                        G[a].discard(b); G[b].discard(a); inner_e[i].add((min(a, b), max(a, b)))      # a connection inside the clearing is not drawn ...
                        if c.get('faint_paths'): faintG[a].add(b); faintG[b].add(a)      # ... or only very lightly
        uds[:] = [(a, b) for a, b in uds if not (a in boxed[i] and b in boxed[i])]
        links[:] = [(a, b) for a, b in links if not (a in boxed[i] and b in boxed[i])]     # (also the range's links to the Trade Route junction inside it)
    for t_ in CL.get('towns', []):                                              # the gate road replaces the thin lines between its rooms
        g_ = t_.get('gate')
        if g_:
            for a_, b_ in zip(g_['rooms'], g_['rooms'][1:]):
                for G in (GS,):
                    if a_ in G: G[a_].discard(b_)
                    if b_ in G: G[b_].discard(a_)
            uds[:] = [(a, b) for a, b in uds if not (a in g_['rooms'] and b in g_['rooms'])]
            links[:] = [(a, b) for a, b in links if not (a in g_['rooms'] and b in g_['rooms'])]
    inn_rooms = {v for i_ in CL.get('inns', []) for v in i_['rooms']}
    for G in (GT,):                                                             # an inn's rooms are inside the building, not road
        for a in list(G):
            for b in list(G[a]):
                if a in inn_rooms or b in inn_rooms: G[a].discard(b); G[b].discard(a)
        for v in [v for v in G if not G[v]]: del G[v]
    links[:] = [(a, b) for a, b in links if a not in inn_rooms and b not in inn_rooms]
    tun_rooms = set()
    for U_ in CL.get('undergrounds', []):                                       # the river's tunnel is not a path: its rooms (but not the surface rooms it opens onto) leave the path graphs
        tun_rooms |= set(U_['path']) - {U_['path'][-1]} | {U_['grotto']}
    for G in (GS, GT):
        for a in list(G):
            for b in list(G[a]):
                if (a in tun_rooms or b in tun_rooms) or (a in {U_['path'][-1] for U_ in CL.get('undergrounds', [])} and b in tun_rooms): G[a].discard(b); G[b].discard(a)
        for v in [v for v in G if not G[v]]: del G[v]
    for U_ in CL.get('undergrounds', []):                                       # the edge between the far-end room and the tunnel goes too (it is the tunnel)
        e_ = U_['path'][-1]
        for G in (GS,):
            for b in list(G.get(e_, [])):
                if b in tun_rooms: G[e_].discard(b); G[b].discard(e_)
    links[:] = [(a, b) for a, b in links if a not in tun_rooms and b not in tun_rooms]
    uds[:] = [(a, b) for a, b in uds if a not in tun_rooms and b not in tun_rooms]
    climb_rooms = [set(c['rooms']) for c in CL.get('climbs', [])]
    for cr in climb_rooms:                                                      # the thin lines between the rooms of a climb are replaced by its wide rocky path
        uds[:] = [(a, b) for a, b in uds if not (a in cr and b in cr)]
        links[:] = [(a, b) for a, b in links if not (a in cr and b in cr)]
        for a in list(GS):
            for b in list(GS[a]):
                if a in cr and b in cr: GS[a].discard(b); GS[b].discard(a)
    report['clearing_boxes'] = [{'name': c['name'], 'rooms': len(boxed[i])} for i, c in enumerate(CL.get('boxes', []))]
    def prune(G, extra):
        pr = set()
        while True:                                                    # dead-end spacer stubs are left off
            sp = [v for v in G if void(v) and len(G[v]) + extra.get(v, 0) <= 1]
            if not sp: break
            for v in sp:
                for u in list(G[v]): G[u].discard(v)
                del G[v]; pr.add(v)
        for v in [v for v in G if not G[v]]: del G[v]
        return pr
    lcount = defaultdict(int)
    for a, b in links: lcount[a] += 1; lcount[b] += 1
    pruned = prune(GS, lcount) | prune(GT, lcount)
    report['rooms_shown'] = {'range': len([v for v in DOM if v not in TRT]), 'route': len(TRT)}
    report['spacer_stubs_dropped'] = len(pruned)
    onmap = {v for G in (GS, GT) for v in G} | {v for a, b in links for v in (a, b) if v in DOM}
    onmap |= {v for a, b in uds for v in (a, b) if v in DOM and not void(v)}                 # (a real room whose only exits are up/down ones is still on the map)
    LINKS = [(a, b) for a, b in links if (a in DOM) != (b in DOM) or (a in DOM and b in DOM)]
    LINKS = [(a, b) for a, b in LINKS if all((v not in DOM) or v in onmap for v in (a, b))]
    UDL = [(a, b) for a, b in uds if all((v not in DOM) or v in onmap for v in (a, b))]       # (a spacer dropped as a stub takes its up/down exit with it)
    UDL = [e for e in UDL if e not in LINKS and (e[1], e[0]) not in LINKS]
    report['up_down_exits'] = {'with_a_range_end': len(uds), 'not_drawn_pruned': len(uds) - len(UDL), 'left_out': [291, 292]}

    # the visual-only connection (owner, Oct 14; not in TinTin's map): room 559 -> spacer room 990001 -> Ashen Forest room 670, a standard dirt trail through standard forest
    VIS = (559, 990001, 670)
    vis = [[round(pos[v][0], 2), round(pos[v][1], 2)] for v in VIS] if all(v in pos and v not in hidden for v in VIS) else None
    moved_ends = 0
    if vis:
        import json, os
        _al = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_layout_final.json')))
        old670 = dict(zip(_al['ids'], zip(_al['xs'], _al['ys'])))[670]                  # where the Ashen Forest drew room 670 (its trail north to 2864 starts there)
        for ln in w['fwtracks']:
            for i in (0, -1):
                if math.dist(ln[i], old670) < 0.06: ln[i] = list(vis[-1]); moved_ends += 1   # (not moved inside the Ashen merge: that re-rolls its random trees)
    report['ashen_connection'] = {'trail_ends_moved': moved_ends, 'drawn': bool(vis), 'length': round(sum(math.dist(p, q) for p, q in zip(vis, vis[1:])), 1) if vis else None}

    # ---------------------------------------------------------------- the window (everything this module paints lies in it)
    allp = np.array([pos[v] for v in onmap] + ([pos[v] for v in VIS] if vis else [])); pad = 12.0
    wx0 = math.floor(allp[:, 0].min() - pad); wx1 = math.ceil(allp[:, 0].max() + pad)
    wy0 = math.floor(allp[:, 1].min() - pad); wy1 = math.ceil(allp[:, 1].max() + pad)
    ww, hw = int((wx1 - wx0) * R8), int((wy1 - wy0) * R8)
    px = lambda p: ((p[0] - wx0) * R8, (p[1] - wy0) * R8)
    gy, gx = np.mgrid[0:hw, 0:ww]; WXg = (gx + .5) / R8 + wx0; WYg = (gy + .5) / R8 + wy0

    # ---------------------------------------------------------------- wide pathways and clearings (one shape, from the adjacent rooms)
    def fabric(G):
        """clearings and wide pathways: every cell of mutually exit-joined real rooms (a triangle, or a 4-cycle = the corners of a square) is filled,
        the cells that share rooms run together, and the result is widened by half a room (the rooms' own squares). Spacing does not matter: a block
        of rooms the owner spread out is still a clump."""
        real = {v for v in G if not void(v)}
        nb = {v: {u for u in G[v] if u in real and math.dist(pos[u], pos[v]) <= CELL_MAX} for v in real}
        cells = set()
        for a in real:
            for b in nb[a]:
                for c in nb[a] & nb[b]:
                    if len({a, b, c}) == 3: cells.add(frozenset((a, b, c)))
            for b in nb[a]:
                for c in nb[a]:
                    if b < c:
                        for d in (nb[b] & nb[c]) - {a}:
                            if len({a, b, c, d}) == 4: cells.add(frozenset((a, b, d, c)))
        im = Image.new('L', (ww, hw), 0); dr = ImageDraw.Draw(im); used = 0
        for cell in cells:
            pts = np.array([pos[v] for v in cell])
            hull = pts[ConvexHull(pts).vertices] if len(pts) >= 3 else pts
            if ConvexHull(pts).volume < 0.45: continue                                   # (three in a line: no area)
            dr.polygon([px(p) for p in hull], fill=255, outline=255); used += 1
        m0 = np.array(im, bool)
        m0 = ndi.binary_dilation(m0, structure=disk(int(PAD * R8)))                     # (the rooms' own squares)
        lab, n = ndi.label(m0); keep = np.zeros_like(m0)
        rp = [(v, px(pos[v])) for v in real]
        for i in range(1, n + 1):
            comp = lab == i
            nrooms = sum(1 for v, p in rp if 0 <= int(p[1]) < hw and 0 <= int(p[0]) < ww and comp[int(p[1]), int(p[0])])
            if nrooms >= 4 and comp.sum() / R8 / R8 >= MIN_PATCH: keep |= comp
        op = ndi.gaussian_filter(keep.astype(float), 0.45 * R8) > 0.5                  # (rounds the corners a little)
        return op, list(cells)
    def trails(G, wide):
        """the lines of what is NOT inside a wide pathway or clearing"""
        T = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                n = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(n + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / n; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / n
                    c, r = int((x - wx0) * R8), int((y - wy0) * R8)
                    if not (0 <= r < hw and 0 <= c < ww and wide[r, c]): inside = False; break
                if not inside: T[a].add(b); T[b].add(a)
        return T
    dwide, dadj = fabric(GS); rwide, radj = fabric(GT)
    forced = Image.new('L', (ww, hw), 0); fd = ImageDraw.Draw(forced)
    for c in CL.get('boxes', []):                                              # the owner's rectangles: one dirt clearing each
        x0_, y0_, x1_, y1_ = c['box']; fd.rectangle([px((x0_, y0_)), px((x1_, y1_))], fill=255)
    dwide = ndi.gaussian_filter((dwide | np.array(forced, bool)).astype(float), 0.45 * R8) > 0.5
    added = {}; done_to = {}
    def disk_px(): return int(PAD * R8)
    sq_ = int(SQ * R8)
    def put_square(dr_, p_): dr_.rectangle([p_[0] - sq_ / 2, p_[1] - sq_ / 2, p_[0] + sq_ / 2, p_[1] + sq_ / 2], fill=255)
    todo = []
    for e_ in CL.get('add_rooms', []):
        e_ = {'room': e_} if isinstance(e_, int) else dict(e_); e_['to'] = [e_['to']] if isinstance(e_.get('to'), int) else list(e_.get('to') or [])
        if e_['room'] not in pos or any(t not in pos for t in e_['to']): added[e_['room']] = 'missing'; continue
        todo.append(e_)
    while todo:                                                               # hulls first, then stems nearest-first (a chain of rooms grows the clearing room by room)
        hulls = [e_ for e_ in todo if e_.get('mode') == 'hull']
        if hulls: e_ = hulls[0]
        else:
            best = None
            for e_c in todo:
                lab_, n_ = ndi.label(dwide); ids_ = {lab_[min(max(int(px(pos[t])[1]), 0), hw - 1), min(max(int(px(pos[t])[0]), 0), ww - 1)] for t in e_c['to']} - {0}
                comp_ = np.isin(lab_, list(ids_)) if ids_ else dwide
                d_, (iy_, ix_) = ndi.distance_transform_edt(~comp_, return_indices=True)
                p_ = px(pos[e_c['room']]); r_, c_ = min(max(int(p_[1]), 0), hw - 1), min(max(int(p_[0]), 0), ww - 1)
                if best is None or d_[r_, c_] < best[0]: best = (d_[r_, c_], e_c, (int(ix_[r_, c_]), int(iy_[r_, c_])))
            e_ = best[1]
        todo.remove(e_)
        im_ = Image.new('L', (ww, hw), 0); dr_ = ImageDraw.Draw(im_); p_ = px(pos[e_['room']])
        if e_.get('mode') == 'hull':
            pts = [pos[e_['room']]] + [pos[t] for t in e_['to']]
            cor = np.array([(x + dx, y + dy) for x, y in pts for dx in (-SQ / 2, SQ / 2) for dy in (-SQ / 2, SQ / 2)])
            hl = cor[ConvexHull(cor).vertices]; dr_.polygon([px(q) for q in hl], fill=255, outline=255); added[e_['room']] = 'hull of %d rooms' % len(pts)
        else:
            tx, ty = best[2] if not hulls else (int(p_[0]), int(p_[1]))
            dr_.line([p_, (tx, ty)], fill=255, width=sq_); put_square(dr_, p_); added[e_['room']] = round(float(best[0]) / R8, 1) if not hulls else 0
            key_ = tuple(e_['to'])
            for q_ in done_to.get(key_, []) + e_['to']:                          # ... and to the other rooms of its group within 4 rooms: rooms side by side fill the ground between them
                if math.dist(pos[q_], pos[e_['room']]) <= 4.0: dr_.line([p_, px(pos[q_])], fill=255, width=sq_)
            done_to.setdefault(key_, []).append(e_['room'])
        dwide = dwide | np.array(im_, bool)                                       # (smoothed once, below: smoothing after every room eroded the small clearings)
    if CL.get('add_rooms'): dwide = ndi.gaussian_filter(dwide.astype(float), 0.45 * R8) > 0.5
    report['clearing_rooms_added'] = added
    townm = Image.new('L', (ww, hw), 0); tdr = ImageDraw.Draw(townm)
    for t_ in CL.get('towns', []): tdr.rectangle([px((t_['box'][0], t_['box'][1])), px((t_['box'][2], t_['box'][3]))], fill=255)
    townmask = np.array(townm, bool)
    dwide &= ~townmask                                                              # (a town replaces any clearing under it)
    dwide &= ~rwide                                                                 # (a road patch lies on top of any dirt patch)
    dT = trails(GS, dwide | rwide); rT = trails(GT, rwide)
    dirt_lines = _chains(dT, pos, set(), 0.8) if dT else []
    road_lines = _chains(rT, pos, set(), 0.8) if rT else []
    # the links between the range, the route, the moved Sparse Woodlands trail and fixed rooms: small dirt lines
    link_lines = []; far = []
    snap = {}; offs = []                                                       # off-ramps lie ON the drawn road: a Trade Route room's pad (and the end of the line that joins it) goes to the nearest point of the road
    for a, b in LINKS:
        for v, o in ((a, b), (b, a)):
            if v in TRT and o not in TRT and road_lines and v not in snap:
                q_ = _nearest_on([_drawn(l) for l in road_lines], pos[v]); snap[v] = [round(q_[0], 2), round(q_[1], 2)]; offs.append(round(math.dist(q_, pos[v]), 2))
    end_ = lambda v: snap.get(v) or [round(pos[v][0], 2), round(pos[v][1], 2)]
    for a, b in LINKS + UDL:
        d = math.dist(pos[a], pos[b])
        if d > 30: far.append((a, b, round(d, 1)))
        elif sorted((a, b)) in [sorted(x) for x in CL.get('bent_links', [])]:         # a long link drawn with a bend, like the other trails (owner, Oct 15: 7 to 8)
            A_, B_ = np.array(end_(a), float), np.array(end_(b), float); dv_ = B_ - A_; nv_ = np.array([-dv_[1], dv_[0]]) / (np.linalg.norm(dv_) or 1)
            pts_ = [A_] + [A_ + dv_ * f_ + nv_ * amp_ for f_, amp_ in ((0.25, 1.6), (0.5, -1.1), (0.78, 1.0))] + [B_]
            link_lines.append([[round(float(q[0]), 2), round(float(q[1]), 2)] for q in pts_])
        else: link_lines.append([end_(a), end_(b)])
    dpatch = AA._contours(dwide, wx0, wy0, sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    rpatch = AA._contours(rwide, wx0, wy0, sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    # ---- thin paths never run over a clearing (owner, Oct 14): each stops where it enters one (it only shows that the path leads into it)
    dmask = AA._raster(dpatch, wx0, wy0, ww, hw) | townmask                          # (paths stop at a town's edge too)
    clearmask = dmask & ~townmask
    def clip(lines, step=0.08, keep_every=4):
        out = []; cut = 0; ext = 0
        for ln in lines:
            pts = []                                                              # the line, sampled; remember which samples are inside a clearing / a town
            for p, q in zip(ln[:-1], ln[1:]):
                n_ = max(1, int(math.dist(p, q) / step))
                pts += [(p[0] + (q[0] - p[0]) * k / n_, p[1] + (q[1] - p[1]) * k / n_) for k in range(n_)]
            pts.append(tuple(ln[-1]))
            ins = []; inc = []
            for x, y in pts:
                c_, r_ = int((x - wx0) * R8), int((y - wy0) * R8); ok_ = 0 <= r_ < hw and 0 <= c_ < ww
                ins.append(ok_ and bool(dmask[r_, c_])); inc.append(ok_ and bool(clearmask[r_, c_]))
            if not any(ins): out.append(ln); continue
            cut += 1; runs = []; run = []
            for k, (pt, i_) in enumerate(zip(pts, ins)):
                if i_:
                    if len(run) >= 2: runs.append(run)
                    run = []
                else: run.append((k, pt))
            if len(run) >= 2: runs.append(run)
            for run in runs:
                k0, k1 = run[0][0], run[-1][0]; L_ = sum(math.dist(a[1], b[1]) for a, b in zip(run[:-1], run[1:]))
                if L_ < VANISH:                                                    # a path that ends right at a clearing and would vanish still shows that it leads in: MIN_STUB long, into the clearing (not into a town); longer ones stop at the edge as before
                    if k0 == 0 and k1 + 1 < len(pts):
                        kk = k1
                        while L_ < MIN_STUB and kk + 1 < len(pts) and inc[kk + 1]:
                            L_ += math.dist(pts[kk], pts[kk + 1]); kk += 1; run.append((kk, pts[kk])); ext += 1
                    elif k1 == len(pts) - 1 and k0 > 0:
                        kk = k0
                        while L_ < MIN_STUB and kk - 1 >= 0 and inc[kk - 1]:
                            L_ += math.dist(pts[kk], pts[kk - 1]); kk -= 1; run.insert(0, (kk, pts[kk])); ext += 1
                th = [p for _, p in run][::keep_every]
                if th[-1] != run[-1][1]: th.append(run[-1][1])
                l2 = [[round(x, 2), round(y, 2)] for x, y in th]
                if len(l2) >= 2 and math.dist(l2[0], l2[-1]) >= 0.04: out.append(l2)
        return out, cut, ext
    dirt_lines, cut1, e1 = clip(dirt_lines); link_lines, cut2, e2 = clip(link_lines); vis_c, cut3, e3 = clip([vis]) if vis else ([], 0, 0)
    report['lines_stopped_at_a_clearing'] = {'trails': cut1, 'links': cut2, 'connection_to_670': cut3, 'paths_that_would_vanish_kept': (e1 + e2 + e3)}
    # ---- the hand-made clearings' extras: their inner paths very lightly, rough-terrain marks between them
    faint_lines = _chains(faintG, pos, set(), 0.6) if faintG else []
    for c in CL.get('boxes', []):                                              # (owner, Oct 14) a path that crosses into the box and should keep showing inside it, in the light style
        x0_, y0_, x1_, y1_ = c['box']
        for a_, b_ in c.get('faint_links', []):
            if a_ not in pos or b_ not in pos or a_ in hidden or b_ in hidden: continue
            n_ = 200; inside_pts = [(pos[a_][0] + (pos[b_][0] - pos[a_][0]) * k / n_, pos[a_][1] + (pos[b_][1] - pos[a_][1]) * k / n_) for k in range(n_ + 1)]
            inside_pts = [p for p in inside_pts if x0_ <= p[0] <= x1_ and y0_ <= p[1] <= y1_]
            if len(inside_pts) >= 2: faint_lines.append([[round(inside_pts[0][0], 2), round(inside_pts[0][1], 2)], [round(inside_pts[-1][0], 2), round(inside_pts[-1][1], 2)]])
    w['smrfaint'] = faint_lines
    road_s = _samples([_drawn(l) for l in w['etrtracks'] + road_lines if any(wx0 <= q[0] <= wx1 and wy0 <= q[1] <= wy1 for q in l)], 0.1)
    rtree = cKDTree(road_s) if len(road_s) else None
    ftree = cKDTree(_samples(faint_lines, 0.1)) if faint_lines else None
    marks = []
    for c in CL.get('boxes', []):
        if not c.get('rough_marks'): continue
        x0_, y0_, x1_, y1_ = c['box']; cand = []
        for gx_ in np.arange(x0_ + 0.45, x1_ - 0.4, 0.2):
            for gy_ in np.arange(y0_ + 0.45, y1_ - 0.4, 0.2):
                if ftree is not None and ftree.query([gx_, gy_])[0] < 0.42: continue
                if rtree is not None and rtree.query([gx_, gy_])[0] < 1.0: continue
                cand.append((gx_ + 0.16 * float(_hash(gx_, gy_, 5)) - 0.08, gy_ + 0.16 * float(_hash(gx_, gy_, 6)) - 0.08))
        placed_ = []
        for i in np.argsort(_hash([q[0] for q in cand], [q[1] for q in cand], 7), kind='stable'):
            x, y = cand[i]
            if all(math.dist((x, y), q) >= 0.8 for q in placed_): placed_.append((x, y))
        for x, y in placed_:
            marks.append([round(x, 2), round(y, 2), round(0.55 + 0.3 * float(_hash(x, y, 8)), 2), 'b' if float(_hash(x, y, 9)) < 0.4 else int(float(_hash(x, y, 10)) * 3)])
        report.setdefault('rough_marks', {})[c['name']] = len(placed_)
    # ---- towns (owner, Oct 14): a top-down village in the box; the streets are the paths that were there, its buildings are its rooms
    import ashen_forest as AF
    _names = AF._world()[0]
    towns = []; nboxes = len(CL.get('boxes', []))
    for ti, c in enumerate(CL.get('towns', [])):
        trng = random.Random(seed * 13 + ti)
        x0_, y0_, x1_, y1_ = c['box']; ins_ = 0.2
        nm = lambda v: _names[v]['name'] if v in _names else ''
        terr = lambda v: info[v].get('terrain') or ''
        inside = sorted(v for v in boxed[nboxes + ti] if v not in hidden)
        BW = re.compile(r'Shrine|Congregation|Sewer|Drain|Well|Bank|Shelter')
        street_room = lambda v: terr(v) == 'City' and not void(v) and not BW.search(nm(v))
        SG = defaultdict(set)
        for a, b in inner_e[nboxes + ti]:
            if street_room(a) and street_room(b): SG[a].add(b); SG[b].add(a)
        streets = _chains(SG, pos, set(), 0.6) if SG else []
        for ci, ln in enumerate(list(streets)):                                # a street that stops a few rooms short of another one (a hidden room between them) is joined to it
            for end in (ln[0], ln[-1]):
                best = None
                for cj, other in enumerate(streets):
                    if cj == ci: continue
                    q_ = _nearest_on([other], end); d_ = math.dist(q_, end)
                    if 0.05 < d_ <= 3.8 and (best is None or d_ < best[0]): best = (d_, q_)
                aligned = best and (abs(best[1][1] - end[1]) <= 1.2 and abs(best[1][0] - end[0]) >= 0.5 or abs(best[1][0] - end[0]) <= 1.2 and abs(best[1][1] - end[1]) >= 0.5)
                if aligned and not any(_nearest_on([[end, list(best[1])]], pos[v]) is not None and math.dist(_nearest_on([[end, list(best[1])]], pos[v]), pos[v]) < 0.6 for v in inside if not street_room(v) and not void(v) and not re.search(r'Well|Circle', nm(v))):
                    streets.append([[round(end[0], 2), round(end[1], 2)], [round(best[1][0], 2), round(best[1][1], 2)]])
        road_d = None; gate_d = None
        g_ = c.get('gate')
        if g_ and all(v in pos for v in g_['rooms']):                          # the grand road into the town (owner, Oct 14), from where the cartyard clearing ends, through the gate, to the first street
            gx_ = pos[g_['rooms'][1]][0]; gy_ = y0_ + 0.1                      # the gate stands in the town's north edge, over the spacer room; the road runs straight at it, then bends to the first street
            ys_ = pos[g_['rooms'][0]][1]
            for yy_ in np.arange(pos[g_['rooms'][0]][1], gy_, 0.04):            # where the road leaves the cartyard clearing (it starts 0.2 inside it, so the join is clean)
                c_, r_ = min(max(int((gx_ - wx0) * R8), 0), ww - 1), min(max(int((yy_ - wy0) * R8), 0), hw - 1)
                if not clearmask[r_, c_]: ys_ = yy_ - 0.2; break
            rend_ = pos[g_['rooms'][-1]]
            road_d = [[round(gx_, 2), round(ys_, 2)], [round(gx_, 2), round(gy_ + 1.0, 2)], [round(rend_[0], 2), round(rend_[1], 2)]]
            gate_d = {'x': round(gx_, 2), 'y': round(gy_, 2), 'w': 2.7}
            streets.append([[gate_d['x'], gate_d['y']]] + road_d[1:])        # (so filler houses keep clear of it)
        road2_d = None; gate2_d = None; gs_ = c.get('gate_s')
        if gs_ and gs_['room'] in pos and gs_['street_room'] in pos:            # the south gate (owner, Oct 14): a gatehouse in the town's south wall, a paved road from the street to the stone bridge
            bx_ = round(pos[gs_['room']][0] + 0.06, 2); r2 = pos[gs_['street_room']]
            road2_d = [[round(r2[0], 2), round(r2[1], 2)], [bx_, round(y1_ - 0.6, 2)], [bx_, gs_['bridge']['y0'] + 0.1]]
            gate2_d = {'x': bx_, 'y': round(y1_ - 0.1, 2), 'w': 2.7}
            streets.append([[bx_, gate2_d['y']]] + road2_d[1:])
            bg_ = gs_['bridge']; sm_ = {'x0': bx_ - 3.0, 'x1': bx_ + 3.0}
            w['smrbridge'] = list(w.get('smrbridge') or []) + [{'x': bx_, 'y0': bg_['y0'], 'y1': bg_['y1'], 'w': bg_['w']}]
            for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):
                w[k_] = [t for t in w[k_] if not (sm_['x0'] - 0.3 <= t[0] <= sm_['x1'] + 0.3 and bg_['y0'] - 0.3 <= t[1] <= bg_['y1'] + 0.3)]
        sst = _samples(streets, 0.1) if streets else np.zeros((0, 2))
        wells = [pos[v] for v in inside if re.search(r'Well|Circle', nm(v))]
        plaza = [round(sum(p[0] for p in wells) / len(wells), 2), round(sum(p[1] for p in wells) / len(wells), 2), 0.85] if wells else None
        def hits_street(cx, cy, hw_, hh_, pad=0.36):
            return len(sst) and bool(np.any((np.abs(sst[:, 0] - cx) < hw_ + pad) & (np.abs(sst[:, 1] - cy) < hh_ + pad)))
        def hits_plaza(cx, cy, hw_, hh_, pad=0.1):
            return plaza is not None and math.hypot(max(abs(cx - plaza[0]) - hw_, 0), max(abs(cy - plaza[1]) - hh_, 0)) < plaza[2] + pad
        blds = []
        def free_spot(cx, cy, hw_, hh_, gap=0.16):
            if cx - hw_ < x0_ + ins_ or cx + hw_ > x1_ - ins_ or cy - hh_ < y0_ + ins_ or cy + hh_ > y1_ - ins_: return False
            if hits_street(cx, cy, hw_, hh_) or hits_plaza(cx, cy, hw_, hh_): return False
            return all(abs(cx - b['x']) >= hw_ + b['w'] / 2 + gap or abs(cy - b['y']) >= hh_ + b['h'] / 2 + gap for b in blds)
        roofs = ['#7A4638', '#86503C', '#6B4A36', '#5F4B3A', '#7E5A40', '#704034']
        for v in inside:                                                       # the rooms that are buildings, where they are
            n_ = nm(v); t_ = terr(v)
            if re.search(r'Congregation', n_): k, w_, h_ = 'church', 1.1, 1.15
            elif re.search(r'Shrine', n_): k, w_, h_ = 'shrine', 0.62, 0.62
            elif re.search(r'Pick And Payload$', n_): k, w_, h_ = 'inn', 1.7, 1.05
            elif re.search(r'Shop|Smelter', n_): k, w_, h_ = 'shop', 0.95, 0.8
            elif re.search(r'Shelter', n_): k, w_, h_ = 'house', 0.75, 0.6
            elif t_ in ('Inside', 'DHinside3'): k, w_, h_ = 'house', 0.95, 0.8
            else: continue
            cx, cy = pos[v]
            cx = min(max(cx, x0_ + ins_ + w_ / 2), x1_ - ins_ - w_ / 2); cy = min(max(cy, y0_ + ins_ + h_ / 2), y1_ - ins_ - h_ / 2)
            if hits_street(cx, cy, w_ / 2, h_ / 2):                            # nudge it off a street by the smallest step
                for step in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
                    alt = [(cx + dx, cy + dy) for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step))]
                    ok_ = [p for p in alt if not hits_street(p[0], p[1], w_ / 2, h_ / 2) and x0_ + ins_ + w_ / 2 <= p[0] <= x1_ - ins_ - w_ / 2 and y0_ + ins_ + h_ / 2 <= p[1] <= y1_ - ins_ - h_ / 2]
                    if ok_: cx, cy = ok_[0]; break
            blds.append({'x': round(cx, 2), 'y': round(cy, 2), 'w': w_, 'h': h_, 'k': k, 'roof': '#5E5B55' if k == 'church' else '#6A3C30' if k == 'inn' else trng.choice(roofs), 'room': v})
        nfixed = len(blds)
        cand = []                                                              # filler houses along the streets, both sides
        for ln in streets:
            for (p, q) in zip(ln[:-1], ln[1:]):
                L_ = math.dist(p, q)
                if L_ < 0.05: continue
                tx, ty = (q[0] - p[0]) / L_, (q[1] - p[1]) / L_; horiz = abs(tx) >= abs(ty)
                for s_ in np.arange(0.3, L_, 1.3):
                    for side in (-1, 1):
                        cand.append((p[0] + tx * s_ - ty * side * 1.05, p[1] + ty * s_ + tx * side * 1.05, horiz))
        trng.shuffle(cand); nfill = 0
        for cx, cy, horiz in cand:
            if nfill >= 10: break
            w_, h_ = (trng.uniform(0.8, 1.05), trng.uniform(0.62, 0.8)) if horiz else (trng.uniform(0.62, 0.8), trng.uniform(0.8, 1.05))
            if free_spot(cx, cy, w_ / 2, h_ / 2): blds.append({'x': round(cx, 2), 'y': round(cy, 2), 'w': round(w_, 2), 'h': round(h_, 2), 'k': 'house', 'roof': trng.choice(roofs), 'room': None}); nfill += 1
        trees = []
        for _ in range(60):
            if len(trees) >= 7: break
            cx, cy, r_ = trng.uniform(x0_ + 0.4, x1_ - 0.4), trng.uniform(y0_ + 0.4, y1_ - 0.4), trng.uniform(0.26, 0.38)
            if free_spot(cx, cy, r_, r_, 0.22) and all(math.dist((cx, cy), (q[0], q[1])) > 1.0 for q in trees): trees.append([round(cx, 2), round(cy, 2), round(r_, 2)])
        towns.append({'name': c['name'], 'ground': [x0_ + 0.12, y0_ + 0.12, x1_ - 0.12, y1_ - 0.12], 'streets': streets, 'plaza': plaza, 'buildings': blds, 'trees': trees, 'road': road_d, 'road2': road2_d, 'gate_s': gate2_d, 'road_w': (g_ or {}).get('width', 0.95), 'gate': gate_d})
        lab = c.get('label') or [(x0_ + x1_) / 2, y0_ - 0.5]
        w['tags'] = list(w['tags']) + [[lab[0], lab[1], c['name'], 0.95]]
        for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):         # nothing grows or stands where the village is
            w[k_] = [t for t in w[k_] if not (x0_ <= t[0] <= x1_ and y0_ <= t[1] <= y1_)]
        report.setdefault('towns', {})[c['name']] = {'road': road_d, 'gate': gate_d, 'rooms_inside': len(inside), 'streets': len(streets), 'buildings_from_rooms': nfixed, 'filler_houses': nfill, 'trees': len(trees), 'plaza': plaza}
    w['smrtowns'] = towns
    # ---- a climb: one wide path through the four rooms with slight rocky steps across it (owner, Oct 14: a regular but wide path, not a mountain); it stops at clearings too
    climbs = []; climbmask = np.zeros((hw, ww), bool)
    for c in CL.get('climbs', []):
        pts = [pos[v] for v in c['rooms']]
        im = Image.new('L', (ww, hw), 0); ImageDraw.Draw(im).polygon([px(p) for p in pts], fill=255, outline=255)
        m = ndi.binary_dilation(np.array(im, bool), structure=disk(int(0.55 * R8))) & ~ndi.binary_dilation(dmask, structure=disk(1))
        m = ndi.gaussian_filter(m.astype(float), 0.5 * R8) > 0.5
        polys = AA._contours(m, wx0, wy0, sigma=1.0, tol=0.3, minarea=0.5)
        ys_, xs_ = np.nonzero(m); y_lo, y_hi = ys_.min() / R8 + wy0, ys_.max() / R8 + wy0
        steps = []
        for gy_ in np.arange(y_lo + 0.55, y_hi - 0.3, 0.9):                       # a tread across the path every ~0.9 rooms, not quite edge to edge, a little uneven
            row = np.nonzero(m[int((gy_ - wy0) * R8)])[0]
            if len(row) < 6: continue
            xa, xb = row.min() / R8 + wx0 + 0.4, row.max() / R8 + wx0 - 0.4
            if xb - xa > 0.6: steps.append([round(xa + rng.uniform(0, 0.25), 2), round(gy_ + rng.uniform(-0.04, 0.04), 2), round(xb - rng.uniform(0, 0.25), 2), round(gy_ + rng.uniform(-0.04, 0.04), 2)])
        climbmask |= m
        climbs.append({'name': c['name'], 'polys': polys, 'steps': steps})
        report.setdefault('climbs', {})[c['name']] = {'sq': round(float(m.sum()) / R8 / R8, 1), 'steps': len(steps)}
    w['smrclimb'] = climbs; w['smrmarks'] = marks
    pads = []
    for a, b in LINKS:                                                              # off-ramp pads: where the route meets anything that is not the route
        for v, o in ((a, b), (b, a)):
            if v in TRT and o not in TRT: pads.append(end_(v))
    pads = [list(p) for p in sorted({tuple(p) for p in pads})]
    w['smrpatch'] = dpatch; w['roadpatch'] = rpatch
    w['fwtracks'] = list(w['fwtracks']) + dirt_lines + link_lines + vis_c
    w['etrtracks'] = list(w['etrtracks']) + road_lines
    w['ntrjoins'] = list(w['ntrjoins']) + pads
    report['dirt'] = {'cells': len(dadj), 'patches': len(dpatch), 'patch_sq': round(float(dwide.sum()) / R8 / R8, 1), 'trail_lines': len(dirt_lines)}
    report['road'] = {'cells': len(radj), 'patches': len(rpatch), 'patch_sq': round(float(rwide.sum()) / R8 / R8, 1), 'road_lines': len(road_lines), 'pads': len(pads), 'pad_was_off_the_road_by': offs}
    report['links_drawn'] = len(link_lines) - len([1 for a, b in UDL if math.dist(pos[a], pos[b]) <= 30]); report['links_over_30'] = far
    report['up_down_exits']['drawn'] = len([1 for a, b in UDL if math.dist(pos[a], pos[b]) <= 30])

    # ---------------------------------------------------------------- the paths as a raster (land margin, sprite clearance)
    pim = Image.new('L', (ww, hw), 0); pd = ImageDraw.Draw(pim)
    for G in (GS, GT):
        for a in G:
            for b in G[a]:
                if a < b: pd.line([px(pos[a]), px(pos[b])], fill=255, width=2)
    for a, b in LINKS + UDL: pd.line([px(pos[a]), px(pos[b])], fill=255, width=2)
    for U_ in CL.get('undergrounds', []):                                      # land round the tunnel and its branches (no gap of open ground)
        chain_ = [U_['path']] + [b_['rooms'] for b_ in U_.get('branches', [])]
        for ch_ in chain_:
            for a_, b_ in zip(ch_, ch_[1:]):
                if a_ in pos and b_ in pos: pd.line([px(pos[a_]), px(pos[b_])], fill=255, width=2)
    if vis:
        for p, q in zip(vis, vis[1:]): pd.line([px(p), px(q)], fill=255, width=2)
    for v in onmap:
        p = px(pos[v]); pd.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=255)
    skel = np.array(pim, bool)
    d_path = ndi.distance_transform_edt(~(skel | dwide | rwide | climbmask)) / R8

    # ---------------------------------------------------------------- the land
    land0 = AA._raster(w['geo']['land'], X0, YN, W, int((wy1 + 40 - YN) * R8))           # (the grid reaches 40 rooms below the window)
    water0 = AA._raster(w['geo']['water'], X0, YN, W, int((wy1 + 40 - YN) * R8))
    c0, r0 = int((wx0 - X0) * R8), int((wy0 - YN) * R8)
    sub = (slice(r0, r0 + hw), slice(c0, c0 + ww))
    wob = ndi.gaussian_filter(nrng.normal(size=(hw, ww)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    near = d_path <= LAND_R * (0.7 + 0.6 * wob)
    near = ndi.binary_closing(near, structure=np.ones((3, 3), bool), iterations=int(1.5 * R8))
    near = ndi.binary_fill_holes(near)
    near = ndi.gaussian_filter(near.astype(float), 0.8 * R8) > 0.5
    new_land = near & ~water0[sub]
    before = float(land0.sum()) / R8 / R8
    land_n = land0.copy(); land_n[sub] |= new_land
    added = land_n & ~land0
    lab, n = ndi.label(added)
    report['land_new_sq'] = round(float(added.sum()) / R8 / R8, 1); report['land_new_pieces'] = int(n)
    nland = AA._contours(land_n, X0, YN)
    # (land beyond the traced rows is kept as it was)
    keep = []
    cut_y = YN + land_n.shape[0] / R8
    for p in w['geo']['land']:
        if min(q[1] for q in p) >= cut_y - 1e-6: keep.append(p)
    w['geo']['land'] = nland + keep
    report['land_sq_before_after'] = (round(before), round(float(land_n.sum()) / R8 / R8))

    # ---------------------------------------------------------------- terrain: tints and sprites, from the rooms' own terrain
    real = [v for v in onmap if not void(v) and v in DOM and (info[v].get('terrain') or '') != 'Underground']       # (the underground rooms do not set the terrain above them)
    cls = {'Mountains': 'm', 'Hills': 'h', 'Forest': 'd'}
    tree = cKDTree(np.array([pos[v] for v in real])); lab_t = [info[v].get('terrain') or '' for v in real]
    P = np.c_[WXg.ravel(), WYg.ravel()]
    dist, idx = tree.query(P)
    tcls = np.array([cls.get(t, '') for t in lab_t], dtype='U1')[idx].reshape(hw, ww)
    dist = dist.reshape(hw, ww)
    landw = land_n[sub]
    band = np.zeros((hw, ww), bool)
    if vis:                                                                    # standard forest round the connection and the trail on to 2864: ground, trees; no other tint
        bl = [vis, [vis[-1], [round(pos[2864][0], 2), round(pos[2864][1], 2)]]]
        dv = cKDTree(_samples(bl, 0.1)).query(np.c_[WXg.ravel(), WYg.ravel()])[0].reshape(hw, ww)
        band = (dv <= BAND * (0.7 + 0.6 * wob)) & landw & ~water0[sub]
        band = ndi.gaussian_filter(band.astype(float), 0.6 * R8) > 0.5
    on = landw & (dist <= TERR_R)
    mount = on & (tcls == 'm') & ~band
    bar = ndi.gaussian_filter(mount.astype(float), 0.6 * R8) > 0.5
    nz = ndi.gaussian_filter(nrng.normal(size=(hw, ww)), 1.4 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    bar2 = bar & (nz > 0.58)
    w['geo']['barren'] = list(w['geo'].get('barren') or []) + AA._contours(bar, wx0, wy0, sigma=2.0)
    w['geo']['barren2'] = list(w['geo'].get('barren2') or []) + AA._contours(bar2, wx0, wy0, sigma=2.0)
    free = landw & (d_path > CLEAR) & ~water0[sub] & ~townmask
    forest = {'trees': 0, 'fill_sq': 0.0, 'old_trees_cleared': 0, 'old_tufts_cleared': 0, 'tints_clipped': {}}
    if vis:
        for k, ks in (('trees', 'old_trees_cleared'), ('tufts', 'old_tufts_cleared')):         # what was growing there is cleared (gotcha 2); the standard forest replaces it
            keep_, n_ = [], 0
            for t in w[k]:
                c_, r_ = int((t[0] - wx0) * R8), int((t[1] - wy0) * R8)
                if 0 <= r_ < hw and 0 <= c_ < ww and band[r_, c_]: n_ += 1
                else: keep_.append(t)
            w[k] = keep_; forest[ks] = n_
        for k in ('ash', 'dread', 'dread2', 'sparse', 'deep', 'bog', 'sand', 'shallows', 'blight', 'black', 'blackheart', 'bramble', 'doom'):    # other ground tints are taken out of the band (a polygon on top of the tint, drawn even-odd, is a hole)
            polys = w['geo'].get(k) or []
            if not polys: continue
            inter = band & AA._raster([p for p in polys if any(wx0 <= q[0] < wx1 and wy0 <= q[1] < wy1 for q in p)], wx0, wy0, ww, hw)
            if inter.sum() > 0:
                w['geo'][k] = list(polys) + AA._contours(inter, wx0, wy0, sigma=1.0, minarea=0.1); forest['tints_clipped'][k] = round(float(inter.sum()) / R8 / R8, 1)
        w['geo']['fill'] = list(w['geo'].get('fill') or []) + AA._contours(band, wx0, wy0, sigma=2.0)
        forest['fill_sq'] = round(float(band.sum()) / R8 / R8, 1)
        ys, xs = np.nonzero(band & free); placed = []; gridc = {}
        for i in np.argsort(_hash(WXg[ys, xs], WYg[ys, xs], 21), kind='stable'):
            x, y = WXg[ys[i], xs[i]], WYg[ys[i], xs[i]]; gk = (int(x // 1.0), int(y // 1.0)); ok = True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if any(math.dist(q, (x, y)) < 1.0 for q in gridc.get((gk[0] + dx, gk[1] + dy), ())): ok = False
            if ok: gridc.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
        w['trees'] = list(w['trees']) + [[x, y, round(0.85 + 0.3 * float(_hash(x, y, 2)), 2), ['w', 'w', 'd'][int(float(_hash(x, y, 4)) * 3)], int(float(_hash(x, y, 3)) * 3)] for x, y in placed]
        forest['trees'] = len(placed)
        free &= ~band                                                          # (no hills / peaks sprites inside the forest band)
    report['ashen_connection']['forest'] = forest
    out = {'m': [], 'h': [], 'd': []}
    for c in ('m', 'h', 'd'):
        ys, xs = np.nonzero(on & (tcls == c) & free)
        order = np.argsort(_hash(WXg[ys, xs], WYg[ys, xs], 11 + ord(c)), kind='stable'); placed = []; gridc = {}
        cs = SPRITE[c]
        for i in order:
            x, y = WXg[ys[i], xs[i]], WYg[ys[i], xs[i]]; gk = (int(x // cs), int(y // cs)); ok = True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for q in gridc.get((gk[0] + dx, gk[1] + dy), ()):
                        if math.dist(q, (x, y)) < cs: ok = False; break
                    if not ok: break
                if not ok: break
            if ok: gridc.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
        out[c] = placed
    w['peaks'] = list(w['peaks']) + [[x, y, round(0.9 + 0.35 * float(_hash(x, y, 2)), 2), 'm', [0, 0, 1, 1, 2][int(float(_hash(x, y, 3)) * 5)]] for x, y in out['m']]
    w['hills'] = list(w['hills']) + [[x, y, round(0.85 + 0.35 * float(_hash(x, y, 2)), 2), 'h', int(float(_hash(x, y, 3)) * 3)] for x, y in out['h']]
    w['trees'] = list(w['trees']) + [[x, y, round(0.85 + 0.3 * float(_hash(x, y, 2)), 2), 'd', int(float(_hash(x, y, 3)) * 3)] for x, y in out['d']]
    report['terrain'] = {'barren_sq': round(float(bar.sum()) / R8 / R8, 1), 'peaks': len(out['m']), 'hills': len(out['h']), 'trees': len(out['d'])}

    # ---- the Darkhaven River's tunnel (owner, Oct 14): an underground river, shown as if seen through the ground
    def catmull(P_, n=10):
        P_ = [np.array(p, float) for p in P_]; ext = [2 * P_[0] - P_[1]] + P_ + [2 * P_[-1] - P_[-2]]; out = []
        for i in range(1, len(ext) - 2):
            p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
            for k in range(n):
                t = k / n; out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        out.append(ext[-2]); return np.array(out)
    unders = []
    for U in CL.get('undergrounds', []):
        pr = U['path']
        if not all(v in pos for v in pr): continue
        mouth = np.array([pos[pr[0]][0], pos[pr[0]][1] + 0.45])                    # the river goes in a little south of room 1's centre
        far = np.array(pos[pr[-1]]); prev_ = np.array(pos[pr[-2]]); ud_ = (prev_ - far) / (np.linalg.norm(prev_ - far) or 1)    # from the far end toward the tunnel (north-east)
        key = [mouth] + [np.array(pos[v]) for v in pr[1:-1]] + [far + ud_ * 0.3]     # (the tunnel mouth at the far end sits 0.9 beyond the waterfall room)
        dense = catmull(key, 12); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(dense, axis=0).T))]
        kidx = [0] + [int(np.argmin(np.hypot(*(dense - np.array(pos[v])).T))) for v in pr[1:-1]] + [len(dense) - 1]
        RW = {pr[0]: 0.55, 22559: 0.5, 2: 0.8, 3: 0.42, 4: 0.6, 5: 0.6, 11: 0.55, 12: 0.72, pr[-1]: 0.8}
        kw = [0.55] + [RW.get(v, 0.5) for v in pr[1:-1]] + [0.8]
        rw = np.interp(seg, [seg[i] for i in kidx], kw)
        tan = np.gradient(dense, axis=0); tan /= np.maximum(np.hypot(*tan.T), 1e-9)[:, None]; nor = np.c_[-tan[:, 1], tan[:, 0]]
        wt = rw + 0.75                                                           # the tunnel is a little wider than its river
        at = lambda v: int(np.argmin(np.hypot(*(dense - np.array(pos[v])).T)))
        rnd = lambda arr: [[round(float(x), 2), round(float(y), 2)] for x, y in arr]
        riv = rnd(np.r_[dense + nor * (rw / 2)[:, None], (dense - nor * (rw / 2)[:, None])[::-1]]); band = rnd(np.r_[dense + nor * (wt / 2)[:, None], (dense - nor * (wt / 2)[:, None])[::-1]])
        wl = rnd(dense + nor * (wt / 2)[:, None]); wr = rnd(dense - nor * (wt / 2)[:, None])
        core = rnd(np.r_[dense + nor * (rw * 0.18)[:, None], (dense - nor * (rw * 0.18)[:, None])[::-1]])
        chev = []                                                                # faint arrows: the water runs toward the mouth at room 1
        for k in range(8, len(dense) - 8, 18):
            p_, t_ = dense[k], tan[k]; n_ = nor[k]
            chev.append([[round(float(p_[0] - t_[0] * 0.16 + n_[0] * 0.13), 2), round(float(p_[1] - t_[1] * 0.16 + n_[1] * 0.13), 2)], [round(float(p_[0] - t_[0] * 0.0), 2), round(float(p_[1] - t_[1] * 0.0), 2)], [round(float(p_[0] - t_[0] * 0.16 - n_[0] * 0.13), 2), round(float(p_[1] - t_[1] * 0.16 - n_[1] * 0.13), 2)]])
        # features, from the rooms' own descriptions
        ft = {}
        i5 = at(U['lake']); ft['lake'] = {'x': round(float(pos[U['lake']][0]) - 0.1, 2), 'y': round(float(pos[U['lake']][1]) + 0.1, 2), 'rx': 1.5, 'ry': 1.05, 'a': round(float(np.degrees(np.arctan2(tan[i5][1], tan[i5][0]))), 1)}
        g6 = pos[U['grotto']]; ft['grotto'] = {'x': round(g6[0], 2), 'y': round(g6[1], 2), 'r': 1.0, 'lake': [round(pos[U['lake']][0], 2), round(pos[U['lake']][1], 2)], 'surface': [round(pos[U['surface_exit']][0], 2), round(pos[U['surface_exit']][1], 2)] if U.get('surface_exit') in pos and math.dist(pos[U['surface_exit']], g6) < 14 else None}
        i3 = at(U['rapids']); ft['rapids'] = [[round(float(dense[k][0]), 2), round(float(dense[k][1]), 2), round(float(np.degrees(np.arctan2(tan[k][1], tan[k][0]))), 1)] for k in range(max(0, i3 - 6), min(len(dense), i3 + 7), 3)]
        i4 = at(U['rain']); rain = []
        for k in range(9):
            t_ = (k - 4) / 4.0; q_ = dense[i4] + nor[i4] * t_ * 0.55 + tan[i4] * (((k * 37) % 7) - 3) * 0.13
            rain.append([round(float(q_[0]), 2), round(float(q_[1]), 2)])
        ft['rain'] = rain
        st = []
        i11, i12, i5b = at(U['stalactites'][0]), at(U['stalactites'][1]), at(U['lake'])
        for k in range(min(i11, i12) - 4, max(i11, i12) + 5, 2):
            for sd in (-1, 1):
                if 0 <= k < len(dense): q_ = dense[k] + nor[k] * sd * (wt[k] / 2 - 0.09); st.append([round(float(q_[0]), 2), round(float(q_[1]), 2), round(0.07 + 0.05 * float(_hash(q_[0], q_[1], 31)), 2), sd])
        ft['stalactites'] = st
        ft['fall'] = {'x': round(float(far[0]), 2), 'y': round(float(far[1]), 2), 'dx': round(float(ud_[0]), 3), 'dy': round(float(ud_[1]), 3)}
        ft['exit_mouth'] = {'x': round(float(far[0] + ud_[0] * 0.3), 2), 'y': round(float(far[1] + ud_[1] * 0.3), 2), 'dx': round(float(ud_[0]), 3), 'dy': round(float(ud_[1]), 3)}
        ft['bend'] = {'x': round(float(pos[U['bend']][0]), 2), 'y': round(float(pos[U['bend']][1]), 2)}
        brs = []
        for B_ in U.get('branches', []):
            rm_ = B_['rooms']
            if not all(v in pos for v in rm_): continue
            pts_ = [np.array(pos[v], float) for v in rm_]; mid_ = []
            if len(pts_) == 2:                                                      # a gentle wander between the two rooms
                d_ = pts_[1] - pts_[0]; L_ = float(np.linalg.norm(d_)); n_ = np.array([-d_[1], d_[0]]) / (L_ or 1)
                for f_ in (0.33, 0.66): mid_.append(pts_[0] + d_ * f_ + n_ * (float(_hash(pts_[0][0] + f_, pts_[0][1], 41)) - 0.5) * 0.7)
                pts_ = [pts_[0]] + mid_ + [pts_[1]]
            dn_ = catmull(pts_, 12); sg_ = np.r_[0, np.cumsum(np.hypot(*np.diff(dn_, axis=0).T))]
            tn_ = np.gradient(dn_, axis=0); tn_ /= np.maximum(np.hypot(*tn_.T), 1e-9)[:, None]; nr_ = np.c_[-tn_[:, 1], tn_[:, 0]]
            wr_ = np.full(len(dn_), B_['width']) * (1 + 0.1 * np.sin(sg_ * 2.3)); wt2_ = wr_ + (0.75 if B_['kind'] == 'water' else 0.55)
            br = {'kind': B_['kind'], 'band': rnd(np.r_[dn_ + nr_ * (wt2_ / 2)[:, None], (dn_ - nr_ * (wt2_ / 2)[:, None])[::-1]]), 'floor': rnd(np.r_[dn_ + nr_ * (wr_ / 2)[:, None], (dn_ - nr_ * (wr_ / 2)[:, None])[::-1]]),
                  'wall_l': rnd(dn_ + nr_ * (wt2_ / 2)[:, None]), 'wall_r': rnd(dn_ - nr_ * (wt2_ / 2)[:, None])}
            if B_['kind'] == 'water': br['core'] = rnd(np.r_[dn_ + nr_ * (wr_ * 0.18)[:, None], (dn_ - nr_ * (wr_ * 0.18)[:, None])[::-1]])
            else:
                br['rocks'] = []                                                   # a dry cavern: loose rocks and a few stalagmites on its floor
                for k in range(4, len(dn_) - 4, 5):
                    sd_ = 1 if (k // 5) % 2 else -1; q_ = dn_[k] + nr_[k] * sd_ * wr_[k] * 0.28 * (0.4 + float(_hash(dn_[k][0], dn_[k][1], 43)))
                    br['rocks'].append([round(float(q_[0]), 2), round(float(q_[1]), 2), round(0.04 + 0.05 * float(_hash(q_[0], q_[1], 45)), 2)])
            if B_.get('mouth') in pos:
                tl_ = tn_[-1]; br['mouth'] = {'x': round(float(pos[B_['mouth']][0]), 2), 'y': round(float(pos[B_['mouth']][1]), 2), 'a': round(float(np.degrees(np.arctan2(tl_[1], tl_[0]))), 1)}
                for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):
                    w[k_] = [t for t in w[k_] if not (abs(t[0] - pos[B_['mouth']][0]) < 0.9 and abs(t[1] - pos[B_['mouth']][1]) < 0.9)]
            brs.append(br)
        ft['grotto']['surface'] = None
        unders.append({'name': U['name'], 'band': band, 'river': riv, 'core': core, 'wall_l': wl, 'wall_r': wr, 'chev': chev, 'mouth': {'x': round(float(pos[pr[0]][0]), 2), 'y': round(float(pos[pr[0]][1]) + 0.55, 2)}, 'features': ft, 'branches': brs})
        report.setdefault('undergrounds', {})[U['name']] = {'length': round(float(seg[-1]), 1), 'points': len(dense), 'rooms_not_drawn_as_path': sorted(tun_rooms), 'features': sorted(ft)}
        for k_ in ('trees', 'tufts'):                                            # nothing grows on the cave mouths / waterfall
            for ax, ay in ((pos[pr[0]][0], pos[pr[0]][1] + 0.5), (far[0], far[1])):
                w[k_] = [t for t in w[k_] if not (abs(t[0] - ax) < 1.1 and abs(t[1] - ay) < 1.1)]
    w['smrunder'] = unders
    # ---- the river beyond the falls (owner, Oct 14): a stream (a little wider than a path) from room 13 down past Edel; at room 120 a still pool, then flooded ground (125), then marsh (126)
    R_ = CL.get('river')
    if R_ and all(v in pos for v in R_['rooms'] + [R_['flood'], R_['marsh']]):
        rr_ = random.Random(seed * 17 + 5)
        keyp = [np.array(pos[v]) for v in R_['rooms'][:-1]]
        dense = catmull(keyp, 10); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(dense, axis=0).T))]
        wbase = R_['width']
        kk_ = [int(np.argmin(np.hypot(*(dense - np.array(pos[v])).T))) for v in (R_['widen_from'], R_['pool'], R_['flood'])]
        sk_ = [seg[k] for k in kk_]
        wd_ = wbase * (1 + 0.18 * np.sin(seg * 1.7)) * np.interp(seg, [0, 1.5, sk_[0] - 1.0, sk_[0], sk_[1], sk_[2]], [0.55, 1.0, 1.0, 1.0, 1.6, 3.4])   # a thread at the falls; wider from room 119 into the pool; spreading into the flood
        px_, py_ = pos[R_['pool']]; fx_, fy_ = pos[R_['flood']]; mx_, my_ = pos[R_['marsh']]
        def blob(cx, cy, rx, ry, amp, n=28, rot=0.0):
            out = []; ph = [rr_.uniform(0, 6.28) for _ in range(3)]
            for k in range(n):
                a = 2 * math.pi * k / n; f = 1 + amp * (math.sin(2 * a + ph[0]) * 0.5 + math.sin(3 * a + ph[1]) * 0.3 + math.sin(5 * a + ph[2]) * 0.2)
                x_, y_ = rx * f * math.cos(a), ry * f * math.sin(a)
                out.append([round(cx + x_ * math.cos(rot) - y_ * math.sin(rot), 2), round(cy + x_ * math.sin(rot) + y_ * math.cos(rot), 2)])
            return out
        pool = blob(px_, py_, 1.25, 0.8, 0.12, 24)
        flood = blob(fx_ - 0.6, fy_ - 0.3, 2.5, 1.5, 0.22, 32, -0.5)                  # the flooded ground: wide, shallow, ragged
        marsh_g = blob(mx_ - 0.2, my_ + 0.1, 2.6, 1.7, 0.25, 32, -0.5)                 # the marsh the river is lost in
        puddles = []
        for _ in range(9):
            a = rr_.uniform(0, 6.28); r_ = math.sqrt(rr_.random()) * 1.6; puddles.append([round(mx_ - 0.2 + math.cos(a) * r_ * 1.5, 2), round(my_ + 0.1 + math.sin(a) * r_ * 0.95, 2), round(rr_.uniform(0.18, 0.42), 2), round(rr_.uniform(0.1, 0.22), 2)])
        reeds = []
        for _ in range(26):
            a = rr_.uniform(0, 6.28); r_ = math.sqrt(rr_.random()); reeds.append([round(mx_ - 0.2 + math.cos(a) * r_ * 2.4, 2), round(my_ + 0.1 + math.sin(a) * r_ * 1.5, 2)])
        for _ in range(10):
            a = rr_.uniform(0, 6.28); reeds.append([round(fx_ - 0.6 + math.cos(a) * 2.2, 2), round(fy_ - 0.3 + math.sin(a) * 1.3, 2)])
        w['smrriver'] = {'pts': [[round(float(x), 2), round(float(y), 2), round(float(wv), 2)] for (x, y), wv in zip(dense, wd_)], 'pool': pool, 'flood': flood, 'marsh': marsh_g, 'puddles': puddles, 'reeds': reeds, 'ends': [round(px_, 2), round(py_, 2)]}
        for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):
            w[k_] = [t for t in w[k_] if not any(math.hypot(t[0] - gx, t[1] - gy) < gr for gx, gy, gr in ((px_, py_, 1.9), (fx_ - 0.6, fy_ - 0.3, 3.4), (mx_ - 0.2, my_ + 0.1, 3.6)))]
        report['river'] = {'length': round(float(seg[-1]), 1), 'rooms': R_['rooms'] + [R_['flood'], R_['marsh']]}
    # ---- canyons (owner, Oct 14): a top-down view of a deep canyon: steep terraced rock walls round a shadowed floor, a harrowing ledge path with hairpins and small caves from the top entrance (south) down to the base (north)
    cany = []
    for C_ in CL.get('canyons', []):
        x0_, y0_, x1_, y1_ = C_['box']; crng = random.Random(seed * 19 + 3)
        def rrect(xa, ya, xb, yb, amp, n=72, pw=5.0):
            cx, cy, a_, b_ = (xa + xb) / 2, (ya + yb) / 2, (xb - xa) / 2, (yb - ya) / 2; ph = [crng.uniform(0, 6.28) for _ in range(3)]; out = []
            for k in range(n):
                t = 2 * math.pi * k / n; ct, st = math.cos(t), math.sin(t); f = 1 + amp * (math.sin(5 * t + ph[0]) * .5 + math.sin(9 * t + ph[1]) * .3 + math.sin(14 * t + ph[2]) * .2)
                out.append([round(cx + a_ * f * math.copysign(abs(ct) ** (2 / pw), ct), 2), round(cy + b_ * f * math.copysign(abs(st) ** (2 / pw), st), 2)])
            return out
        ins = [(0.05, 0.0, 0.05), (0.5, 0.1, 1.0), (1.0, 0.2, 1.6), (1.5, 0.3, 2.2), (2.0, 0.4, 2.8), (2.5, 0.5, 3.4)]      # (west/east, north, south) insets: the walls close in toward a narrow floor in the north
        cols = ['#7A6347', '#8B7455', '#75604A', '#5E4F3E', '#483D31', '#352D25']
        levels = []
        for k, (dw, dn, ds) in enumerate(ins):
            poly = rrect(x0_ + dw, y0_ + dn - (0.25 if k == 0 else 0), x1_ - dw, y1_ - ds, 0.045 + 0.01 * k)
            cxm = sum(q[0] for q in poly) / len(poly); cym = sum(q[1] for q in poly) / len(poly); hatch = []
            for (a, b) in zip(poly, poly[1:] + poly[:1]):
                L_ = math.dist(a, b)
                for sx in np.arange(0.1, L_, 0.21):
                    q = (a[0] + (b[0] - a[0]) * sx / L_, a[1] + (b[1] - a[1]) * sx / L_); d_ = np.array([cxm - q[0], cym - q[1]]); d_ /= (np.linalg.norm(d_) or 1); ln = crng.uniform(0.14, 0.3)
                    hatch.append([round(q[0], 2), round(q[1], 2), round(q[0] + d_[0] * ln, 2), round(q[1] + d_[1] * ln, 2)])
            levels.append({'poly': poly, 'fill': cols[k], 'hatch': hatch})
        fx_ = (x0_ + x1_) / 2 + 0.1                                                  # the floor: a shadowed slot that runs out of the canyon at the base entrance (north)
        floor = [[fx_ - 0.75, 25.4], [fx_ - 0.6, 24.5], [fx_ - 0.42, 23.6], [fx_ - 0.4, 22.6], [fx_ + 0.4, 22.6], [fx_ + 0.45, 23.5], [fx_ + 0.7, 24.5], [fx_ + 0.85, 25.4], [fx_ + 0.4, 25.85], [fx_ - 0.4, 25.85]]
        lo, hi = pos[C_['low']], pos[C_['high']]
        ledge = [[round(hi[0], 2), round(hi[1], 2)], [fx_ + 1.65, 27.8], [fx_ - 1.45, 27.4], [fx_ + 1.3, 26.95], [fx_ - 1.3, 26.55], [fx_ + 0.8, 26.2], [fx_ - 0.7, 25.9], [fx_ + 0.05, 25.55]]
        ledge = [[round(a, 2), round(b, 2)] for a, b in ledge]
        segs = []                                                                    # the ledge, a wandering line per stretch; the narrowest stretches are thin and broken
        for i, (a, b) in enumerate(zip(ledge, ledge[1:])):
            dv = np.array(b) - np.array(a); nv = np.array([-dv[1], dv[0]]) / (np.linalg.norm(dv) or 1); pl = [a]
            for f_ in (0.2, 0.4, 0.6, 0.8): pl.append([round(a[0] + dv[0] * f_ + nv[0] * crng.uniform(-.07, .07), 2), round(a[1] + dv[1] * f_ + nv[1] * crng.uniform(-.07, .07), 2)])
            segs.append({'pts': pl + [b], 'thin': i in (2, 4)})
        caves = []
        for i, q in enumerate(ledge[1:-1], 1):
            sd = 1 if q[0] > fx_ else -1; caves.append([round(q[0] + sd * 0.24, 2), round(q[1] - 0.02, 2), round(0.09 + 0.025 * (i % 3), 2), 0 if sd > 0 else 180])
        caves = caves[:5]; caves += [[round(x1_ - 0.55, 2), 26.0, 0.11, 0], [round(x0_ + 0.5, 2), 27.4, 0.1, 180]]
        rocks = []
        for _ in range(26):
            rx_, ry_ = crng.uniform(x0_ + 0.3, x1_ - 0.3), crng.uniform(y0_ + 0.6, y1_ - 0.3)
            if any(math.dist((rx_, ry_), q) < 0.45 for q in ledge): continue
            rocks.append([round(rx_, 2), round(ry_, 2), round(crng.uniform(.04, .1), 2)])
        cany.append({'name': C_['name'], 'levels': levels, 'floor': [[round(a, 2), round(b, 2)] for a, b in floor], 'ledge': segs, 'caves': caves, 'rocks': rocks, 'pads': [[round(hi[0], 2), round(hi[1], 2)], [round(lo[0], 2), 23.1]]})
        for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):
            w[k_] = [t for t in w[k_] if not (x0_ - 0.2 <= t[0] <= x1_ + 0.2 and y0_ - 0.2 <= t[1] <= y1_ + 0.2)]
        report.setdefault('canyons', {})[C_['name']] = {'levels': len(levels), 'hatch': sum(len(l['hatch']) for l in levels), 'ledge_points': len(ledge), 'caves': len(caves)}
    w['smrcanyon'] = cany
    # ---- inns (owner, Oct 14): an inn graphic like the Ashen Forest Inn's, with a small label; its rooms are not drawn as road
    for inn in CL.get('inns', []):
        x, y = inn['x'], inn['y']
        w['gfx'] = list(w['gfx']) + [{'k': 'inn', 'at': 'xy', 'x': x, 'y': y, 'w': 2.3, 'h': 2.0}, {'k': 'text', 'at': 'xy', 'x': x, 'y': round(y + inn.get('label_dy', 2.9), 2), 'text': inn['name']}]
        for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):         # nothing grows under it
            w[k_] = [t for t in w[k_] if not (abs(t[0] - x) < 1.5 and abs(t[1] - y) < 1.4)]
        report.setdefault('inns', {})[inn['name']] = {'at': [x, y], 'rooms_not_drawn_as_road': inn['rooms']}
    ymax = max(allp[:, 1].max() + 14, 0)                                          # (room below the range for the west sea to taper off)
    w['bounds'] = [w['bounds'][0], w['bounds'][1], w['bounds'][2], max(w['bounds'][3], int(math.ceil(ymax)))]
    report['bounds'] = w['bounds']
    return w, report
