"""Owner, Oct 23:
  - Over the Cliff Maze's label bigger (size FS, was 0.55) and centred on the maze (its centroid, inside it);
  - the Village of Edo: the owner's new directions; its route redrawn over the drawn rooms and its marker moved to where the route leaves
    them (gotcha 3), the final room when it is drawn."""
import maplib
from shapely.geometry import Polygon, Point
from shapely.ops import polylabel

FS = 0.85
EDO = 'nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;n;n;n;n;nw;n;ne;n;nw;ne;n;n'
R = lambda q: [round(q[0], 3), round(q[1], 3)]


def apply(town, wild, pos):
    m = next(m for m in wild['fwmazes'] if m['name'] == 'Over the Cliff Maze')
    M = Polygon(m['poly']); c = M.centroid
    if not M.buffer(-1.5).contains(c): c = polylabel(M, 0.05)
    was = (m['cx'], m['cy'], m.get('fs'))
    m.update(cx=round(c.x, 2), cy=round(c.y, 2), fs=FS)
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    p = next(p for p in wild['places'] if p['name'] == 'Village of Edo')
    route = maplib.condense(EDO); t = walk(route)
    assert len(t) > 1
    last = max(i for i, v in enumerate(t) if at(v))
    out = next(e['name'] for e in exits[t[last]] if e['to'] == t[last + 1]) if last + 1 < len(t) else 'here'
    path = []
    for v in t[:last + 1]:
        if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
    old = (p['room'], p['path'][-1])
    p.update(route=route, room=rooms[t[last]]['name'], dir=out, path=path, segs=[path])
    p.pop('at', None)
    return {'Over the Cliff Maze label (was x, y, size -> now)': (was, (m['cx'], m['cy'], FS)),
            'Village of Edo (rooms; ends; marker was -> now)': (len(t) - 1, (t[-1], rooms[t[-1]]['name']), old, (t[last], rooms[t[last]]['name'], out, path[-1]))}
