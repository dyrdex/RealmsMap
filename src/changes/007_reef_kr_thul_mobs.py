"""Owner, Oct 25:
  - The Spiral Reef: a large spiral, fully under water, round Blood Sea - Fathomless Depths' name and marker: 5.5 turns, an ellipse
    (wider than tall, like the name), wavy, very faint (template REEF, `wild.reef`); 1.5 clear of Hurricane Island.
  - Knights of the Round: the DAG route is the default (first) option; its line runs to the Darkhaven Art Gallery, then a jump (dashed arc,
    `jumps`) up to the Knights of the Round marker. The marker stays where it was (`at`).
  - Thul Ab'hara: route options 'Northern Entrance (River)', 'Northern Entrance (East)' (the two it had, to its original entrance) and
    'Southern Entrance' (the owner's directions; drawn as far as 6475 Traveling the Western Road, the last drawn room); a second marker
    (`more`) on 6475 opening the card on the Southern Entrance.
  - Mobs: Karl (Camelot's Reparations): line to the gallery, a jump to the first drawn Knights of the Round room (11737), then the path to
    Camelot's Grand Entryway 14084, where it stops (the marker there). Jokaan's Repair Shop: card line 'Can portal from #8 s'; line = the
    Southern Entrance's (ends at 6475); its marker 0.9 east of 6475 (Thul Ab'hara's second marker is on 6475)."""
import math, random, maplib
from shapely.geometry import Polygon, Point

R = lambda q: [round(q[0], 3), round(q[1], 3)]
SOUTH = 's;s;s;s;s;s;s;s;s;s;s;s;s;e;e;u;u;e;se;se;se;d;s;se;se;s;s;s;s;se;se;se;sw;w;w;sw;s;s;s;se;s;sw;s;se;s;s;s;e;s;d;se;d'
JOKAAN = SOUTH + ';ne;nw;w;nw;ne;ne;n;n;nw;e'
KARL = '#4 s;w;#2 n;#2 n;w;nw;w;nw;w;sw;w;enter;#3 s;#3 w;#4 s;w;e;s;e;w;#4 n;n;n;n;e'
SOUTH_ROOM, CASTLE = 6475, 14084
NAME_W = 10.9                          # 'Blood Sea - Fathomless Depths' at .96 (from the 1.4 name 'Hurricane Island': 8.81 for 16 letters)
TURNS, R_IN, RX, RY = 5.5, 0.7, 8.0, 5.8


def apply(town, wild, pos):
    rooms, exits = maplib.world(); walk, at = maplib.tracer(pos, wild); rep = {}
    def trace(route, stop=None):
        t = walk(route); path = []
        for v in t:
            if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
            if v == stop: break
        return t, path
    pl = {p['name']: p for p in wild['places']}
    # ---- Knights of the Round: DAG first, with a jump to the marker ----
    kr = pl['Knights of the Round']; mk = R(kr['path'][-1]); walkopt, dag = kr['opts']
    gal = dag['segs'][-1][-1]
    dag['segs'] = [list(dag['segs'][0]) + [mk]]
    dag['gap'] = 'Through the "Mists at Ends" painting in the Darkhaven Art Gallery: enter it and you arrive at The Cadbury Chocolate Factory in the Knights of the Round (the dashed jump on the map).'
    kr['opts'] = [dag, walkopt]; kr['route'] = dag['route']; kr['at'] = mk; kr['path'] = dag['segs'][0]; kr['segs'] = dag['segs']
    wild['jumps'] = list(wild.get('jumps') or []) + [[gal[0], gal[1], mk[0], mk[1], 'Mists at Ends painting']]
    rep['Knights of the Round: default DAG, jump'] = (gal, mk)
    # ---- Thul Ab'hara: Northern (its two) + Southern Entrance, second marker ----
    th = pl["Thul Ab'hara"]; t, sp = trace(maplib.condense(SOUTH), SOUTH_ROOM)
    assert SOUTH_ROOM in t and sp[-1] == R(pos[str(SOUTH_ROOM)])
    for o in th['opts']: o['dir'] = 'Northern Entrance (' + o['dir'] + ')'
    th['opts'] = th['opts'] + [dict(dir='Southern Entrance', rooms=None, note=None, route=maplib.condense(SOUTH), segs=[sp], gap=None)]
    th['more'] = [dict(at=sp[-1], opt=len(th['opts']) - 1)]
    rep["Thul Ab'hara Southern Entrance: rooms walked, drawn to"] = (len(t) - 1, sp[-1])
    # ---- mobs ----
    t, kp = trace(maplib.condense(KARL), CASTLE)
    i = next(k for k, q in enumerate(kp) if q[1] < -20)                   # the first Knights of the Round room after the painting
    wild['jumps'].append([kp[i - 1][0], kp[i - 1][1], kp[i][0], kp[i][1], 'Mists at Ends painting'])
    wild['places'].append(dict(name='Karl', route=maplib.condense(KARL), room="Camelot's Reparations", dir='here', kind='mob', group='af',
                               where='in the Knights of the Round', note=None, path=kp, segs=[kp], at=kp[-1]))
    rep['Karl: jump, stops at'] = ((kp[i - 1], kp[i]), kp[-1], rooms[CASTLE]['name'])
    t, jp = trace(maplib.condense(JOKAAN), SOUTH_ROOM)
    jat = [round(jp[-1][0] + 0.9, 2), jp[-1][1]]
    wild['places'].append(dict(name="Jokaan's Repair Shop", route=maplib.condense(JOKAAN), room="Jokaan's Repair Shop", dir='here', kind='mob', group='af',
                               where="off the Desert of Despair", card='Can portal from #8 s', note=None, path=jp, segs=[jp], at=jat))
    rep["Jokaan: line ends, marker"] = (jp[-1], jat, 'route walks %d rooms' % (len(t) - 1))
    # ---- the Spiral Reef ----
    fd = pl['Blood Sea - Fathomless Depths']; mx, my = fd['at']
    x0, x1 = mx - 0.55 - NAME_W, mx + 0.36; cx, cy = round((x0 + x1) / 2, 2), round(my + 0.1, 2)
    rng = random.Random(4242); ph = rng.uniform(0, 6.3); pts = []
    n = int(TURNS * 120)
    for k in range(n + 1):
        th_ = 2 * math.pi * TURNS * k / n; f = R_IN / RX + (1 - R_IN / RX) * k / n
        w = 1 + 0.035 * math.sin(18 * th_ / TURNS * 1.0 + ph) + 0.02 * math.sin(7 * th_ + 2 * ph)
        pts.append([round(cx + RX * f * w * math.cos(th_), 3), round(cy + RY * f * w * math.sin(th_), 3)])
    wild['reef'] = pts
    hi = Polygon(wild['hurricane']['isle'])
    rep['Spiral Reef: centre, size, turns, to Hurricane Island'] = ((cx, cy), (2 * RX, 2 * RY), TURNS, round(hi.distance(Polygon(pts).convex_hull), 2))
    return rep
