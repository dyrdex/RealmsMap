"""Places added or changed on request (owner, Oct 15).
  - Suds 'n Stones (the inn on the Southern Mountain Trade Route, room 9303): a destination now. The owner's directions end on the road outside it (room 9301,
    'Deeper Within the Mountain Canyon'; TinTin's 'n' from there is the inn), so the traced line ends there. A small dot sits just west of the inn's existing
    label (gfx text from smr_merge, size unchanged); the place has no label of its own (`nolabel`), the existing one names it.
  - V'laresch: listed under Mobs (kind 'mob').
  - A'enari (mob): the owner's directions run through the Pixie Forest (not drawn) into the Asgard Nexus (kept off the map). The line is traced over the map as
    far as room 4019 (Markings of Possession, Forgotten Woods), then on through the unmapped rooms one step per direction (TinTin's exit directions, 0.8 apart:
    the Forgotten Woods' scale) as far as the room where the directions say 'enter' (5018, Bright Beginnings); the marker is there."""
import itertools, math
import ashen_forest as AF
from route_fix import make_tracer

SUDS_ROUTE = 'w;w;w;w;w;w;w;w;sw;s;sw;sw;s;w;w;sw;sw;w;se;sw;se;sw;se;sw;sw;se;s;s;sw;s;sw;s;se;e;ne;se;s;se;e'
SUDS_DOT = (-13.75, 51.47)                                                        # just west of the label 'Suds 'n Stones' (centred -12.06, 51.6)
AEN_ROUTE = 'e;e;e;e;e;e;e;e;ne;ne;ne;e;e;e;ne;e;ne;e;e;n;n;n;n;n;sw;nw;w;n;n;n;n;enter;ne;w'
STEP = 0.8


def numbered(r):
    return ';'.join((f'#{len(g)} {d}' if len(g) > 1 else d) for d, g in ((d, list(g)) for d, g in itertools.groupby(r.split(';'))))


def segments(pts):
    segs, cur = [], []
    for q in pts:
        if q is None:
            if cur: segs.append(cur); cur = []
        else: cur.append([round(q[0], 3), round(q[1], 3)])
    if cur: segs.append(cur)
    return segs


def add_extra_places(w, layouts):
    rooms, walk, at = make_tracer(w, layouts)
    _, exits = AF._world()
    report = {}
    # Suds 'n Stones
    t = walk(SUDS_ROUTE)
    assert t[-1] == 9301, t[-1]
    segs = segments([at(v) for v in t])
    w['places'].append(dict(name="Suds 'n Stones", route=numbered(SUDS_ROUTE), room=rooms[9301]['name'], dir='n', path=[q for s in segs for q in s], segs=segs,
                            group='af', where='on the Southern Mountain Trade Route', at=list(SUDS_DOT), small=True, nolabel=True,
                            note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
    report['suds'] = dict(end=t[-1], pieces=len(segs), dot=SUDS_DOT)
    # V'laresch -> Mobs
    v = [p for p in w['places'] if p['name'] == "V'laresch"]; assert len(v) == 1
    v[0]['kind'] = 'mob'; report['vlaresch'] = 'mob'
    # A'enari
    toks = AEN_ROUTE.split(';'); k = toks.index('enter')
    t = walk(';'.join(toks[:k]))
    known = max(i for i, x in enumerate(t) if at(x))
    pts = [at(x) for x in t[:known + 1]]
    x0, y0 = pts[-1]; unmapped = []
    for a, b in zip(t[known:], t[known + 1:]):
        d = next(e['dir'] for e in exits[a] if e['to'] == b); dv = AF.DV[d]
        x0, y0 = x0 + dv[0] * STEP, y0 + dv[1] * STEP; pts.append((x0, y0)); unmapped.append(b)
    segs = segments(pts)
    w['places'].append(dict(name="A'enari", route=numbered(AEN_ROUTE), room=rooms[12232]['name'] if 12232 in rooms else 'Serenity', dir='here', kind='mob',
                            path=[q for s in segs for q in s], segs=segs, group='af', where='in the Asgard Nexus, past the Pixie Forest',
                            note="The Pixie Forest isn't drawn yet: the end of the line and this pin are placed roughly, where your directions say 'enter'."))
    report['aenari'] = dict(last_mapped=t[known], unmapped=unmapped, marker=[round(x0, 2), round(y0, 2)], pieces=len(segs))
    return w, report
