"""Owner, Oct 29: area names. 'Barren Peaks' -> 'Barren Peaks of Tahjliera' (the place, the cards that are reached at it, Z'hyal's
location there); 'City of Aurora' -> 'The Ancient City of Aurora'."""

NAMES = {'Barren Peaks': 'Barren Peaks of Tahjliera', 'City of Aurora': 'The Ancient City of Aurora'}


def apply(town, wild, pos):
    rep = {'renamed': 0, 'reached at': 0, 'deity locations': 0}
    for p in wild['places']:
        if p['name'] in NAMES: p['name'] = NAMES[p['name']]; rep['renamed'] += 1
        if p.get('room') == 'the Barren Peaks': p['room'] = 'the Barren Peaks of Tahjliera'; rep['reached at'] += 1
        for o in p.get('opts') or []:
            if o.get('sub') in NAMES:
                o['dir'] = o['dir'].replace(o['sub'], NAMES[o['sub']]); o['sub'] = NAMES[o['sub']]; rep['deity locations'] += 1
    assert rep['renamed'] == 2, rep
    return rep
