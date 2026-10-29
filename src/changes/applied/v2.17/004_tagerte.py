"""Owner, Oct 29: a new Point of Interest, Tagerte's Conveyances (#3 s;#3 e;n), marker in Darkhaven at the corner of Park Avenue and
Hawk Street, north of Park Avenue (the room the directions end at). Level range in src/rodpedia.tsv (no link). Card note (owner, Oct 29)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
NAME, RAW = "Tagerte's Conveyances", '#3 s;#3 e;n'


def apply(town, wild, pos):
    rooms, _ = maplib.world()
    walk, at = maplib.walker(pos, wild)
    assert not any(p['name'] == NAME for p in wild['places'] + town['places'])
    route = maplib.condense(RAW); t = walk(route)
    assert all(at(v) for v in t), [v for v in t if not at(v)]
    pts = []
    for v in t:
        if not pts or pts[-1] != R(at(v)): pts.append(R(at(v)))
    wild['places'].append(dict(name=NAME, route=route, room=rooms[t[-1]]['name'], dir='here', path=pts, segs=[pts], kind='mob', group='af',
                               note='Teleport Tickets for Lowbies', poi=True, nopin=True, at=pts[-1]))
    return {NAME: {'rooms': [(v, rooms[v]['name']) for v in t], 'marker': pts[-1]}}
