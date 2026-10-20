"""Owner, Oct 20: the Desert of Despair's sub-areas, mazes and a link label.
Markers (routes from data.py, traced from Darkhaven Square; one piece each):
  - Daichaal: leaves the desert at 6520 Wastelands road, south-east (as traced);
  - Barren Wastes: the marker at 13061 Traveling the sands...., the drawn route ends there (its directions on file go on: dig down);
  - Great Eastern Desert: the marker on 9057 The Great Eastern Desert, on a sandy maze blob round it;
  - Blasted Lands: the marker on spacer 22145 (north of 9057), on a sandy maze blob round it; the route runs on from 9057 to it
    ('scan for entrance');
  - Thul Ab'hara: the marker on hidden 6561 The mouth of a cave; The Dungeon: on hidden 929 A roughly hewn tunnel. The rooms stay hidden;
    the routes run over them.
Mazes: sandy maze blobs (fwmazes, style 'desert', no name) round 4050 (Traveling the sands...), 9057 and 22145.
Area name: Desert / Of / Despair in the middle. Label: "(Emerald Hills)", small text west of 6366 Wandering the Desert (its exit west leads to the Emerald Hills)."""
import math, random, re
import maplib, data

R = lambda q: [round(q[0], 3), round(q[1], 3)]
GAP = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
WHERE = 'off the Desert of Despair'
# name, marker room (the drawn route ends there), extra point after it (or None)
PLACES = [('Daichaal', None, None), ('Barren Wastes', 13061, None), ('Great Eastern Desert', 9057, None),
          ('Blasted Lands', 9057, 22145), ("Thul Ab'hara", 6561, None), ('The Dungeon', 929, None)]
# mazes: (room, centre offset, rx, ry, extra fields). Traveling the sands... over the paths, with its name (owner, Oct 20); the Great Eastern Desert's
# much bigger, round the Blasted Lands' (a maze within a maze: owner, Oct 20), kept clear of the steppes' clearing (its east edge ~52.1); Blasted
# Lands' drawn after it, darker, so it reads as a maze inside it
MAZES = [(4050, (0, 0), 2.7, 2.3, dict(top=True, name='Traveling the sands...', nolabel=False, fs=0.62, bottom=135.842)),   # (bigger to the north, east and west, its south edge kept: owner, Oct 20)
         (9057, (1.9, -2.15), 3.45, 3.75, {}),
         (22145, (0, 0), 1.4, 1.19, dict(fill='#352C1E', edge='#EAD9AE'))]
AREA_NAME = dict(x=72.5, y=99.5, lh=2.8, sag=0.5, hw=6, lines=['Desert', 'Of', 'Despair'])   # one word per line, in the open ground between the trails at x 65 and x 80 (owner, Oct 20)
OASIS = (13630, 3.2, 2.2)                                    # the oasis round 13630 (owner, Oct 20): a medium drawing centred on it
BOULDERS = [6403, 6391, 6459, 6395]                          # the quest's large boulders (owner, Oct 20), one on each room
LABEL_ROOM, LABEL_DX = 6366, -1.9                            # "(Emerald Hills)": centred this far west of 6366, on its line (0.48 clear of the Tayalardian Rangelands name, 0.34 of the trail)


def blob(cx, cy, rx, ry, rng, n=26):
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(n):
        a = 6.2832 * i / n
        k = 1 + 0.07 * math.sin(2 * a + ph[0]) + 0.05 * math.sin(3 * a + ph[1]) + 0.03 * math.sin(5 * a + ph[2])
        pts.append([round(cx + rx * k * math.cos(a), 3), round(cy + ry * k * math.sin(a), 3)])
    return pts


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    routes = dict(l.split('|', 1) for l in data.AREAS.strip().splitlines() if '|' in l)
    rep = {}
    for name, end, extra in PLACES:
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(routes[name].strip().rstrip(';'))
        t = walk(route)
        if end is None: k = max(i for i, v in enumerate(t) if at(v))
        else: k = t.index(end)
        upto = t[:k + 1]
        segs, cur = [], []
        for v in upto:
            q = at(v)
            if q is None:
                if cur: segs.append(cur); cur = []
            else: cur.append(R(q))
        if cur: segs.append(cur)
        if extra is not None: segs[-1].append(R(at(extra)))
        last = upto[-1] if extra is None else extra
        d = 'here' if (end is not None or k == len(t) - 1) else re.sub(r'^#\s*\d+\s*', '', route.split(';')[-1].strip())
        wild['places'].append(dict(name=name, route=route, room=rooms[last]['name'] or rooms[upto[-1]]['name'], dir=d, path=[q for s in segs for q in s], segs=segs,
                                   group='af', where=WHERE, note=None if len(segs) == 1 else GAP))
        rep[name] = dict(marker_room=last, at=segs[-1][-1], dir=d, pieces=len(segs), walked=len(t), drawn_to=len(upto))
    rng = random.Random(2010)                                   # (its own random numbers: nothing else moves)
    rep['mazes'] = []
    for v, (ox, oy), rx, ry, extra in MAZES:
        cx, cy = at(v)[0] + ox, at(v)[1] + oy
        m = dict(name='', nolabel=True, style='desert', cx=round(cx, 3), cy=round(cy, 3), poly=blob(cx, cy, rx, ry, rng)); m.update(extra)
        if 'bottom' in m:                                                           # (moved up so its south edge stays where it was)
            dy = m.pop('bottom') - max(q[1] for q in m['poly'])
            m['poly'] = [[q[0], round(q[1] + dy, 3)] for q in m['poly']]; m['cy'] = round(m['cy'] + dy, 3)
        if not m['nolabel']: del m['nolabel']
        wild['fwmazes'].append(m); rep['mazes'].append((v, m['cx'], m['cy'], rx, ry))
    q = at(OASIS[0])
    wild['gfx'] = list(wild['gfx']) + [{'k': 'oasis', 'at': 'xy', 'x': round(q[0], 2), 'y': round(q[1], 2), 'w': OASIS[1], 'h': OASIS[2]}] + \
        [{'k': 'bigboulder', 'at': 'xy', 'x': round(at(v)[0], 2), 'y': round(at(v)[1], 2), 'w': 1.65, 'h': 1.32} for v in BOULDERS]
    rep['oasis'] = q; rep['boulders'] = {v: at(v) for v in BOULDERS}
    wild['arealabels'] = list(wild.get('arealabels') or []) + [AREA_NAME]          # the area's name in the empty middle of the desert (owner, Oct 20)
    rep['area_name'] = AREA_NAME
    q = at(LABEL_ROOM)
    g = {'k': 'text', 'at': 'xy', 'x': round(q[0] + LABEL_DX, 2), 'y': round(q[1] + 0.13, 2), 'text': '(Emerald Hills)'}
    wild['gfx'] = list(wild['gfx']) + [g]
    rep['label'] = g
    return rep
