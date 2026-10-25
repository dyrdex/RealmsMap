"""Owner, Oct 25: the Forest of Tears editor save of Oct 25 04:13Z (`legacy/ft_layout_oct25b.json`; 13 of the new rooms moved since 03:58Z, `ft_layout_oct25.json`): the 19 rooms added that day
(tools/forest_of_tears_editor/add_oct25_rooms.py) get their spots, all hidden (no trails drawn: they exist so routes can be traced through
them; the save moved no other room). New places, traced as 001 (the line stops at the last drawn room on the way):
  - New Hope Farm: reaches A Path Between the Trees 10015; marker there.
  - Abishai's Morgue: goes 7807 sw 7810 7811 7829 (not in the editor), so the line stops at Before the Morgue 7807; marker there.
  - The Underworld: the directions end at The Crossing 4011 (then 'give 50000 coins Wicorith'); marker on The Underworld 878, just south.
  - In the list only (no marker, no line): Olympus, Scourge of Time, The Domain of World Eater (the owner's note, 'scan/scry to find
    Formless Void Maze', on its card; its commas read as ';')."""
import json, os, maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
NEW = [1944, 7807, 7808, 7809, 7834, 1526, 9997, 10000, 10015, 1561, 4002, 4003, 4004, 4007, 4008, 4009, 4010, 4011, 878]
PLACES = [   # name, owner's directions, marker room (None: list only), where, note
    ('New Hope Farm', '#6 w;sw;sw;#5 w;s;e;s;se', 10015, 'off the Western Trade Route', None),
    ("Abishai's Morgue", '#9 w;sw;#4 w;s;sw;w;w;open s;s;s;sw;s;window', 7807, 'off the Forest of Tears', None),
    ('The Underworld', '#26 w;#7 s;e;s;e;s;d;s;give 50000 coins Wicorith', 878, 'past Kontaur', None),
    ('Olympus', '#8 u;n; track juna;say will you take me to Olympus?', None, 'past the Astral Plane', None),
    ('Scourge of Time', '#8 u;n;unlock n;open n;n;track Malsangre;say back in time', None, 'past the Astral Plane', None),
    ('The Domain of World Eater', '#13 e;#3 s;w;s;#2 w;n;#2 w;#2 s;se;#2 e;ne;w;s;#3 d', None, 'past Machine Dreams',
     'After the last #3 d, scan or scry to find the Formless Void Maze.'),
]


def apply(town, wild, pos):
    o = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'legacy', 'ft_layout_oct25b.json')))
    sv = dict(zip(o['ids'], zip(o['xs'], o['ys'])))
    for v in NEW:
        assert str(v) not in pos and v in o['hidden'], v
        pos[str(v)] = R(sv[v])
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {'rooms placed (hidden)': len(NEW)}
    for name, raw, mark, where, note in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))
        path = []
        for v in t[:last + 1]:
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
        if last < len(t) - 1 and mark:
            note = f"The rest of the way isn't mapped yet, so the drawn line stops at {rooms[t[last]]['name']}."
        p = dict(name=name, route=route, room=rooms[t[-1]]['name'], dir='here', path=path, segs=[path], group='af', where=where, note=note)
        if mark:
            if R(at(mark)) != path[-1]: p['at'] = R(at(mark))
        else: p['nopin'] = p['hidepath'] = True
        wild['places'].append(p)
        rep[name] = {'ends at': (t[-1], rooms[t[-1]]['name']), 'line stops at': (t[last], rooms[t[last]]['name']), 'marker': R(at(mark)) if mark else 'list only'}
    return rep
