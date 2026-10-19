"""Owner, Oct 19: the Inahir Camp redrawn in a new style, simpler and closer to the map (Edel's plan view): seen from above, solid shapes
with dark outlines and soft shadows instead of thin ink line-work. The earthen yard inside the wall; the palisade a solid band of
log tops with its two gates; the long house a thatched roof with its ridge; the corral a fenced pen of trampled ground; the fire pit
a ring of stones with embers; worn paths from the gates to the fire. No tents (owner). Same spots as before (from the v22 camp)."""


def apply(town, wild, pos):
    old = wild.get('camps') or []
    assert len(old) == 1, 'expected the one v22 camp'
    c = old[0]
    wall = c['wall']
    # the v22 trodden ground drawn for the camp (wltown) goes; the new drawing has its own yard
    near = lambda P: all(min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in wall) < .5 for p in P)
    n0 = len(wild['wltown']); wild['wltown'] = [P for P in wild['wltown'] if not (len(P) == len(wall) and near(P))]
    fx, fy = c['fire']
    paths = [[g[:2], [fx, fy]] for g in c['gates']]
    lx, ly, lw = c['longhouse']
    paths.append([[lx, ly + .15], [fx, fy]])                      # from the long house's door to the fire
    wild['camp2'] = [dict(wall=wall, gates=c['gates'], gatew=c.get('gatew', 1.0), longhouse=[lx, ly - .6, lw, 1.15],
                          corral=c['corral'], fire=c['fire'], paths=paths)]
    wild['camps'] = []
    return {'old camp drawing removed': 1, 'old yard ground removed': n0 - len(wild['wltown']), 'tents': 0, 'paths': len(paths)}
