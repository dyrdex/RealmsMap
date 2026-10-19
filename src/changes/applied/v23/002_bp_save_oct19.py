"""Owner's Barren Peaks save of Oct 19 (19:58Z, the editor with the Forgotten Woods unlocked): no room moved; 5 Forgotten Woods rooms hidden
(their trails come off the map) and 6 Barren Peaks rooms shown (their trails drawn, as the Peaks' other trails: straight dirt lines between
the rooms, through spacer rooms, only to rooms that are shown; up/down exits not drawn)."""
import math
from maplib import world, tracer

HIDDEN = [5655, 5688, 5756, 21623, 22303]                       # The Fallen Log, a spacer, Forgotten Lookout, A Hole in the Ground, Inside a Rickety Hut
SHOWN = [6723, 6919, 6920, 6937, 6938, 6939]                    # Cries From Above, A Training Ground, Army Base, Echoes of Life, Dangerous Grounds, The Black Chaos
STILL_HIDDEN = {6940}                                           # (the rooms next to them that the save keeps hidden)
DIRS = ('n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw')


def apply(town, wild, pos):
    rooms, exits = world(); _, at = tracer(pos, wild)
    isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    near = lambda q, p: p is not None and math.dist(q[:2], p) < .06
    gone = [at(v) for v in HIDDEN]
    n0 = len(wild['fwtracks'])
    wild['fwtracks'] = [L for L in wild['fwtracks'] if not any(near(L[0], p) or near(L[-1], p) for p in gone)]
    removed = n0 - len(wild['fwtracks'])

    def drawn(a, b):                                            # a trail already joins these two spots
        return any((near(L[0], a) and near(L[-1], b)) or (near(L[0], b) and near(L[-1], a)) for L in wild['fwtracks'])
    added, seen = [], set()
    for v in SHOWN:
        for e in exits.get(v, []):
            if e['name'] not in DIRS: continue
            chain = [v]; u = e['to']; k = 0
            while isspacer(u) and k < 40:
                chain.append(u); c = [x['to'] for x in exits.get(u, []) if x['name'] == e['name']]
                if not c: u = None; break
                u = c[0]; k += 1
            if u is None or u in STILL_HIDDEN or u in HIDDEN or not at(u) or u not in rooms: continue
            chain.append(u)
            if frozenset((v, u)) in seen or any(at(c) is None for c in chain): continue
            seen.add(frozenset((v, u)))
            if drawn(at(v), at(u)): continue
            line = [[round(at(c)[0], 3), round(at(c)[1], 3)] for c in chain]
            wild['fwtracks'].append(line); added.append((v, u))

    segs = [(L[i], L[i + 1]) for L in wild['fwtracks'][len(wild['fwtracks']) - len(added):] for i in range(len(L) - 1)]
    def onpath(q):                                              # a sprite standing on a new trail
        for a, b in segs:
            dx, dy = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
            if math.dist(q[:2], (a[0] + t * dx, a[1] + t * dy)) < .35: return True
        return False
    cleared = {}
    for k in ('trees', 'tufts', 'boulders', 'crags', 'hills', 'peaks', 'brush'):
        L = wild.get(k) or []; keep = [q for q in L if not onpath(q)]
        if len(keep) != len(L): cleared[k] = len(L) - len(keep); wild[k] = keep
    return {'trails removed (hidden rooms)': removed, 'trails added (shown rooms)': len(added), 'links': [f'{a}-{b}' for a, b in added],
            'sprites cleared off the new trails': cleared}
