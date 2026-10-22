# Morte's Peak (owner, Oct 23): the path through the Heart of the mountain is a thin dashed line (moved from oltracks to oltunnels, the
# Cramped Tunnel's style): the whole path between the "...Heart of Morte's Peak" rooms, through The Concealed Horror and Lost in the Darkness.
import math, random
from maplib import world

TRACK_A, TRACK_L = 0.16, 7.0                    # the trails' warp (applied/v2.4/001_otherland.py), to find the rooms on them


def apply(town, wild, pos):
    rooms, exits = world()
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    warp = lambda x, y: (x + TRACK_A * (0.7 * math.sin(2 * math.pi * y / TRACK_L + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TRACK_L * 1.6) + a3)),
                         y + TRACK_A * (0.7 * math.sin(2 * math.pi * x / TRACK_L + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TRACK_L * 1.6) + a4)))
    named = {v: warp(*pos[str(v)]) for v, r in rooms.items() if str(v) in pos and r['area'] == 'Otherland' and r['name']}   # (spacer rooms have no name)
    HEART = {v for v in named if 'Heart of Morte' in rooms[v]['name']}
    TUN = HEART | {v for v in named if rooms[v]['name'] in ("The Concealed Horror of Morte's Peak", 'Lost in the Darkness')} | {15703}   # (owner, Oct 23: from The Sudden Stop)
    grid = {}
    for v, q in named.items(): grid.setdefault((round(q[0]), round(q[1])), []).append((v, q))
    def hit(p):
        for v, q in grid.get((round(p[0]), round(p[1])), []):
            if math.dist(p, q) < 0.01: return v
    keep, moved, n = [], [], 0
    for l in wild['oltracks']:
        idx = [(i, hit(p)) for i, p in enumerate(l)]; idx = [(i, v) for i, v in idx if v]
        cuts = [(i, j) for (i, a), (j, b) in zip(idx, idx[1:]) if a in TUN and b in TUN]
        if not cuts: keep.append(l); continue
        s = 0
        for i, j in cuts:
            if i > s: keep.append(l[s:i + 1])
            moved.append(l[i:j + 1]); n += 1; s = j
        if s < len(l) - 1: keep.append(l[s:])
    keep = [k for k in keep if len(k) > 1]
    joined = []                                  # consecutive dashed stretches as one line
    for m in moved:
        if joined and joined[-1][-1] == m[0]: joined[-1] += m[1:]
        else: joined.append(list(m))
    wild['oltracks'] = keep; wild['oltunnels'] = list(wild['oltunnels']) + joined
    return {"Heart of Morte's Peak path dashed (rooms, stretches, dashed lines, length)": (len(TUN), n, len(joined), round(sum(math.dist(a, b) for m in joined for a, b in zip(m, m[1:])), 1))}
