"""Owner, Oct 25: new directions for the Land of the Fire Newts and Machine Dreams, and The Domain of World Eater shown on the map like
them (its marker and line; was list only). All three go #13 e, then through the Ashen Forest to Within the Ashen Forest 1255 and on south
into Moria (not drawn), so each line stops at 1255 and they share its marker (dir 's', as before); names stacked east of it: the Land of
the Fire Newts, Machine Dreams below it, The Domain of World Eater above it (template LBL)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ROUTES = {   # owner's directions (Oct 25)
    'Land of the Fire Newts': '#13 e; #3 s;e;s;e;s',
    'Machine Dreams': '#13 e; #3 s;e;s;e;#3 s;e;#3 s;e;s;d',
    'The Domain of World Eater': '#13 e; #3 s;e;s;e;#3 s;e;#3 s;e;s;#3 d',
}
SHARED = "One shared pin marks the Land of the Fire Newts, Machine Dreams and The Domain of World Eater, at forest room 1255, whose south exit leads into Moria."
NOTES = {
    'Land of the Fire Newts': "Your directions go on through Moria, which isn't drawn yet. " + SHARED,
    'Machine Dreams': "Your directions go on through Moria and the Land of the Fire Newts, which aren't drawn yet. " + SHARED,
    'The Domain of World Eater': "After the last #3 d, scan or scry to find the Formless Void Maze. Your directions go on through Moria, the Land of the Fire Newts and Machine Dreams, which aren't drawn yet. " + SHARED,
}


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, raw in ROUTES.items():
        p = next(p for p in wild['places'] if p['name'] == name)
        route = maplib.condense(raw); t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))
        assert t[last] == 1255, (name, t[last])
        path = []
        for v in t[:last + 1]:
            if not path or path[-1] != R(at(v)): path.append(R(at(v)))
        p.update(route=route, path=path, segs=[path], room=rooms[1255]['name'], dir='s', group='af', where='through Moria', note=NOTES[name])
        for k in ('nopin', 'hidepath'): p.pop(k, None)
        rep[name] = {'route': route, 'walked': len(t) - 1, 'ends at': (t[-1], rooms[t[-1]]['name']), 'line stops at': (1255, path[-1]), 'drawn points': len(path)}
    return rep
