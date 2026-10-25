"""Owner, Oct 25 (second set):
  - 'Keep of Mahn-Tor (Ogre Village)' renamed 'The Keep of Mahn-Tor (Ogre Village)'.
  - Three new places, routes fully drawn, marker on the last room: Southern Mountain Range, Miden'nir (no name: the map already names
    Miden'nir), Western Trade Route.
  - Tribal Swamplands (Lizardmen) renamed Tribal Swamplands. Western Trade Route's marker on 831 (#6 w;sw).
  - The Southern Mountain Range's big area name, NE of Suds 'n Stones.
  - Hometowns: the card line under the name ('Area off ... · reached at ...') replaced by the owner's text (`card`; template + site)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
RENAME = {'Keep of Mahn-Tor (Ogre Village)': 'The Keep of Mahn-Tor (Ogre Village)', 'Tribal Swamplands (Lizardmen)': 'Tribal Swamplands'}
NEW = [   # name, owner's directions, where, no label
    ('Southern Mountain Range', 's;s;s;s;s;s;ne;s;s;se;e;e;s', 'off New Darkhaven', False),
    ("Miden'nir", '#7 s', 'off New Darkhaven', True),
    ('Western Trade Route', 'w;w;w;w;w;w;sw;sw', 'off New Darkhaven', False),
]
PIN_AT = {'Western Trade Route': '#6 w;sw'}   # the marker on the room these steps reach (owner, Oct 25; the route itself unchanged)
SMR_LABEL = dict(x=-7.0, y=47.5, lh=2.6, sag=1.0, hw=12, lines=['Southern', 'Mountain Range'])   # big area name NE of Suds 'n Stones (owner, Oct 25):
                                                    # clear of every marker and marker name; crosses one Woods-style trail (6 points)
CARDS = {   # the owner's names in brackets where the map's differ
    'Keep of Lomar': 'Human Hometown', "Qetag's Reach": 'Dwarf Hometown', 'The Island of Irrybis': 'Elf Hometown',
    'The Burrows': 'Halfling Hometown', 'Reomyr Village': 'Pixie Hometown', 'City of Eldestra': 'Half-Elf Hometown',
    'Mount Krozloy': 'Half-Orc Hometown',                      # (Mount Krozly)
    'Opallinoc': 'Half-Ogre Hometown',
    "The Ruins of T'man": 'Half-Troll Hometown',               # (Ruins of T'man)
    'Mathlaan Lagoon': 'Sea-Elf Hometown',
    'The City of Iniquity': 'Drow Hometown',                   # (City of Iniquity)
    'Tribal Swamplands': 'Lizardman Hometown',
    'Vale of Nidaros': 'Gnome Hometown',
}


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for old, new in RENAME.items():
        p = next(p for p in wild['places'] if p['name'] == old); p['name'] = new; rep.setdefault('renamed', []).append((old, new))
    for name, raw, where, nolabel in NEW:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t = walk(route)
        assert all(at(v) for v in t), name
        path = []
        for v in t:
            if not path or path[-1] != R(at(v)): path.append(R(at(v)))
        p = dict(name=name, route=route, room=rooms[t[-1]]['name'], dir='here', path=path, segs=[path], group='af', where=where, note=None)
        if nolabel: p['nolabel'] = True
        if name in PIN_AT:
            v = walk(maplib.condense(PIN_AT[name]))[-1]; p['at'] = R(at(v)); rep[name + ' pin'] = (v, rooms[v]['name'], p['at'])
        wild['places'].append(p)
        rep[name] = {'ends at': (t[-1], rooms[t[-1]]['name']), 'marker': path[-1], 'label': not nolabel}
    for name, card in CARDS.items():
        p = next(p for p in wild['places'] if p['name'] == name); p['card'] = card
    rep['cards'] = len(CARDS)
    wild['arealabels'].append(SMR_LABEL); rep['area name'] = SMR_LABEL
    return rep
