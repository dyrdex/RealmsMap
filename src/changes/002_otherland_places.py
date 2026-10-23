"""Owner, Oct 22: sub-area markers for Otherland, with the owner's directions (data.py, condensed), traced from Darkhaven Square; each route drawn
in one piece over the drawn rooms (rooms not on the map skipped), its marker where the route leaves the drawn rooms (gotcha 3).
Valley of Crucifixion and The Ziggurat both leave at 13271 heading s (into hidden rooms): their markers side by side just south of it."""
import maplib, data

R = lambda q: [round(q[0], 3), round(q[1], 3)]
AT = {'The Ziggurat': (66.6, 177.65), 'Valley of Crucifixion': (67.4, 177.65)}   # (0.8 apart, 0.81 from 13271)
PLACES = ['Valley of Crucifixion', 'The Ziggurat', 'Wild Tundra']
WHERE = 'off Otherland'


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    routes = dict(l.split('|', 1) for l in data.AREAS.strip().splitlines() if '|' in l)
    rep = {}
    for name in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(routes[name].strip().rstrip(';'))
        t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))                                  # the last drawn room: the route leaves the map there
        out = next(e['name'] for e in exits[t[last]] if e['to'] == t[last + 1]) if last + 1 < len(t) else 'here'
        seg = [R(at(v)) for v in t[:last + 1] if at(v)]
        seg = [q for i, q in enumerate(seg) if not i or q != seg[i - 1]]
        p = dict(name=name, route=route, room=rooms[t[last]]['name'], dir=out, path=seg, segs=[seg], group='af', where=WHERE, note=None)
        if name in AT: p['at'] = list(AT[name])
        wild['places'].append(p)
        rep[name] = dict(end_room=t[-1], leaves_map_at=(t[last], out), marker=p.get('at') or seg[-1], rooms_not_drawn=[v for v in t[:last] if not at(v)])
    return rep
