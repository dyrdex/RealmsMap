"""Owner, Oct 27: card warnings.
  - The Blood Sea break (Otherland (Southern), and the North option of the Otherland sub-areas and mobs) now reads NS.
  - The 'isn't mapped / line stops' notes, the shared-pin note and the notes on where a pin is (16) come off (the lines stay as drawn).
  - Abattoir Asylum, Cold Comfort, The Domain of World Eater: the owner's full directions (their closing scan/scry steps back in the
    directions, not on the card); their notes come off."""
import maplib

NS = 'North-South link: Route runs far north and links to far south off Otherland'
ROUTES = {   # owner's directions (Oct 27)
    'Abattoir Asylum': '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#2 e;u;#3 e;#3 s;se;#3 e;s;#2 se;#3 s;se;s;scry/scan for room with east/west exits and move there;e',
    'Cold Comfort': '#4 s;w;#2 n;give 5k coins receptionist;unlock n;open n;#3 n;ne;n;ne;n;enter;d;e;#2 n;scry/scan for room with se exit and move there',
    'The Domain of World Eater': '#13 e;#3 s;e;s;e;#3 s;e;#3 s;e;s;#3 d; scry/scan for The Formless Void (maze)',
}
DROP = ['Dragontail Glen', 'The Blood Sea', 'The Burrows', 'Mathlaan Lagoon', 'The Keep of Mahn-Tor (The Keep)', 'Galaxy',
        'Machine Dreams'] + list(ROUTES)
PINS = ['Corruption of Anciastra', 'Vale of Nidaros', 'Valley of Mysts', 'The Tower of Zenothir', "Wyvern's Tower",   # notes on where the pin is (owner, Oct 27)
        "La Chute D'eau De L'ancients", 'Raven Tor', 'Gnarlwood Forest', 'The Keep of Mahn-Tor (Ogre Village)', 'New Ofcol',
        'Tullfuhrzky Manor', "Ezard's Fields", 'Moria', 'Fire Station', 'Eastern Trade Route', 'Reomyr Village']


def apply(town, wild, pos):
    pl = {p['name']: p for p in wild['places']}
    rep = {'NS': 0, 'notes removed': 0, 'directions': 0}
    for p in wild['places']:
        if p.get('note') and 'down into the Blood Sea' in p['note']: p['note'] = NS; rep['NS'] += 1
        for o in p.get('opts') or []:
            if o.get('gap') and 'down into the Blood Sea' in o['gap']: o['gap'] = NS; rep['NS'] += 1
    for n in DROP + PINS:
        assert pl[n].get('note'), n
        pl[n]['note'] = None; rep['notes removed'] += 1
    dc = pl['Dwarven Catacombs']['opts'][0]
    assert dc['gap'] and "isn't mapped" in dc['gap']
    dc['gap'] = None; rep['notes removed'] += 1
    for n, raw in ROUTES.items():
        p = pl[n]; assert not p.get('opts'), n
        p['route'] = maplib.condense(raw); rep['directions'] += 1
    return rep
