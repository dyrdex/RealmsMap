"""The Fissure and Tirebaen's Gorge told apart (owner, Oct 22): the rooms named 'The Fissure' are 'down' paths that lead to the Floor of Tirebaen's
Gorge, so the Fissure is drawn as a downward climb and the gorge as the flat ground at its foot:
  - the two descents (The Fissure 13180 down to 13179, 13222 down to 13221: their drawn trails, from the top room to the bottom one), the ground
    between them and 13223 on the rim no longer carry the gorge's wide floor and walls (`olgorge`, applied/v2.4/001): it is cut back to the gorge
    floor's rooms (GORGE_R round them and the short stretches between them; pieces without a floor room dropped), with walls hachured round its
    new head; the snow there gets its drifts back at the snow's density;
  - each descent is a narrow cleft in the snow (`wild.olfissure`, template OLFISSURE), widening as it goes down (W_TOP to W_BOT each side), dark
    inside, pale rims, short hachures down its sides; on its trail, steps across it (as the cliff climbs) and, every CHEV_D, a small chevron
    pointing down the descent."""
import json, math, random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union, substring
import maplib

TRACK_A, TRACK_L = 0.16, 7.0                                                  # applied/v2.4/001's trail warp (its rooms are on the warped spots)
FLOOR = "The Floor of Tirebaen's Gorge"
DESCENTS = [(13180, 13179), (13222, 13221)]                                   # (top, bottom): owner, Oct 22
GORGE_R, NEAR = 3.0, 3.5                                                      # as applied/v2.4/001: the gorge this wide round its stretches; a stretch
W_TOP, W_BOT, MOUTH = 0.22, 0.75, 2.5                                         # the cleft: half width at the top, at the foot; widening over its last MOUTH
STEP_D, STEP_W, CHEV_D, CHEV_S = 0.3, 0.17, 2.5, 0.22                         # steps: apart, half width; chevrons: apart, size


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    warp = lambda x, y: (x + TRACK_A * (0.7 * math.sin(2 * math.pi * y / TRACK_L + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TRACK_L * 1.6) + a3)),
                         y + TRACK_A * (0.7 * math.sin(2 * math.pi * x / TRACK_L + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TRACK_L * 1.6) + a4)))
    W = lambda v: warp(*pos[str(v)])
    rp = lambda q: [round(q[0], 3), round(q[1], 3)]
    rings = lambda g: [[rp(q) for q in list(p.exterior.coords)[:-1]] for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area > 0.05] + \
                      [[rp(q) for q in list(h.coords)[:-1]] for p in getattr(g, 'geoms', [g]) if p.geom_type == 'Polygon' and p.area > 0.05 for h in p.interiors]
    G = wild['olgorge']; land = unary_union([Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2])

    # ---- the descents: the drawn trail from the top room to the bottom one ----
    lines = []
    for top, bot in DESCENTS:
        pt, pb = W(top), W(bot); best = None
        for l in wild['oltracks']:
            it = [i for i, q in enumerate(l) if math.dist(q, pt) < 0.05]; ib = [i for i, q in enumerate(l) if math.dist(q, pb) < 0.05]
            if it and ib:
                i, j = it[0], ib[0]; seg = l[min(i, j):max(i, j) + 1]
                if i > j: seg = seg[::-1]                                                       # (top first)
                if best is None or len(seg) < len(best): best = seg
        assert best, (top, bot)
        lines.append(LineString(best))

    # ---- the gorge cut back to its floor ----
    fl = [v for v in map(int, pos) if rooms.get(v, {}).get('name') == FLOOR]
    fseg = [LineString([W(a), W(b)]) for i, a in enumerate(fl) for b in fl[i + 1:] if math.dist(pos[str(a)], pos[str(b)]) <= NEAR]
    floorreg = unary_union([Point(W(v)).buffer(GORGE_R) for v in fl] + [s.buffer(GORGE_R) for s in fseg])
    top = [LineString([W(13222), W(13223)])]                                                    # (13223, The Fissure on the rim)
    corridor = unary_union([unary_union(lines).convex_hull.buffer(GORGE_R + 0.5)] + [s.buffer(GORGE_R + 0.5) for s in top]).difference(floorreg)
    band0 = unary_union([Polygon(p).buffer(0) for p in G['band']]); floor0 = unary_union([Polygon(p).buffer(0) for p in G['floor']])
    band = band0.difference(corridor); band = unary_union([g for g in getattr(band, 'geoms', [band]) if g.area > 0.3 and any(g.contains(Point(W(v))) for v in fl)])
    floor = floor0.difference(corridor.buffer(0.8)).intersection(band.buffer(-0.8))
    cut = band0.difference(band)
    inside = lambda q, g=cut: g.contains(Point(q))
    nh0 = len(G['hach'])
    G['hach'] = [h for h in G['hach'] if not inside(((h[0][0] + h[1][0]) / 2, (h[0][1] + h[1][1]) / 2))]
    hnew = []
    for g in getattr(band, 'geoms', [band]):                                                    # walls round the gorge's new head (as 001's)
        for ring in [g.exterior] + list(g.interiors):
            n = int(ring.length / 0.2)
            for i in range(n):
                q = ring.interpolate(i * 0.2)
                if not cut.buffer(0.1).contains(q): continue
                f = floor.boundary.interpolate(floor.boundary.project(q)) if not floor.is_empty else q
                d = math.dist((q.x, q.y), (f.x, f.y))
                if 0.15 < d < 1.3:
                    k = (0.55 + 0.35 * (i % 2)) * d
                    hnew.append([[round(q.x, 3), round(q.y, 3)], [round(q.x + (f.x - q.x) / d * k, 3), round(q.y + (f.y - q.y) / d * k, 3)]])
    G['hach'] += hnew
    G['band'] = rings(band); G['floor'] = rings(floor)
    nr0 = (len(G.get('rocks', [])), len(G.get('gravel', [])), len(G.get('cracks', [])))
    G['rocks'] = [r for r in G.get('rocks', []) if not cut.intersects(Polygon(r).buffer(0))]
    G['gravel'] = [g for g in G.get('gravel', []) if not inside(g[:2])]
    G['cracks'] = [c for c in G.get('cracks', []) if not cut.intersects(LineString(c))]

    # ---- the clefts ----
    clefts, rims, hach, steps, chev = [], [], [], [], []
    cr = random.Random(26003)
    for l in lines:
        L = l.length; n = max(4, int(L / 0.15)); left, right = [], []
        hw = lambda d: W_TOP + (W_BOT - W_TOP) * max(0.0, (d - (L - MOUTH)) / MOUTH) ** 1.5 + 0.06 * (d / L)
        for i in range(n + 1):
            d = L * i / n; p = l.interpolate(d).coords[0]; p1 = l.interpolate(max(0, d - 0.1)).coords[0]; p2 = l.interpolate(min(L, d + 0.1)).coords[0]
            t = math.dist(p1, p2) or 1; nx_, ny_ = -(p2[1] - p1[1]) / t, (p2[0] - p1[0]) / t; w = hw(d)
            left.append((p[0] + nx_ * w, p[1] + ny_ * w)); right.append((p[0] - nx_ * w, p[1] - ny_ * w))
            if 0 < i < n and i % 2 == 0:                                                        # its sides falling away into it
                for s in (1, -1):
                    k = cr.uniform(0.45, 0.8)
                    hach.append([rp((p[0] + s * nx_ * w, p[1] + s * ny_ * w)), rp((p[0] + s * nx_ * w * (1 - k), p[1] + s * ny_ * w * (1 - k)))])
        poly = Polygon(left + right[::-1]).buffer(0).intersection(land)
        clefts += rings(poly); rims += [[rp(q) for q in left], [rp(q) for q in right]]
        for i in range(1, int(L / STEP_D)):                                                     # steps down it
            d = i * STEP_D; p = l.interpolate(d).coords[0]; p1 = l.interpolate(max(0, d - 0.05)).coords[0]; p2 = l.interpolate(min(L, d + 0.05)).coords[0]
            t = math.dist(p1, p2) or 1; nx_, ny_ = -(p2[1] - p1[1]) / t, (p2[0] - p1[0]) / t
            steps.append([rp((p[0] - nx_ * STEP_W, p[1] - ny_ * STEP_W)), rp((p[0] + nx_ * STEP_W, p[1] + ny_ * STEP_W))])
        for i in range(1, int(L / CHEV_D)):                                                     # chevrons pointing down the descent
            d = i * CHEV_D + 0.15; p = l.interpolate(d).coords[0]; p1 = l.interpolate(max(0, d - 0.05)).coords[0]; p2 = l.interpolate(min(L, d + 0.05)).coords[0]
            t = math.dist(p1, p2) or 1; tx, ty = (p2[0] - p1[0]) / t, (p2[1] - p1[1]) / t; nx_, ny_ = -ty, tx
            tip = (p[0] + tx * CHEV_S * 0.6, p[1] + ty * CHEV_S * 0.6)
            chev.append([rp((tip[0] - tx * CHEV_S + nx_ * CHEV_S, tip[1] - ty * CHEV_S + ny_ * CHEV_S)), rp(tip), rp((tip[0] - tx * CHEV_S - nx_ * CHEV_S, tip[1] - ty * CHEV_S - ny_ * CHEV_S))])
    wild['olfissure'] = {'cleft': clefts, 'rim': rims, 'hach': hach, 'steps': steps, 'chev': chev}

    # ---- the snow where the gorge was: its drifts back, at the snow's density (their own random.Random) ----
    o = wild['olsnow']; rr = random.Random(26004)
    cl = unary_union([Polygon(p).buffer(0) for p in clefts])
    free = cut.intersection(land).difference(cl.buffer(0.6)).difference(unary_union(lines).buffer(0.8)).buffer(-0.4)
    nd = round(len(o['drifts']) / land.area * cut.area); dr = []
    if not free.is_empty:
        x0, y0, x1, y1 = free.bounds
        for _ in range(6000):
            if len(dr) >= nd: break
            x, y = rr.uniform(x0, x1), rr.uniform(y0, y1)
            if free.contains(Point(x, y)) and all(math.dist((x, y), d[:2]) > 2.0 for d in o['drifts'] + dr):
                dr.append([round(x, 3), round(y, 3), round(rr.uniform(0.7, 1.0), 2), round(rr.uniform(-0.2, 0.2), 3)])
    o['drifts'] = list(o['drifts']) + dr
    return {'gorge cut back to its floor (area before -> after; hachures dropped, added; rocks/gravel/cracks dropped)':
            (round(band0.area, 1), round(band.area, 1), nh0 - (len(G['hach']) - len(hnew)), len(hnew), tuple(a - len(G.get(k, [])) for a, k in zip(nr0, ('rocks', 'gravel', 'cracks')))),
            'Fissure descents (lengths; cleft area; steps; chevrons; drifts added)':
            ([round(l.length, 1) for l in lines], round(cl.area, 2), len(steps), len(chev), len(dr))}
