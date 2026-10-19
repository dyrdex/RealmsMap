"""Owner, Oct 19: the Inahir Camp (Northern Plains) drawn: a palisade of sharpened wooden stakes around its 10 rooms, with 4671 (The
Outskirts of the Camp) left outside in a notch and a gate where each of its two exits enters the camp (east to 4672, south to 4680).
Inside, from the room names: hide tents in 'The Inahir Camp' rooms, a long house on 'Inside the Long House' (4679), a railed corral
over 'The Corral' (4676, 4681), and a fire pit in the middle of the yard. The camp's ground is trodden earth (Camden's style); trees, rocks, brush and wheat tufts inside the wall are cleared. Drawn by CAMPS in template.html, in old-map ink
(owner, Oct 19: no animals, 5 tents)."""
import math

X0, X1, Y0, Y1 = 6.9, 21.8, -158.2, -148.6                                       # the wall (as drawn, before moving with the rooms)
NX, NY = 9.75, -151.55                                                           # the notch's inner corner (4671 stays outside it)
WALL = [[NX, Y0], [X1, Y0], [X1, Y1], [X0, Y1], [X0, NY], [NX, NY]]
GATES = [[NX, -153.33, 1], [8.27, NY, 0]]                                         # x, y, 1 = in an upright (north-south) stretch of wall


CAMP = (4671, 4672, 4673, 4674, 4675, 4676, 4677, 4678, 4679, 4680, 4681)
AT = {4671: (8.14, -153.28), 4672: (11.31, -153.39), 4673: (11.3, -156.66), 4674: (14.34, -156.69), 4675: (17.06, -156.52),
      4676: (17.07, -153.25), 4677: (14.35, -153.42), 4678: (11.54, -150.07), 4679: (14.61, -150.2), 4680: (8.4, -150.06),
      4681: (20.25, -153.34)}                                     # where the camp's rooms were when it was drawn (Oct 19)


def apply(town, wild, pos):
    # the camp follows its rooms: everything is drawn relative to 4671; if the rooms were moved as one group it moves with them,
    # otherwise (rooms rearranged inside the camp) the build stops, so the camp can be redrawn to fit
    dx = sum(pos[str(v)][0] - AT[v][0] for v in CAMP) / len(CAMP); dy = sum(pos[str(v)][1] - AT[v][1] for v in CAMP) / len(CAMP)   # (the group's mean move)
    off = [v for v in CAMP if math.dist((pos[str(v)][0] - dx, pos[str(v)][1] - dy), AT[v]) > .15]     # (a drag's rounding is fine)
    assert not off, f'Inahir Camp rooms rearranged (not moved as one group): {off}; redraw the camp to fit'
    S = lambda p: [round(p[0] + dx, 3), round(p[1] + dy, 3)] + list(p[2:])
    X0, X1, Y0, Y1 = globals()['X0'] + dx, globals()['X1'] + dx, globals()['Y0'] + dy, globals()['Y1'] + dy
    NX, NY = globals()['NX'] + dx, globals()['NY'] + dy
    def _inside(x, y, m):                                         # inside the wall, or within m of it
        if not (X0 - m <= x <= X1 + m and Y0 - m <= y <= Y1 + m): return False
        return not (x < NX - m and y < NY - m)
    cr = [15.75 + dx, -154.7 + dy, 21.3 + dx, -151.9 + dy]
    camp = dict(wall=[S(p) for p in WALL], gates=[S(g) for g in GATES], gatew=1.0,
                tents=[S(t) for t in [[11.0, -157.0, 1.0], [14.3, -157.3, 1.0], [17.5, -156.9, .95], [12.1, -152.4, .9], [10.0, -149.4, .9]]],
                longhouse=S([14.61, -149.55, 3.4]), fire=S([12.85, -154.9]),
                corral=dict(rect=[round(v, 3) for v in cr], gate=S([15.75, -153.3])))
    wild.setdefault('camps', []).append(camp)
    g = [[NX - .15, Y0 + .15], [X1 - .15, Y0 + .15], [X1 - .15, Y1 - .15], [X0 + .15, Y1 - .15], [X0 + .15, NY + .15], [NX - .15, NY + .15]]
    wild['wltown'] = list(wild.get('wltown') or []) + [[[round(a, 2), round(b, 2)] for a, b in g]]   # trodden ground (drawn like Camden's)
    cleared = {}
    for k in ('trees', 'boulders', 'brush', 'wheattufts', 'tufts', 'hills'):
        arr = wild.get(k) or []; kept = [q for q in arr if not _inside(q[0], q[1], .6)]
        if len(kept) != len(arr): cleared[k] = len(arr) - len(kept); wild[k] = kept
    return dict(moved_with_rooms=[round(dx, 2), round(dy, 2)], tents=len(camp['tents']), wall_length=round(sum(math.dist(WALL[i], WALL[(i + 1) % len(WALL)]) for i in range(len(WALL))), 1),
                gates=len(GATES), cleared=cleared)
