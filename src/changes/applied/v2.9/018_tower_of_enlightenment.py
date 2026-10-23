"""Owner, Oct 23: the Tower of Enlightenment's new directions. Traced from Darkhaven Square over the drawn rooms; the streets of Ofcol (not
drawn) are crossed as the Ofcol Shortcut, as on every other route that takes it (gate 1363 straight to 5333; changes/017 draws that as a
jump); the marker where the route leaves the drawn rooms (gotcha 3: into the Blood Sea, 13640 on)."""
import maplib

ROUTE = ('n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;e;se;se;e;e;e;e;n;nw;n;n;sw;e;ne;s;s;se;s;se;s;w;w;w;w;sw;sw;s;w;w;s;sw;s;w;s;'
         'sw;s;se;e;e;ne;se;e;e;se;d;w;sw;n;n;n')
OFCOL = (1363, 5333)
R = lambda q: [round(q[0], 3), round(q[1], 3)]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    p = next(p for p in wild['places'] if p['name'] == 'Tower of Enlightenment')
    route = maplib.condense(ROUTE); t = walk(route)
    assert rooms[t[-1]]['area'] == 'Tower of Enlightenment', t[-1]
    g, l = t.index(OFCOL[0]), t.index(OFCOL[1])
    last = max(i for i, v in enumerate(t) if at(v))
    assert all(at(v) for i, v in enumerate(t[:last + 1]) if not g < i < l), 'a break besides Ofcol'
    path = []
    for i, v in enumerate(t[:last + 1]):
        if g < i < l: continue
        q = R(at(v))
        if not path or path[-1] != q: path.append(q)
    out = next(e['name'] for e in exits[t[last]] if e['to'] == t[last + 1])
    old = (p['room'], p['dir'], len(p.get('segs') or []))
    p.update(route=route, room=rooms[t[last]]['name'], dir=out, path=path, segs=[path], note=None)
    p.pop('at', None)
    return {'Tower of Enlightenment (rooms; ends; marker was -> now; pieces)': (len(t) - 1, (t[-1], rooms[t[-1]]['name']), old,
            (t[last], rooms[t[last]]['name'], out, path[-1]), 1)}
