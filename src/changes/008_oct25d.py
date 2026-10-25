"""Owner, Oct 25 (fourth set): the trail from Lost Between Woods 1755 southwest to The Weeping Forest 1754 (fwtracks, straight, 2 points) made to
look as if it went on: it runs straight on past 1754 along its own line for 2 more rooms (owner: same trajectory, about 2 rooms; a first try
bent it towards 1919 and was too long). A drawing only: no exit or route changes."""
import math

A, B, MORE = 1755, 1754, 2.0


def apply(town, wild, pos):
    a, b = (tuple(pos[str(v)]) for v in (A, B))
    tr = wild['fwtracks']
    hit = [i for i, t in enumerate(tr) if len(t) == 2 and math.dist(t[0], a) < .05 and math.dist(t[1], b) < .05]
    assert len(hit) == 1, hit
    L = math.dist(a, b); c = (b[0] + (b[0] - a[0]) / L * MORE, b[1] + (b[1] - a[1]) / L * MORE)
    tr[hit[0]] = [list(tr[hit[0]][0]), list(tr[hit[0]][1]), [round(c[0], 2), round(c[1], 2)]]
    return {'trail': hit[0], 'now ends at': tr[hit[0]][-1], 'added': MORE}
