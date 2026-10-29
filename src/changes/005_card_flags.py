"""Owner, Oct 29: card warnings. Level-restricted areas ('Restricted: Level N and under', N = the top of the card's level range;
site_template) and 'No astral travel to or from other geos.' on 9 more cards (`astrallocal`, shown without an Astral Points line too)."""

RESTRICTED = ['Along the Forest Path', 'The Sentinel', "Ezard's Fields", 'Haven of Everlasting Light']
NOASTRAL = ['The Blood Sea', 'Hurricane Island', 'Blood Sea - Fathomless Depths', 'Azure Sea', 'Otherland (Northern)', 'Otherland (Southern)',
            'Eastern Trade Route', 'Northern Trade Route', 'Western Trade Route']


def apply(town, wild, pos):
    P = {p['name']: p for p in wild['places'] + town['places']}
    for n in RESTRICTED: P[n]['restricted'] = True
    for n in NOASTRAL: assert not P[n].get('astrallocal'), n; P[n]['astrallocal'] = True
    return {'restricted': len(RESTRICTED), 'no astral': len(NOASTRAL)}
