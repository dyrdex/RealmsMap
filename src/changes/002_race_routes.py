"""Owner, Oct 27: race-only routes to the 13 hometowns (only a member of that race can take them). Each becomes a route option
'<Race> Only' after the area's own routes (an area with one route gets it as option 'All races'). Its line: the town rooms of
'#2 ne;#2 n' from Darkhaven Square, then a route jump (dashed arc) to the area's marker. On The Sands of Teracchei (`hidepath`: no line for
its own route) the Gith line is drawn (`show`; site drawRoute)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
RACES = [   # place, race, owner's directions
    ('Keep of Lomar', 'Human', '#2 ne;#2 n;tell tage I seek the peace of the garden'),
    ("Qetag's Reach", 'Dwarf', '#2 ne;#2 n;tell tage I long for the forges of Khazad'),
    ('The Island of Irrybis', 'Elf', '#2 ne;#2 n;tell tage I seek the warmth of nature'),
    ('The Burrows', 'Halfling', '#2 ne;#2 n;tell tage I seek the simpler ways'),
    ('Reomyr Village', 'Pixie', '#2 ne;#2 n;tell tage I seek the guidance of Reomyr'),
    ('City of Eldestra', 'Half-Elf', '#2 ne;#2 n;tell tage I seek the sanctuary of Eldestra'),
    ('Mount Krozloy', 'Half-Orc', '#2 ne;#2 n;say I seek the solace of the caves'),
    ('Opallinoc', 'Half-Ogre', '#2 ne;#2 n;tell tage I must defend my lands!'),
    ("The Ruins of T'man", 'Half-Troll', '#2 ne;#2 n;tell tage I seek the refuge of the forest'),
    ('Mathlaan Lagoon', 'Sea-Elf', '#2 ne;#2 n;tell tage I seek the clear water of my haven'),
    ('The Sands of Teracchei', 'Gith', '#2 ne;#2 n;tell tage the glittering sands call my name'),
    ('The City of Iniquity', 'Drow', '#2 ne;#2 n;tell tage I seek the darkness of my home'),
    ('Vale of Nidaros', 'Gnome', '#2 ne;#2 n;tell tage I seek the safety of Nidaros'),
]


def apply(town, wild, pos):
    walk, at = maplib.tracer(pos, wild)
    town_pts = []
    for v in walk('#2 ne;#2 n'):                                    # Darkhaven Square to Unity of the Nations
        if at(v) and (not town_pts or town_pts[-1] != R(at(v))): town_pts.append(R(at(v)))
    P = {p['name']: p for p in wild['places']}
    rep = {}
    for name, race, raw in RACES:
        p = P[name]; m = R(p['at'] if p.get('at') else p['path'][-1])
        if not p.get('opts'):
            p['opts'] = [dict(dir='All races', route=p['route'], segs=p.get('segs') or [p['path']])]
        p['opts'].append(dict(dir=f'{race} Only', route=maplib.condense(raw), segs=[town_pts + [m]], **({'show': True} if p.get('hidepath') else {})))
        wild['jumps'].append([town_pts[-1][0], town_pts[-1][1], m[0], m[1], f'{race} Only: {name}'])
        rep[name] = {'option': len(p['opts']) - 1, 'jump': (town_pts[-1], m)}
    return rep
