"""Owner, Oct 19: New Ofcol and the City of Salburg drawn like the other cities (Revelation City, Drow City, Thalos): the standard
round marker with the stone-city drawing just above it, instead of the white walled-town emblem."""
CITIES = ('New Ofcol', 'City of Salburg')


def apply(town, wild, pos):
    done = []
    for p in wild['places']:
        if p['name'] in CITIES and p.get('kind') == 'town':
            del p['kind']; done.append(p['name'])
    assert sorted(done) == sorted(CITIES), done
    for n in CITIES:                                               # (the same drawing and spot as Drow City's)
        wild['gfx'].append({'k': 'stonecity', 'label': n, 'at': 'above-pin', 'w': 2.6, 'h': 2.15})
    box = (41.9, -47.25, 44.5, -45.1)                              # the one tree under Salburg's drawing (Ofcol's spot is clear)
    n0 = len(wild['trees']); wild['trees'] = [q for q in wild['trees'] if not (box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3])]
    return {'emblem replaced': done, 'trees under the drawings removed': n0 - len(wild['trees'])}
