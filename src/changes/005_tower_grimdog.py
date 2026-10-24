"""Owner, Oct 24:
  - the Tower of Enlightenment's marker on Path to the Tower 13642 (its route's step after 5644: d 13640, w 13641, sw 13642; then n into the
    tower): its line follows the three rooms, the marker sits on 13642 ('here'); its label left to the solver (owner: may overlap things);
  - a small Tower of Enlightenment drawing beside it (the map's `magetower`, kept in its own proportions), as large as fits: TOWER (centre x,
    base y, height) was searched for the tallest one clear of the cliff face, trails, stairways and markers, all on land (3.47 tall);
  - The Grimdog Port Authority's marker bumped BUMP south-east (it looked as if it sat on the long path 1669 - 1668; it doesn't)."""
import math

TOWER = (-49.7, -44.0, 3.4)                         # (centre x, base y, height); 0.64 from 13642, a little under the 3.47 that fits
MT_W, MT_H, MT_BASE = 1.6, 5.1, 2.5                 # magetower's own size and base (template SPRITE.magetower)
BUMP = (1.41, 1.41)                                 # about 2 rooms south-east


def apply(town, wild, pos):
    R = lambda v: [round(c, 2) for c in pos[str(v)][:2]]
    toe = next(p for p in wild['places'] if p['name'] == 'Tower of Enlightenment')
    assert toe['route'].endswith('se;d;w;sw;#3 n') and math.dist(toe['path'][-1][:2], R(5644)) < 0.01, toe['path'][-1]
    add = [R(13640), R(13641), R(13642)]
    toe['path'] = list(toe['path']) + add
    if toe.get('segs'): toe['segs'] = [list(s) for s in toe['segs'][:-1]] + [list(toe['segs'][-1]) + add]
    toe['dir'] = 'here'
    cx, by, h = TOWER; w = h * MT_W / MT_H
    wild['gfx'] = list(wild['gfx']) + [{'k': 'magetower', 'at': 'xy', 'x': cx, 'y': round(by - h * MT_BASE / MT_H, 3), 'w': round(w, 3), 'h': h}]
    gd = next(p for p in wild['places'] if p['name'] == 'The Grimdog Port Authority')
    end = gd['path'][-1]; mx, my = end[0], end[1] - 0.62 if gd['dir'] == 'n' else end[1]   # (the marker: 0.62 north of the line's end, template pins)
    assert gd['dir'] == 'n' and not gd.get('at')
    gd['at'] = [round(mx + BUMP[0], 2), round(my + BUMP[1], 2)]
    from shapely.geometry import LineString, Point
    p375 = LineString([q[:2] for q in wild['fwtracks'][375]])
    return {'Tower of Enlightenment marker': R(13642), 'tower drawing (centre x, base y, width, height)': (cx, by, round(w, 2), h),
            'Grimdog marker (old -> new)': ([round(mx, 2), round(my, 2)], gd['at']),
            'Grimdog marker from the 1669-1668 path (old -> new)': (round(p375.distance(Point(mx, my)), 2), round(p375.distance(Point(gd['at'])), 2))}
