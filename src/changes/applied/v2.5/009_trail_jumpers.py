# Otherland's trails (owner, Oct 22): where two trails cross with no room there, one "jumps" the other like a wire jumper in an electrical
# diagram: a small half-circle hop over the straight one; no gaps, no marks. The tunnel (dashed) one hops if one is involved, else the shorter
# line; every hop bulges to the same side (up-left on the map).
import math
from shapely.geometry import LineString, Point
from shapely.ops import substring

R0, FOOT, RMAX = 0.45, 0.42, 0.8               # the hop's radius: at least R0, and its feet FOOT off the crossed trail's centre (the trails are 0.36
                                                # wide), so it is wider where the crossing is slanted; at most RMAX
NEAR_ROOM = 0.3                                 # a crossing this close to a room is a real junction: left alone
N_ARC = 14


def apply(town, wild, pos):
    rooms = [Point(q) for q in pos.values()]
    def room_d(p):
        return min([r.distance(p) for r in rooms if abs(r.x - p.x) < 1 and abs(r.y - p.y) < 1] or [9])
    def lines():
        return [('oltunnels', i, l) for i, l in enumerate(wild['oltunnels']) if len(l) > 1] + [('oltracks', i, l) for i, l in enumerate(wild['oltracks']) if len(l) > 1]
    def crossings():
        L = lines(); out = []
        G = [LineString(l) for _, _, l in L]
        for i in range(len(G)):
            for j in range(i + 1, len(G)):
                if not G[i].envelope.intersects(G[j].envelope): continue
                c = G[i].intersection(G[j])
                for p in getattr(c, 'geoms', [c]):
                    if p.geom_type == 'Point' and room_d(p) >= NEAR_ROOM:
                        out.append((p, L[i], L[j]))
        return out
    done, skipped = [], []
    todo = crossings()                                  # (found once: a hop's arc passes over the other trail by design)
    for p, a, b in todo:
        a = (a[0], a[1], wild[a[0]][a[1]]); b = (b[0], b[1], wild[b[0]][b[1]])   # (as hopped so far)
        cand = sorted([a, b], key=lambda t: (t[0] != 'oltunnels', LineString(t[2]).length))       # the tunnel first, else the shorter
        for hk, hi, hl in cand:
            g = LineString(hl); s = g.project(p)
            o = LineString(b[2] if (hk, hi) == (a[0], a[1]) else a[2]); so = o.project(p)
            u = (g.interpolate(min(g.length, s + 0.2)).x - g.interpolate(max(0, s - 0.2)).x, g.interpolate(min(g.length, s + 0.2)).y - g.interpolate(max(0, s - 0.2)).y)
            v = (o.interpolate(min(o.length, so + 0.2)).x - o.interpolate(max(0, so - 0.2)).x, o.interpolate(min(o.length, so + 0.2)).y - o.interpolate(max(0, so - 0.2)).y)
            sin = abs(u[0] * v[1] - u[1] * v[0]) / (math.hypot(*u) * math.hypot(*v) or 1)
            R = min(RMAX, max(R0, FOOT / max(sin, 0.05)))
            if s - R > 0.05 and s + R < g.length - 0.05: break
        else:
            skipped.append((round(p.x, 2), round(p.y, 2))); done.append((p, None)); continue
        q0, q1 = g.interpolate(s - R), g.interpolate(s + R)
        tx, ty = (q1.x - q0.x) / (2 * R), (q1.y - q0.y) / (2 * R); tn = math.hypot(tx, ty) or 1; tx, ty = tx / tn, ty / tn
        nx, ny = -ty, tx
        if nx * -1 + ny * -1 < 0: nx, ny = -nx, -ny                                               # bulge up-left
        cx, cy = (q0.x + q1.x) / 2, (q0.y + q1.y) / 2
        arc = [[round(cx - R * math.cos(t) * tx + R * math.sin(t) * nx, 3), round(cy - R * math.cos(t) * ty + R * math.sin(t) * ny, 3)] for t in (math.pi * k / N_ARC for k in range(N_ARC + 1))]
        head = [list(c) for c in substring(g, 0, s - R).coords]; tail = [list(c) for c in substring(g, s + R, g.length).coords]
        wild[hk][hi] = head[:-1] + arc + tail[1:]
        done.append((p, (hk, hi, arc)))
    # checks: each hop clear of rooms and of every other trail but the one it jumps
    rep = []
    for p, h in done:
        if not h: continue
        hk, hi, arc = h; A = LineString(arc)
        others = [LineString(l) for k, i, l in lines() if not (k == hk and i == hi)]
        hits = sum(1 for o in others if o.intersects(A))
        rep.append(((round(p.x, 1), round(p.y, 1)), hk[2:], round(math.dist(arc[0], arc[-1]) / 2, 2), round(min(r.distance(A) for r in rooms), 2), hits))
    return {'trail jumpers (crossing, the hopping kind, radius, nearest room to the hop, trails the hop still touches); skipped': (rep, skipped)}
