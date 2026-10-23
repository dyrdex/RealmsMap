"""The Royal Jetty of Camelot and the castle of Camelot (owner, Oct 23).
  - a dock (`docks`, template; `shack: false`: the dock alone) on 21075: from the shore north-east of the room, through it and about one room
    on to the south-west, into the bay (changes/002);
  - Camelot (gfx 'camelot', template SPRITE.camelot: a legendary castle in the map's old front-view style) on 14084, its gate at the room, the
    top of the drawing at y TOP; trees and tufts under it removed."""
import math
from shapely.geometry import Point, box
from shapely.ops import unary_union
from shapely.geometry import Polygon

JETTY, CASTLE = 21075, 14084
OUT = 1.0                                           # the dock reaches this far past the room
A = 135.0                                           # its direction: south-west (degrees, x right, y down)
TOP, W, H = -55.0, 4.2, 5.25                        # the castle: top of the drawing, width, height (the drawing's natural size: no stretch)
GATE = 0.25                                         # the bottom of the drawing this far below the room (the gate opens onto it)
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def _parity(rings):
    S = Polygon()
    for p in rings:
        if len(p) > 2: S = S.symmetric_difference(Polygon(p).buffer(0))
    return S


def apply(town, wild, pos):
    land = _parity(wild['geo']['land'])
    jx, jy = pos[str(JETTY)][:2]; ux, uy = math.cos(math.radians(A)), math.sin(math.radians(A))
    assert not land.contains(Point(jx, jy))
    s = 0.0
    while not land.contains(Point(jx - ux * s, jy - uy * s)) and s < 3: s += 0.01        # back along the dock to the shore
    sx, sy = jx - ux * s, jy - uy * s
    wild['docks'] = list(wild.get('docks') or []) + [{'x': round(sx, 3), 'y': round(sy, 3), 'a': A, 'len': round(s + OUT, 2), 'shack': False}]
    end = (sx + ux * (s + OUT), sy + uy * (s + OUT))
    # ---- the castle ----
    cx, cy0 = pos[str(CASTLE)][:2]; bottom = cy0 + GATE; cy = TOP + H / 2
    assert abs(bottom - (TOP + H)) < 1e-6, (bottom, TOP + H)
    wild['gfx'] = list(wild['gfx']) + [{'k': 'camelot', 'at': 'xy', 'x': round(cx, 3), 'y': round(cy, 3), 'w': W, 'h': H}]
    foot = box(cx - W / 2, TOP + 0.6, cx + W / 2, bottom)                              # (the drawing's solid part: below the spires' tips)
    gone = {}
    for k in SPRITES:
        if k in wild:
            n0 = len(wild[k]); wild[k] = [q for q in wild[k] if not foot.contains(Point(q[0], q[1]))]
            if n0 - len(wild[k]): gone[k] = n0 - len(wild[k])
    under = sorted(int(v) for v, q in pos.items() if box(cx - W / 2, TOP, cx + W / 2, bottom).contains(Point(q[:2])) and int(v) != CASTLE)
    near = sorted((round(box(cx - W / 2, TOP, cx + W / 2, bottom).distance(Point(q[:2])), 2), int(v)) for v, q in pos.items()
                  if 0 < box(cx - W / 2, TOP, cx + W / 2, bottom).distance(Point(q[:2])) < 0.6)
    return {'dock (shore start, length, end; end in the sea, end to shore)': ((round(sx, 2), round(sy, 2)), round(s + OUT, 2), (round(end[0], 2), round(end[1], 2)),
                                                                              not land.contains(Point(end)), round(land.distance(Point(end)), 2)),
            'castle (centre, x range, y range)': ((round(cx, 2), round(cy, 3)), (round(cx - W / 2, 2), round(cx + W / 2, 2)), (TOP, round(bottom, 2))),
            'shown rooms under the castle': under, 'shown rooms within 0.6 of it': near, 'sprites removed under it': gone}
