"""Owner, Oct 19: the Inahir Camp redrawn in a new style, simpler and closer to the map (Edel's plan view): seen from above, solid shapes
with dark outlines and soft shadows instead of thin ink line-work. The earthen yard inside the wall; the palisade a solid band of
log tops with its two gates; the long house a thatched roof with its ridge; the corral a fenced pen of trampled ground; the fire pit
a ring of stones with embers. No tents, no paths (owner). Owner, Oct 19 (2nd look): the long house stretched east-west to 6.2 rooms
(was 3.4); 5 small round huts, thatched like the long house, where the v22 tents stood. Same spots as before (from the v22 camp)."""


LONG = 6.2                                                       # the long house's length east-west (owner: larger)


def apply(town, wild, pos):
    old = wild.get('camps') or []
    assert len(old) == 1, 'expected the one v22 camp'
    c = old[0]
    wall = c['wall']
    # the v22 trodden ground drawn for the camp (wltown) goes; the new drawing has its own yard
    near = lambda P: all(min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in wall) < .5 for p in P)
    n0 = len(wild['wltown']); wild['wltown'] = [P for P in wild['wltown'] if not (len(P) == len(wall) and near(P))]
    lx, ly, lw = c['longhouse']
    huts = [[t[0], t[1] - .35, .42] for t in c['tents']]           # (a tent's spot was its foot; a hut is centred a little above it)
    wild['camp2'] = [dict(wall=wall, gates=c['gates'], gatew=c.get('gatew', 1.0), longhouse=[lx, ly - .6, LONG, 1.25],
                          corral=c['corral'], fire=c['fire'], huts=huts)]
    wild['camps'] = []
    return {'old camp drawing removed': 1, 'old yard ground removed': n0 - len(wild['wltown']), 'tents': 0, 'paths': 0, 'huts': len(huts), 'long house': [LONG, 1.25]}
