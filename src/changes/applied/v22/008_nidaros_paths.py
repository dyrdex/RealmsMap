"""Owner, Oct 19: the Nidaros Shortcut's short paths drawn (dirt trails, like the Woods' own): east 5307 -> 5317 -> 935 -> 936 -> spacer 5511, west
5510 -> 5507. The long step 5511 -> 5507 across the map is not drawn (it is only in the routes, changes/007). The one tree on the east path removed."""
import math

EAST = [(39.29, -62.69), (38.16, -63.82), (38.16, -64.82), (38.16, -65.82), (37.16, -64.82)]     # 5307, 5317, 935, 936, 5511 (the owner's save)
WEST = [(-36.94, -64.91), (-37.6, -66.37)]                                                       # 5510, 5507


def _d(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def apply(town, wild, pos):
    for k, v in (('5307', EAST[0]), ('5510', WEST[0])): assert math.dist(pos[k], v) < .02, k
    lines = [[list(q) for q in EAST], [list(q) for q in WEST]]
    wild['fwtracks'] = list(wild['fwtracks']) + lines
    n0 = len(wild['trees'])
    wild['trees'] = [q for q in wild['trees'] if min(_d(q[:2], a, b) for L in lines for a, b in zip(L, L[1:])) >= .45]
    return dict(paths=len(lines), length=round(sum(math.dist(a, b) for L in lines for a, b in zip(L, L[1:])), 2), trees_removed=n0 - len(wild['trees']))
