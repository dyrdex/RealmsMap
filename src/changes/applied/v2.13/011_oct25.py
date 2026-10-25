"""Owner, Oct 25: Barren Peaks + Forgotten Woods editor save of Oct 25 00:12Z (`legacy/bp_layout_oct25.json`): The Crimson Caverns 22807
placed (east of A Dark Valley 6998; 5796 where 010 put it). Its trail 6998 - 22807 (a Woods trail, straight); The Crimson Caverns' line traced
again over its own directions (unchanged), so it and its marker end on 22807."""
import json, math, os
import maplib
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', '..', '..', 'legacy')
ROOM, FROM, PLACE = 22807, 6998, 'The Crimson Caverns'
CLEAR = 0.3
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'bp_layout_oct25.json'))); P = dict(zip(S['ids'], zip(S['xs'], S['ys'])))
    assert ROOM not in S['hidden'] and math.dist(P[5796], pos['5796'][:2]) < 0.01
    pos[str(ROOM)] = [round(P[ROOM][0], 2), round(P[ROOM][1], 2)]
    a = [round(c, 2) for c in pos[str(FROM)][:2]]; b = pos[str(ROOM)]
    wild['fwtracks'] = list(wild['fwtracks']) + [[a, b]]
    band = LineString([a, b]).buffer(CLEAR); gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    rooms, _ = maplib.world(); walk, at = maplib.tracer(pos, wild)
    p = next(q for q in wild['places'] if q['name'] == PLACE)
    t = walk(p['route']); assert t[-1] == ROOM, t[-3:]
    segs = [[]]
    for v in t:
        if at(v):
            q = [round(at(v)[0], 3), round(at(v)[1], 3)]
            if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
    old = p['path'][-1]
    p.update(path=segs[0], segs=[s for s in segs if s], room=rooms[ROOM]['name'], dir='here')
    return {'22807 at': b, 'trail from 6998 (length)': round(math.dist(a, b), 2), 'sprites cleared': gone,
            'Crimson Caverns marker (old -> new), rooms walked (directions unchanged)': (old, p['segs'][-1][-1], len(t) - 1)}
