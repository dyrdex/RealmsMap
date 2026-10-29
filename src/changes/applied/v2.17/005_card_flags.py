"""Owner, Oct 29: card warnings. Level-restricted areas ('Restricted: Level N and under', N = the top of the card's level range;
site_template) and 'No astral travel to or from other geos.' on 9 more cards (`astrallocal`, shown without an Astral Points line too).
Later Oct 29: Northern Trade Route's note removed; danger notes on 4 cards (owner's words)."""

RESTRICTED = ['Along the Forest Path', 'The Sentinel', "Ezard's Fields", 'Haven of Everlasting Light']
NOASTRAL = ['The Blood Sea', 'Hurricane Island', 'Blood Sea - Fathomless Depths', 'Azure Sea', 'Otherland (Northern)', 'Otherland (Southern)',
            'Eastern Trade Route', 'Northern Trade Route', 'Western Trade Route']
NOTES = {'Northern Trade Route': None, 'Shadar Logoth': 'Danger: No Supplicate Area!', 'Realm of Worship': 'Danger!', "Shai'ghool": 'Danger!',
         "Mulciber's Forge": 'Danger!'}


def apply(town, wild, pos):
    P = {p['name']: p for p in wild['places'] + town['places']}
    for n in RESTRICTED: P[n]['restricted'] = True
    for n in NOASTRAL: assert not P[n].get('astrallocal'), n; P[n]['astrallocal'] = True
    for n, t in NOTES.items(): assert bool(P[n].get('note')) == (t is None), n; P[n]['note'] = t
    return {'notes': len(NOTES), 'restricted': len(RESTRICTED), 'no astral': len(NOASTRAL)}
