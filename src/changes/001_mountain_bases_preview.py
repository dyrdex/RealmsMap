# TEMPORARY review (owner, Oct 22): where the bases of Otherland's two mountains would go, as dashed circles (wild.olmtnpreview).
# Each circle = the smallest circle round the mountain's rooms, plus BASE_M. Remove once the owner settles the circles.
import itertools, math
import maplib

MP_NAMES = {'Nestled Between the Peaks', 'Upon the Roof', 'Platforms of Sacrifice', 'An Icy Pass', 'A Snow Clogged Pass', "Dead Man's Pass", 'The Drop-Off',
            'The Sudden Stop', 'Entombed in Ice', 'A Cavern of Ice', 'An Icy Burrow', 'The Cave', 'Home of the Jarl', 'A Crisp Path', 'Scratching the Surface',
            'Lost in the Darkness', 'The Last of the Foothills'}       # as applied/v2.4/001_otherland (Morte's Peak, east of x 50)
BASE_M = 1.5                                                            # the base this far beyond the outermost room


def mec(pts):
    cands = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in itertools.combinations(pts, 2)]
    for a, b, c in itertools.combinations(pts, 3):
        d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        if abs(d) < 1e-9: continue
        sa, sb, sc = (q[0] ** 2 + q[1] ** 2 for q in (a, b, c))
        cands.append(((sa * (b[1] - c[1]) + sb * (c[1] - a[1]) + sc * (a[1] - b[1])) / d, (sa * (c[0] - b[0]) + sb * (a[0] - c[0]) + sc * (b[0] - a[0])) / d))
    return min(((c, max(math.dist(c, p) for p in pts)) for c in cands), key=lambda t: t[1])


def apply(town, wild, pos):
    rooms, _ = maplib.world()
    ol = [int(v) for v in pos if int(v) in rooms and rooms[int(v)]['area'] == 'Otherland']
    nm = lambda v: rooms[v]['name']
    sets = {"Morte's Peak": [v for v in ol if pos[str(v)][0] > 50 and (nm(v) in MP_NAMES or ("Morte's Peak" in nm(v) and 'View' not in nm(v)))],
            'Zenith of the Gods': [v for v in ol if pos[str(v)][0] < 14 and ('Gods' in nm(v) or nm(v) == 'The Western Face')]}
    wild['olmtnpreview'] = []; out = {}
    for name, S in sets.items():
        (cx, cy), r = mec(sorted({tuple(pos[str(v)][:2]) for v in S}))
        wild['olmtnpreview'].append({'cx': round(cx, 2), 'cy': round(cy, 2), 'r': round(r + BASE_M, 2)})
        out[name + ' preview circle (rooms, centre, radius)'] = (len(S), (round(cx, 1), round(cy, 1)), round(r + BASE_M, 1))
    return out
