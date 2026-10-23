"""The Desert of Despair east coast's primary water path (owner, Oct 23): the sea rooms 12984 - 12985 - 12986 - ... - 12993, running on from the
Coral Depths path (which ends at 12983 - 12984) south along the coast, drawn in the standard water path style (`seawaysfaint`, type B) instead
of `seawaves`; its wave kept but softer (amplitude 0.12 -> WAVE_AMP; wavelength as before, a whole number of waves per room-to-room stretch,
flat at the rooms). The routes from these rooms to the coastline land rooms (secondary) stay `seawaves`, untouched."""
import math

CHAIN = [12984, 12985, 12986, 12987, 12988, 12989, 12990, 12991, 12992, 12993]
WAVE_AMP, WAVE_LEN = 0.06, 2.5                       # applied/v2.3/001: 0.12, 2.5


def _knots(line, P):
    on = {(round(x, 2), round(y, 2)) for x, y in P}
    return [q for i, q in enumerate(line) if (round(q[0], 2), round(q[1], 2)) in on and (i == 0 or math.dist(q, line[i - 1]) > 1e-6)]


def _wave(pts):
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / WAVE_LEN)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = WAVE_AMP * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def apply(town, wild, pos):
    P = [tuple(v[:2]) for v in pos.values()]
    at = lambda v: tuple(pos[str(v)][:2])
    same = lambda q, v: math.dist(q[:2], at(v)) < 0.02
    take = []
    for a, b in zip(CHAIN, CHAIN[1:]):
        c = [i for i, l in enumerate(wild['seawaves']) if l and ((same(l[0], a) and same(l[-1], b)) or (same(l[0], b) and same(l[-1], a)))]
        c.sort(key=lambda i: len(_knots(wild['seawaves'][i], P)))
        assert c, (a, b)
        take.append(c[0])                              # the direct one (12987 - 12988 also has a route through the land room 15044: kept)
    lines = [_wave(_knots(wild['seawaves'][i], P)) for i in take]
    wild['seawaves'] = [l for i, l in enumerate(wild['seawaves']) if i not in set(take)]
    wild['seawaysfaint'].extend(lines)
    return {'primary path: stretches, rooms on them (spacers incl.), length': (len(lines), sum(len(_knots(l, P)) for l in lines),
            round(sum(math.dist(p, q) for l in lines for p, q in zip(l, l[1:])), 1))}
