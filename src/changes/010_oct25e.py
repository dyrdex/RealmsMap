"""Owner, Oct 25 (fifth set):
  - Abattoir Asylum and Antall, the Lost Harbor: new places, every room on the way drawn; markers on the last rooms (Azure and Green 12994,
    A dark, scarlet main 12995). Abattoir Asylum's last words ('scan/move to room with east/west exits, then east') go on its card.
  - The Dwarven Catacombs: two route options, 'Northern Entrance' (its directions so far, the card's default) and 'Southern Entrance' (the
    owner's new directions, all drawn, to the Southern entrance to the Catacombs 9081); a second marker (`more`, template + site) on 9081
    that opens the same card with the Southern Entrance picked; the first marker opens it on the Northern Entrance. One entry in the list."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
PLACES = [   # name, owner's directions, note
    ('Abattoir Asylum', 's;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;se;se;s;s;s;se;s',
     'From Azure and Green, scan or move to the room with east and west exits, then go east.'),
    ('Antall, the Lost Harbor', 's;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;se;se;s;s;s;se;s;se', None),
]
SOUTH = 's;s;s;s;s;s;s;s;s;s;s;s;s;e;e;u;u;e;se;se;se;d;s;se;se;s;s;s;s;se;se;se;sw;s;sw;sw;w;sw;sw;nw;d;d;sw;d;n;ne;e;e;n;d;n;n'


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    def trace(route):
        t = walk(route); assert all(at(v) for v in t if rooms[v]['name']), [v for v in t if not at(v)]
        path = []
        for v in t:
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
        return t, path
    rep = {}
    for name, raw, note in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t, path = trace(route)
        wild['places'].append(dict(name=name, route=route, room=rooms[t[-1]]['name'], dir='here', path=path, segs=[path], group='af', where='off the Azure Sea', note=note))
        rep[name] = (t[-1], rooms[t[-1]]['name'], path[-1])
    p = next(p for p in wild['places'] if p['name'] == 'Dwarven Catacombs')
    route = maplib.condense(SOUTH); t, path = trace(route)
    p['opts'] = [dict(dir='Northern Entrance', rooms=None, note=None, route=p['route'], segs=p['segs'], gap=p.get('note')),
                 dict(dir='Southern Entrance', rooms=None, note=None, route=route, segs=[path], gap=None)]
    p['note'] = None
    p['more'] = [dict(at=path[-1], opt=1)]
    rep['Dwarven Catacombs, Southern Entrance'] = {'walked': len(t) - 1, 'ends at': (t[-1], rooms[t[-1]]['name']), 'second marker': path[-1]}
    return rep
