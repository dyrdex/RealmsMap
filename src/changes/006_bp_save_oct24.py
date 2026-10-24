"""Barren Peaks, owner's save of Oct 24 14:58Z (legacy/bp_layout_oct24.json): Killing Fields 6997 and A Dark Valley 6998 shown (hidden
before), and 6997, 6998, The Silver Sword 6999, A Shadowy Grove 7006, Glowing Eyes 7007 moved (6999, 7006, 7007 still hidden: their spots only).
  - the shown rooms' exits to rooms on the map: Woods dirt trails, straight room to room (as 2.12/007): 6996 - 6997, 6997 - 6998
    (6997 e 6999: 6999 hidden; 6998 e 22807: not in the editor); trees/tufts cleared within CLEAR;
  - route lines through the moved rooms (The Crimson Caverns) follow them."""
import json, math, os
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
SHOWN = [6997, 6998]
MOVED = [6997, 6998, 6999, 7006, 7007]
CLEAR = 0.3
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct24.json'))); E = json.load(open(os.path.join(LEG, 'bp_editor_edges_oct23.json')))
    P = dict(zip(S['ids'], zip(S['xs'], S['ys']))); hidden = set(S['hidden'])
    assert not set(SHOWN) & hidden and {6999, 7006, 7007} <= hidden
    old = {v: tuple(pos[str(v)][:2]) for v in MOVED}
    for v in MOVED: pos[str(v)] = [round(P[v][0], 2), round(P[v][1], 2)]
    at = lambda v: [round(c, 2) for c in pos[str(v)][:2]]
    new = [[at(a), at(b)] for a, b, k in E['edges'] if (a in SHOWN or b in SHOWN) and a not in hidden and b not in hidden and k != 'ud']
    wild['fwtracks'] = list(wild['fwtracks']) + new
    band = unary_union([LineString(l).buffer(CLEAR) for l in new]); gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    moved_pts, routes = 0, []
    def fix(line):
        nonlocal moved_pts
        out = []
        for q in line:
            hit = next((v for v in MOVED if math.dist(q[:2], old[v]) < 0.05), None)
            if hit: moved_pts += 1; out.append(at(hit) + list(q[2:]))
            else: out.append(q)
        return out
    for p in wild['places']:
        b = moved_pts
        if p.get('path'): p['path'] = fix(p['path'])
        if p.get('segs'): p['segs'] = [fix(s) for s in p['segs']]
        if moved_pts > b: routes.append(p['name'])
    return {'rooms moved (old -> new)': {v: (old[v], at(v)) for v in MOVED}, 'trails added': new, 'sprites cleared': gone,
            'route points moved': (moved_pts, routes)}
