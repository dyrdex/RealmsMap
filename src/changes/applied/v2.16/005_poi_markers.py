"""Owner, Oct 27: Points of Interest work like deities: no marker on the map until one is selected, then its own marker (site_template
POI) and its route. Six new ones; lines traced as far as the mapped rooms go, the marker at the line's end. Card notes in the owner's
words (Sonoria's replaced). The sidebar section moves to the bottom (site_template)."""
import math
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
NOTES = {'Sonoria': 'Respawn point for non-guilded/ordered characters',
         "Jokaan's Repair Shop": 'Affordable Equipment Repairs', 'Camelot Reparations': 'Affordable Equipment Repairs'}
NEW = [   # name, card note, owner's directions
    ('Dalach', 'Repair and Recharge staves and wands.',
     'nw;#2 w;#4 n;e;look painting;open n;#2 n;#57 w;ne;n;nw;n;#3 nw;open s;s;w;open u;u;u;open w;w;u'),
    ("Adventurer's Emporium", 'Useful Potions',
     '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#2 e;u;#3 e;#3 s;se;#3 e;#2 s;w;nw;#3 w;sw;s;#2 sw;w;#2 sw;nw;#2 d;sw;d;s;#3 se;s;sw;se;s;#2 w;#3 n;'),
    ('Seolwyn Smoke Shop', 'Smokeable herbs for mana and other affects.',
     '#13 s;#2 e;#2 u;e;#3 se;d;s;#2 se;#4 s;#3 se;sw;#2 w;sw;#3 s;se;s;sw;s;se;#3 s;e;s;d;se;d;se;#2 ne;nw;w;nw;#2 ne;#2 n;#2 nw;w'),
    ('Cultic Candies', 'Teleport candies and more', '#4 s;e;n;say idolizer of dragons;#2 n;open d;d;e;open n;n'),
    ('Hobgoblin Cave', 'Evil mobs to adjust align toward devout.',
     's;s;s;s;s;s;s;s;s;s;s;w;s;w;s;s;u;n;give 500 coin troll;s;d;e;ne;u;e;e;se;d;w;sw;s'),
    ('Queen Mordrineagh Ni Riain', 'Purchase a Prestige scrippe',
     '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;n;ne;#4 n;#2 u;open w;w'),
]

UNTRACED = {'Seolwyn Smoke Shop'}   # its directions stop matching the map's exits at The Trail Towards the Canyon Continues: no room name on the card


def apply(town, wild, pos):
    rooms, _ = maplib.world()
    walk, at = maplib.walker(pos, wild)
    jumps = [((j[0], j[1]), (j[2], j[3])) for j in wild.get('jumps') or []]
    isjump = lambda a, b: any((math.dist(a, x) < .03 and math.dist(b, y) < .03) or (math.dist(b, x) < .03 and math.dist(a, y) < .03) for x, y in jumps)
    P = {p['name']: p for p in wild['places'] + town['places']}
    rep = {}
    for name, note in NOTES.items():                                 # the three already on the map: the marker where their pin was
        p = P[name]; p.update(note=note, poi=True, nopin=True, at=maplib.pin(p)); rep[name] = {'marker': p['at']}
    for name, note, raw in NEW:
        assert name not in P, name
        route = maplib.condense(raw); t = walk(route)
        pts = []
        for v in t:
            if at(v) and (not pts or pts[-1] != R(at(v))): pts.append(R(at(v)))
        last = max(i for i, v in enumerate(t) if at(v))
        segs = [[pts[0]]]
        for a, b in zip(pts, pts[1:]):                               # a sea crossing (over 100) breaks the line, as for the deities
            if math.dist(a, b) > 100 and not isjump(a, b): segs.append([b])
            else: segs[-1].append(b)
        wild['places'].append(dict(name=name, route=route, room=None if name in UNTRACED else rooms[t[-1]]['name'], dir='here', path=pts, segs=segs, kind='mob', group='af',
                                   note=note, poi=True, nopin=True, at=pts[-1]))
        rep[name] = {'walked': len(t) - 1, 'ends at': rooms[t[-1]]['name'], 'line stops at': (t[last], rooms[t[last]]['name']), 'marker': pts[-1],
                     'pieces': len(segs)}
    return rep
