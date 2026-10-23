"""Barren Peaks, owner's saves of Oct 23 21:08Z and 21:17Z (legacy/bp_layout_oct23.json): 14 + 6 rooms shown, 5 moved (6880 is still hidden: its spot only).
  - the shown rooms' exits (to rooms already on the map): Woods dirt trails (fwtracks), straight room to room; a line ends on the old trail
    where that trail passes beside its room rather than through it; up/down exits not drawn (6939 u 6940); trees/tufts cleared within CLEAR;
  - deathtraps (owner, Oct 23): the deathtrap emblem (`deathtraps`, template SKULL) on 13 rooms, size SKULL (smaller than the Azure Coast's
    0.6: the seven sins lie a room apart round 7022);
  - mobs, map only (owner, Oct 23: no list entry, no directions): `mobmarks` (template MOBMARK: the mob marker and its name, LABEL_FS)."""
import json, math, os
from collections import defaultdict
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, nearest_points

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
SHOWN = [6836, 6940, 6990, 6991, 6992, 6993, 6994, 7008, 7009, 7012, 7016, 7257, 7258, 7259,
         6958, 6959, 6960, 6961, 6962, 6963]                 # (save of Oct 23 21:17Z: the way to Dae'Clya)
MOVED = [6880, 6940, 7008, 7009, 7016]
DEATHTRAPS = [7029, 7026, 7024, 7023, 7025, 7027, 7028, 7012, 7009, 7008, 6940, 7016, 6836]
SKULL = 0.34
MOBS = [(7022, 'RakShasa'), (6963, "Dae'Clya"), (6994, 'Hirema')]
LABEL_FS = 0.72
CLEAR = 0.3
SNAP = 0.05                                     # an end room further than this from every old trail: the line ends on the nearest trail
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct23.json'))); E = json.load(open(os.path.join(LEG, 'bp_editor_edges_oct23.json')))
    P = dict(zip(S['ids'], zip(S['xs'], S['ys']))); hidden = set(S['hidden'])
    assert not set(SHOWN) & hidden and 6880 in hidden
    moved = {v: (tuple(pos[str(v)][:2]), P[v]) for v in MOVED}
    for v in MOVED: pos[str(v)] = [P[v][0], P[v][1]]
    at = lambda v: tuple(pos[str(v)][:2])
    # ---- trails ----
    old = unary_union([LineString(l) for l in wild['fwtracks'] if len(l) > 1])
    new, ud, snapped = [], [], []
    for a, b, k in E['edges']:
        if not (a in SHOWN or b in SHOWN) or a in hidden or b in hidden: continue
        if k == 'ud': ud.append((a, b)); continue
        line = []
        for v in (a, b):
            q = at(v)
            if v not in SHOWN and old.distance(Point(q)) > SNAP:
                n = nearest_points(old, Point(q))[0]; snapped.append((v, round(old.distance(Point(q)), 2))); q = (n.x, n.y)
            line.append([round(q[0], 2), round(q[1], 2)])
        new.append(line)
    wild['fwtracks'] = list(wild['fwtracks']) + new
    band = unary_union([LineString(l).buffer(CLEAR) for l in new]); gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    # ---- deathtraps and mobs ----
    wild['deathtraps'] = list(wild.get('deathtraps') or []) + [[at(v)[0], at(v)[1], SKULL] for v in DEATHTRAPS]
    wild['mobmarks'] = list(wild.get('mobmarks') or []) + [{'x': at(v)[0], 'y': at(v)[1], 'name': n, 'fs': LABEL_FS} for v, n in MOBS]
    close = sorted((round(math.dist(at(a), at(b)), 2), a, b) for i, a in enumerate(DEATHTRAPS) for b in DEATHTRAPS[i + 1:] + [m for m, _ in MOBS] if math.dist(at(a), at(b)) < 1.2)
    return {'rooms moved (old -> new)': moved, 'trails added (exits; up/down not drawn; ends snapped to the old trail)': (len(new), ud, snapped),
            'sprites cleared': gone, 'deathtraps (rooms, size)': (len(DEATHTRAPS), SKULL), 'closest emblem/marker pairs': close[:4],
            'mob marks (room, name, at)': [(v, n, at(v)) for v, n in MOBS]}
