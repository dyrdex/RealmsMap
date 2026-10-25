"""Owner, Oct 25: rooms added in Darkhaven without a layout editor (owner's go-ahead; none exists for the town), placed in the empty block
south-west of Darkhaven Square (south of Horizon Road, north of Market Street, east of Falcon Road, west of Vertic Avenue); the town's
drawing is untouched (rooms aren't drawn there; only the markers + names below, all inside that block or, for the Town Hall, the empty
block south of Horizon Road at 763). In the Air 12176/13598 stay where they were (on the Square: they are above it).
Places: The Astral Plane (#8 u;n, marker on The Astral Gate 13606, north of 13604), The Sands of Teracchei (#8 u;e, marker on An Endless
Sea of Void 1416, east of 13604), Town Hall (e;s, marker on The Lobby of Darkhaven Town Hall 1453, south of Horizon Road 763).
The Sands of Teracchei's card: 'Gith Hometown' (the owner's hometown list)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
SPOTS = {   # the Rainbow from the block's south-east corner west and up to 13604; the gate north of it, the void east of it
    13599: (-1.0, 2.95), 13600: (-1.85, 3.05), 13601: (-2.7, 3.05), 13602: (-3.55, 2.95), 13603: (-4.4, 2.6), 13604: (-5.1, 1.85),
    13606: (-5.1, 0.95), 1416: (-4.5, 1.85), 1453: (0.8, 0.85)}   # (Town Hall: by the corner of Vertic Avenue and Horizon Road, owner Oct 25; was 2, 1)
AT = {'The Astral Plane': (-0.8, 0.85), 'The Sands of Teracchei': (-0.8, 1.75)}   # markers by the corner of Vertic and Horizon, east of their
                                                  # names, the Sands directly south of the Astral Plane; no route line for either (owner, Oct 25)
PLACES = [   # name, owner's directions, kind
    ('The Astral Plane', '#8 u;n', None),
    ('The Sands of Teracchei', '#8 u;e', None),
    ('Town Hall', 'e;s', 'structure'),
]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    for v, q in SPOTS.items():
        assert str(v) not in pos, v
        pos[str(v)] = list(q)
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, raw, kind in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t = walk(route)
        assert all(at(v) for v in t if rooms[v]['name']), name          # (the spacer 18468 has no spot: the line goes 13604 -> 13606)
        path = []
        for v in t:
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
        p = dict(name=name, route=route, room=rooms[t[-1]]['name'], dir='here', path=path, segs=[path], note=None)
        if kind: p['kind'] = kind
        if name in AT: p['at'] = list(AT[name]); p['hidepath'] = True
        if name == 'Town Hall':   # e then s, plainly (owner, Oct 25): east along Horizon Road to above the lobby, then straight south to it
            q = path[-1]; p['path'] = p['segs'][0] = path = [[0, 0], [q[0], 0], q]
        wild['places'].append(p)
        rep[name] = {'ends at': (t[-1], rooms[t[-1]]['name']), 'marker': path[-1], 'drawn points': len(path)}
    next(p for p in wild['places'] if p['name'] == 'The Sands of Teracchei')['card'] = 'Gith Hometown'   # (owner, Oct 25: Sands of Teracchei)
    rep['rooms placed'] = len(SPOTS)
    return rep
