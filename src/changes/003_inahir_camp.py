"""Owner, Oct 19: the Inahir Camp (Northern Plains) drawn: a palisade of sharpened wooden stakes around its 10 rooms, with 4671 (The
Outskirts of the Camp) left outside in a notch and a gate where each of its two exits enters the camp (east to 4672, south to 4680).
Inside, from the room names: hide tents in 'The Inahir Camp' rooms, a long house on 'Inside the Long House' (4679), a railed corral with
two horses over 'The Corral' (4676, 4681), and a fire pit in the middle of the yard. The camp's ground is trodden earth (Camden's style);
trees, rocks, brush and wheat tufts inside the wall are cleared. Drawn by CAMPS in template.html."""
import math

R = {4671: (8.14, -153.28), 4672: (11.31, -153.39), 4680: (8.4, -150.06)}          # (as in base/map.json's room_pos)
X0, X1, Y0, Y1 = 6.9, 21.8, -158.2, -148.6                                       # the wall
NX, NY = 9.75, -151.55                                                           # the notch's inner corner (4671 stays outside it)
WALL = [[NX, Y0], [X1, Y0], [X1, Y1], [X0, Y1], [X0, NY], [NX, NY]]
GATES = [[NX, -153.33, 1], [8.27, NY, 0]]                                         # x, y, 1 = in an upright (north-south) stretch of wall


def _inside(x, y, m):
    """inside the wall, or within m of it"""
    if not (X0 - m <= x <= X1 + m and Y0 - m <= y <= Y1 + m): return False
    return not (x < NX - m and y < NY - m)


def apply(town, wild, pos):
    for v, q in R.items(): assert math.dist(pos[str(v)], q) < 0.01, v
    camp = dict(wall=WALL, gates=GATES, gatew=1.0,
                tents=[[10.4, -157.3, 1.0], [12.4, -156.9, .9], [14.1, -157.4, 1.0], [15.7, -156.6, .85], [17.5, -157.3, 1.0],
                       [19.5, -156.5, .9], [12.1, -152.4, .85], [14.9, -152.2, .8], [9.4, -149.4, .9], [11.2, -149.2, .85]],
                longhouse=[14.61, -149.55, 3.4], fire=[12.85, -154.9],
                corral=dict(rect=[15.75, -154.7, 21.3, -151.9], gate=[15.75, -153.3], horses=[[18.5, -153.3, 0], [20.3, -152.5, 1]]))
    wild.setdefault('camps', []).append(camp)
    g = [[NX - .15, Y0 + .15], [X1 - .15, Y0 + .15], [X1 - .15, Y1 - .15], [X0 + .15, Y1 - .15], [X0 + .15, NY + .15], [NX - .15, NY + .15]]
    wild['wltown'] = list(wild.get('wltown') or []) + [[[round(a, 2), round(b, 2)] for a, b in g]]   # trodden ground (drawn like Camden's)
    cleared = {}
    for k in ('trees', 'boulders', 'brush', 'wheattufts', 'tufts', 'hills'):
        arr = wild.get(k) or []; kept = [q for q in arr if not _inside(q[0], q[1], .6)]
        if len(kept) != len(arr): cleared[k] = len(arr) - len(kept); wild[k] = kept
    return dict(tents=len(camp['tents']), wall_length=round(sum(math.dist(WALL[i], WALL[(i + 1) % len(WALL)]) for i in range(len(WALL))), 1),
                gates=len(GATES), cleared=cleared)
