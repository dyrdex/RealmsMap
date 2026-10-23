"""Owner, Oct 23: six new locations on the map and in the list, in the owner's words (directions in numbered form), each traced from Darkhaven
Square as applied/v2.9/011: the line over the drawn rooms, the marker on the owner's room (every route ends on a drawn room, checked).
Knights of the Round has two routes: walking (by the stairway down from 5639) and through the Darkhaven Art Gallery's painting (enter: The
Cadbury Chocolate Factory 11736, not drawn, so that line ends in Darkhaven and its card says so)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
DH = ('af', 'off New Darkhaven')
FW = ('fw', None)
PLACES = [   # name, room, routes [(label, route, note)], (group, where)
    ('Forgotten Woods', 1338, [(None, 'n;n;n;n;n;n;n;n;ne;w;n', None)], DH),
    ('Forest of Tears', 820, [(None, '#7 w', None)], DH),
    ('Ashen Forest', 1241, [(None, '#12 e', None)], DH),
    ('Barren Peaks', 5090, [(None, 'n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;sw;sw;s;s;ne;ne;n;nw;w;nw;nw;w;nw;nw;nw;w;w;w;nw;nw;w;w;w;s', None)], FW),
    ('Northern Plains', 4221, [(None, 'nw;w;w;n;n;n;n;e;look painting;open n;n', None)], DH),
    ('Knights of the Round', 11743, [
        ('Walking', 'n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;e;se;se;e;e;e;e;n;nw;n;n;sw;e;ne;s;s;se;s;se;s;w;w;w;w;sw;sw;s;w;w;s;sw;s;w;s;sw;s;se;e;e;d;n;n', None),
        ('DAG', 's;s;s;s;w;n;n;n;n;w;nw;w;sw;w;nw;w;enter', 'Through the "Mists at Ends" painting in the Darkhaven Art Gallery: enter it and you arrive at The Cadbury Chocolate Factory in the Knights of the Round, so the drawn line ends at the gallery in Darkhaven.')], FW),
]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, room, routes, (group, where) in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        opts = []
        for label, raw, note in routes:
            route = maplib.condense(raw); t = walk(route)
            assert len(t) > 1, name
            segs = [[]]
            for v in t:
                if at(v):
                    q = R(at(v))
                    if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
            opts.append(dict(dir=label, rooms=None, note=None, route=route, segs=[s for s in segs if s], gap=note, end=t[-1]))
        main = opts[0]
        assert main['end'] == room and at(room), (name, main['end'], room)
        p = dict(name=name, route=main['route'], room=rooms[room]['name'], dir='here', path=main['segs'][0], segs=main['segs'], group=group, note=None)
        if where: p['where'] = where
        if len(opts) > 1:
            p['opts'] = [{k: v for k, v in o.items() if k != 'end'} for o in opts]
        wild['places'].append(p)
        rep[name] = {'room': (room, rooms[room]['name']), 'marker': main['segs'][-1][-1],
                     'routes (rooms walked, drawn points, ends at)': [(len(walk(o['route'])) - 1, sum(len(s) for s in o['segs']), o['end'], rooms[o['end']]['name']) for o in opts]}
    return rep
