"""The Desert of Despair east coast's primary water path (owner, Oct 23): the sea rooms 12984 - 12985 - 12986 - ... - 12993, then 15098 - 15108 -
15097 - 6300 at the south end, running on from the Coral Depths path (which ends at 12983 - 12984) south along the coast, drawn in the standard
water path style (`seawaysfaint`, type B) instead of `seawaves`, no wave: the straight room-to-room line,
bent with every other water path by changes/005 (the standard water path, maplib.warpline). The routes from these rooms to the
coastline land rooms (secondary) stay `seawaves`, untouched."""
import math

CHAIN = [12984, 12985, 12986, 12987, 12988, 12989, 12990, 12991, 12992, 12993, 15098, 15108, 15097, 6300]


def _knots(line, P):
    on = {(round(x, 2), round(y, 2)) for x, y in P}
    return [tuple(q[:2]) for i, q in enumerate(line) if (round(q[0], 2), round(q[1], 2)) in on and (i == 0 or math.dist(q, line[i - 1]) > 1e-6)]


def apply(town, wild, pos):
    P = [tuple(v[:2]) for v in pos.values()]
    at = lambda v: tuple(pos[str(v)][:2])
    same = lambda q, v: math.dist(q[:2], at(v)) < 0.02
    take, path = [], []
    for a, b in zip(CHAIN, CHAIN[1:]):
        c = [i for i, l in enumerate(wild['seawaves']) if l and ((same(l[0], a) and same(l[-1], b)) or (same(l[0], b) and same(l[-1], a)))]
        c.sort(key=lambda i: len(_knots(wild['seawaves'][i], P)))
        assert c, (a, b)
        take.append(c[0])                              # the direct one (12987 - 12988 also has a route through the land room 15044: kept)
        ks = _knots(wild['seawaves'][c[0]], P)
        if not same(ks[0], a): ks = ks[::-1]
        path += ks if not path else ks[1:]
    line = [list(q) for q in path]                     # straight, room to room: changes/005 bends it (the standard water path)
    wild['seawaves'] = [l for i, l in enumerate(wild['seawaves']) if i not in set(take)]
    wild['seawaysfaint'].append(line)
    return {'primary path: stretches, rooms on it (spacers incl.), length': (len(take), len(path), round(sum(math.dist(p, q) for p, q in zip(line, line[1:])), 1))}
