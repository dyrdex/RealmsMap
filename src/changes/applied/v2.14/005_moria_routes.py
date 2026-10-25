"""Owner, Oct 25: new directions for the Land of the Fire Newts and Machine Dreams, and The Domain of World Eater shown on the map like
them (its marker and line; was list only). All three go #13 e, then through the Ashen Forest to Within the Ashen Forest 1255 and on south
into Moria and the Land of the Fire Newts (drawn from the Ashen save of Oct 25 04:58Z, 004b), so each line runs as far as
those rooms go (Fire Newts: the whole way, to 3352; the others to Hanging on Air 3360); markers on the lines' ends (owner, Oct 25): the Fire Newts' on 3352, a shared one for the other two on 3360; names stacked east of it: the Land of
the Fire Newts, Machine Dreams below it, The Domain of World Eater above it (template LBL)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ROUTES = {   # owner's directions (Oct 25)
    'Land of the Fire Newts': '#13 e; #3 s;e;s;e;s',
    'Machine Dreams': '#13 e; #3 s;e;s;e;#3 s;e;#3 s;e;s;d',
    'The Domain of World Eater': '#13 e; #3 s;e;s;e;#3 s;e;#3 s;e;s;#3 d',
}
SHARED = "Machine Dreams and The Domain of World Eater share one pin, at Hanging on Air."
NOTES = {
    'Land of the Fire Newts': None,
    'Machine Dreams': "Your directions go on from Hanging on Air into Machine Dreams, which isn't drawn yet, so the line stops there. " + SHARED,
    'The Domain of World Eater': "After the last #3 d, scan or scry to find the Formless Void Maze. Your directions go on from Hanging on Air into Machine Dreams, which isn't drawn yet, so the line stops there. " + SHARED,
}


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, raw in ROUTES.items():
        p = next(p for p in wild['places'] if p['name'] == name)
        route = maplib.condense(raw); t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))
        path = []
        for v in t[:last + 1]:
            if not path or path[-1] != R(at(v)): path.append(R(at(v)))
        p.update(route=route, path=path, segs=[path], room=rooms[t[-1]]['name'], dir='here', group='af', where='through Moria', note=NOTES[name])   # marker on the line's end (owner, Oct 25)
        p.pop('at', None)
        for k in ('nopin', 'hidepath'): p.pop(k, None)
        rep[name] = {'route': route, 'walked': len(t) - 1, 'ends at': (t[-1], rooms[t[-1]]['name']), 'line stops at': (t[last], rooms[t[last]]['name'], path[-1]), 'drawn points': len(path)}
    return rep
