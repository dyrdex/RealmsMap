"""Owner, Oct 20: markers for the Sea of Sorrows (at 12272) and Winterlight Island (at 9842), with the owner's new directions (data.py, condensed),
traced from Darkhaven Square over the new sea rooms; each drawn in one piece to its marker room."""
import maplib, data

R = lambda q: [round(q[0], 3), round(q[1], 3)]
PLACES = [('Sea of Sorrows', 12272), ('Winterlight Island', 9842)]
WHERE = 'off the Wastelands'


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    routes = dict(l.split('|', 1) for l in data.AREAS.strip().splitlines() if '|' in l)
    rep = {}
    for name, end in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(routes[name].strip().rstrip(';'))
        t = walk(route)
        assert t[-1] == end and all(at(v) for v in t), (name, t[-1])
        seg = [R(at(v)) for v in t]
        wild['places'].append(dict(name=name, route=route, room=rooms[end]['name'], dir='here', path=seg, segs=[seg], group='af', where=WHERE, note=None))
        rep[name] = dict(marker_room=end, at=seg[-1], steps=len(t), pieces=1)
    return rep
