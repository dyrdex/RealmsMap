"""Owner, Oct 25 (fourth set): the trail from Lost Between Woods 1755 southwest to The Weeping Forest 1754 (fwtracks, straight, 2 points) made to
look as if it went on about two rooms further south-west: it runs on past 1754 to Drowning in Sorrow 1919 (4.67 rooms), with a gentle bend
at 1754 (rounded 0.6 either side; 1754 stays within 0.35 of the curve). A drawing only: no exit or route changes."""
import math

A, B, C = 1755, 1754, 1919


def apply(town, wild, pos):
    a, b, c = (tuple(pos[str(v)]) for v in (A, B, C))
    tr = wild['fwtracks']
    hit = [i for i, t in enumerate(tr) if len(t) == 2 and math.dist(t[0], a) < .05 and math.dist(t[1], b) < .05]
    assert len(hit) == 1, hit
    u = lambda p, q, d: (p[0] + (q[0] - p[0]) * d / math.dist(p, q), p[1] + (q[1] - p[1]) * d / math.dist(p, q))
    p1, p2 = u(b, a, 0.6), u(b, c, 0.6)
    pts = [a, p1] + [((1 - s) ** 2 * p1[0] + 2 * (1 - s) * s * b[0] + s * s * p2[0], (1 - s) ** 2 * p1[1] + 2 * (1 - s) * s * b[1] + s * s * p2[1]) for s in (i / 8 for i in range(1, 8))] + [p2, c]
    out = [pts[0]]
    for p, q in zip(pts, pts[1:]):
        n = max(1, round(math.dist(p, q) / 0.32))
        out += [(p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n) for k in range(1, n + 1)]
    tr[hit[0]] = [[round(x, 2), round(y, 2)] for x, y in out]
    near = min(math.dist(b, q) for q in out)
    return {'trail': hit[0], 'points': len(out), 'ends': (a, c), '1754 to the curve': round(near, 2)}
