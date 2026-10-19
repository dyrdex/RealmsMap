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

SUDS_ROUTE = '#8 w;sw;s;#2 sw;s;#2 w;#2 sw;w;se;sw;se;sw;se;#2 sw;se;#2 s;sw;s;sw;s;se;e;ne;se;s;se;e'
SUDS_DOT = (-12.06, 51.75)                                                        # just above the inn graphic (owner, Oct 15: the usual place name, no separate inn label)
AEN_ROUTE = '#8 n;ne;w;n;ne;nw;e;ne;n;e;ne;#2 n;#2 ne;#2 e;n;ne;nw;w;#4 n;enter;ne;w'   # (owner's new directions, Oct 15)
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
                            group='af', where='on the Southern Mountain Trade Route', at=list(SUDS_DOT),
                            note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
    report['suds'] = dict(end=t[-1], pieces=len(segs), dot=SUDS_DOT)
    # V'laresch -> Mobs
    v = [p for p in w['places'] if p['name'] == "V'laresch"]; assert len(v) == 1
    v[0]['kind'] = 'mob'; report['vlaresch'] = 'mob'
    # A'enari: in full over the Pixie Forest layout (owner's save, Oct 15) when every room has a spot; otherwise the rough guess below
    t = walk(AEN_ROUTE)
    if t[-1] == 12232 and all(at(x) for x in t):
        segs = segments([at(x) for x in t])
        w['places'].append(dict(name="A'enari", route=numbered(AEN_ROUTE), room=rooms[12232]['name'], dir='here', kind='mob',
                                path=[q for s in segs for q in s], segs=segs, group='af', where='in the Asgard Nexus, past the Pixie Forest', note=None))
        report['aenari'] = dict(full=True, marker=segs[-1][-1], pieces=len(segs))
    else:
        w, report['aenari'] = _aenari_rough(w, rooms, walk, at, exits)
    # Reomyr Village: its line now runs on through the Pixie Forest to 5004, the room it is 'u' from; the pin goes there
    p = next(p for p in w['places'] if p['name'] == 'Reomyr Village')
    t = walk(p['route'])
    if 5004 in t and all(at(x) for x in t[:t.index(5004) + 1]):
        segs = segments([at(x) for x in t[:t.index(5004) + 1]])
        p.update(path=[q for s in segs for q in s], segs=segs, dir='here', room=rooms[5004]['name'],
                 note="Reomyr Village is up (u) from this room of the Pixie Forest.")
        report['reomyr'] = dict(marker=segs[-1][-1], pieces=len(segs))
    # Pixie Forest (owner's new directions, Oct 15): they run into the Pixie Forest at 4993 and end at 4994; its rooms have spots now, so the line runs there and so does the pin
    p = next(p for p in w['places'] if p['name'] == 'Pixie Forest')
    t = walk(p['route'])
    if t[-1] == 4994 and all(at(x) for x in t):
        segs = segments([at(x) for x in t])
        p.update(path=[q for s in segs for q in s], segs=segs, dir='here', room=rooms[4994]['name'], note=None)
        report['pixie'] = dict(marker=segs[-1][-1], pieces=len(segs))
    return w, report


def _aenari_rough(w, rooms, walk, at, exits):
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
    return w, dict(last_mapped=t[known], unmapped=unmapped, marker=[round(x0, 2), round(y0, 2)], pieces=len(segs))
