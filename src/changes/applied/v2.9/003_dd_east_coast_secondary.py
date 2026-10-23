"""The Desert of Despair east coast's other water routes (owner, Oct 23): every route left in `seawaves` (the links from the primary path,
changes/002, to the coastline rooms and the land, and between them) drawn as type C, the Harbor of Icebergs' routes (`olharborways`: thin,
nearly transparent, its slight wave HWAVE_A/HWAVE_L as applied/v2.4/001), from the same rooms. The primary path is untouched."""
import math

HWAVE_A, HWAVE_L = 0.05, 1.6                         # applied/v2.4/001's harbour routes


def _knots(line, P):
    on = {(round(x, 2), round(y, 2)) for x, y in P}
    return [tuple(q[:2]) for i, q in enumerate(line) if (round(q[0], 2), round(q[1], 2)) in on and (i == 0 or math.dist(q, line[i - 1]) > 1e-6)]


def _wave(pts):                                      # applied/v2.4/001's _wave(line, HWAVE_A, HWAVE_L)
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / HWAVE_L)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = HWAVE_A * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def apply(town, wild, pos):
    P = [tuple(v[:2]) for v in pos.values()]
    lines = [_wave(_knots(l, P)) for l in wild['seawaves'] if l]
    wild['olharborways'].extend(lines)
    wild['seawaves'] = []
    return {'routes to type C (lines, length)': (len(lines), round(sum(math.dist(p, q) for l in lines for p, q in zip(l, l[1:])), 1))}
