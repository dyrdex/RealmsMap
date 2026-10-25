"""Owner, Oct 25: nine new destinations, in the owner's words (directions in numbered form, never edited). None of them is fully mapped:
each line is traced from Darkhaven Square over the drawn rooms and stops at the last drawn room on the way (where the directions go out
of the mapped rooms). Markers where the owner placed them (`at`); Keep of Mahn-Tor (The Keep), Cold Comfort and Galaxy are in the list
only (`nopin`: no marker, no name on the map; template)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
DAG = '#4 s;w;#2 n;give 5k coins receptionist;unlock n;open n'
PLACES = [   # name, owner's directions, marker spot (None: list only), where
    ('Dwarven Catacombs',
     '#8 e;se;se;s;#3 se;e;ne;ne;n;ne;ne;n;nw;n;ne;w;push leaves;pull leaves;e;e;n;n;u;open u;u;open u;u;e;d;d;#4 n;open n;n;open n;n;d',
     (22.29, 9.45), 'past the Mountains of Desolation'),         # halfway between Machine Dreams' marker (Hanging on Air 3360, 23.28, 7.66) and the
                                                                    # Mountains of Desolation's (21.31, 11.23) (owner, Oct 25; was 21.31, 7.5)
    ('Dragontail Glen',
     'nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;w;w;w;w;w;w;w;s;w;sw;s;s;w;w;w;w;nw;nw;w;w;sw;sw;sw;sw;w;n;d;w;w;n;n;w;w;w;n;n',
     (-10.5, -136.6), 'past Crystalmir Lake'),                     # WNW of the Crystalmir Lake marker (-8.09, -135.67), 1.0 below the road
    ('The Blood Sea', '#53 w', (-105.9, 1), 'off the Forest of Tears'),
    ('Azure Sea', 's;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;e;se', (51.74, 45.35), 'off the Southern Mountain Range'),   # SE of 1494
    ('The Burrows', 'w;w;w;w;w;w;w;w;w;nw;w;w;nw;n;n;n;w;w;n;n;n;e;e', (-29.98, -4.46), 'in The Shire'),   # 3 north of The Shire's marker
    ('Mathlaan Lagoon',
     'e;e;e;e;e;e;e;e;ne;ne;ne;e;e;e;ne;e;ne;e;e;n;n;n;n;n;ne;e;ne;e;se;e;ne;n;n;n;ne;d;d;w;w;w;w;w;w;w;w;w;w;w;se;d',
     (48.62, -35.31), 'past Ocean Keep'),                          # NW of the Ocean Keep marker (51.42, -32.46), 4.0 off it: clear of its town drawing (owner, Oct 25: 2.5 times as far)
    ('The Keep of Mahn-Tor (The Keep)', DAG + ';#3 n;ne;n;ne;n;enter;d;e;n;u;u', None, 'through the Darkhaven Art Gallery'),
    ('Cold Comfort', DAG + ';#3 n;ne;n;ne;n;enter;d;e;#2 n;se', None, 'through the Darkhaven Art Gallery'),
    ('Galaxy', DAG + ';n;n;n;ne;n;enter', None, 'through the Darkhaven Art Gallery'),
]
NOTES = {'Cold Comfort': 'After the last #2 n, scan or scry for the room with a se exit, then go se.'}   # (owner's words, from the directions)


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, raw, spot, where in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))                 # the last drawn room on the way: the line stops there
        path = []
        for v in t[:last + 1]:
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
        assert len(path) > 1 and last < len(t) - 1 or name == 'Azure Sea', name
        note = (NOTES.get(name, '') + ' ' if name in NOTES else '') + (
            f"The rest of the way isn't mapped yet, so the drawn line stops at {rooms[t[last]]['name']}." if last < len(t) - 1 else '')
        p = dict(name=name, route=route, room=rooms[t[-1]]['name'], dir='here', path=path, segs=[path], group='af', where=where,
                 note=note.strip() or None)
        if spot: p['at'] = list(spot)
        else: p['nopin'] = True
        wild['places'].append(p)
        rep[name] = {'walked': len(t) - 1, 'ends at': (t[-1], rooms[t[-1]]['name']), 'line stops at': (t[last], rooms[t[last]]['name'], path[-1]),
                     'drawn points': len(path), 'marker': spot or 'none (list only)'}
    return rep
