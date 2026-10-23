"""Near Ocean Keep (owner, Oct 23): the one line left in `streams` (14257 Along the shore - 14295 - 14265 ... to the end of the type B route at
58.12, -37.14) drawn as a standard water path (`seawaysfaint`; changes/006 bends it). Its shape kept: the template drew it as a smooth curve
(curve(): quadratic pieces through the midpoints), so that curve is sampled here, every 0.1 rooms, and drawn as given."""
import math


def _curve(p):
    if len(p) < 3: return [list(q[:2]) for q in p]
    out = [tuple(p[0][:2])]; s = tuple(p[0][:2])
    for i in range(1, len(p) - 1):
        c = tuple(p[i][:2]); e = ((p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2)
        n = max(2, int((math.dist(s, c) + math.dist(c, e)) / 0.1))
        for k in range(1, n + 1):
            t = k / n
            out.append(((1 - t) ** 2 * s[0] + 2 * (1 - t) * t * c[0] + t * t * e[0], (1 - t) ** 2 * s[1] + 2 * (1 - t) * t * c[1] + t * t * e[1]))
        s = e
    out.append(tuple(p[-1][:2]))
    return [[round(x, 3), round(y, 3)] for x, y in out]


def apply(town, wild, pos):
    S = wild.get('streams') or []
    assert len(S) == 1, len(S)
    line = _curve(S[0])
    wild['streams'] = []
    wild['seawaysfaint'].append(line)
    return {'stream to standard water path (points, length)': (len(line), round(sum(math.dist(a, b) for a, b in zip(line, line[1:])), 1))}
