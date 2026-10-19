"""Owner, Oct 19: the Forest of Tears editor save of 15:42Z: the new area's rooms (Asgard Nexus 2086, 2112, 2088, 2090, Sesuad'ra Rift 13608 and
the spacer rooms between) and The Shire's 1984 + spacer 21127, all hidden (they exist only so routes run in full; nothing of them is drawn).
- their spots go into the room positions the route tracer uses (2086 is treated as hidden too; room 2360's 0.34 nudge in the same save is not
  taken: it would redraw the forest)
- new destination "Sesuad'ra Rift" with the owner's directions, traced through the hidden rooms to 13608; its marker sits just off the end of
  the line, clear of the V'laresch and Old Thalos markers and names (`at`)
- V'laresch's directions (owner): ... #13 w;n;cauldron
- every route through these rooms traced again (markers stay); the 'not drawn yet' note goes when a route is one unbroken line"""
import math
import maplib

SAVE = {2112: (-85.16, -7.83), 21974: (-85.26, -7.81), 21973: (-85.24, -7.82), 13608: (-86.16, -7.8), 21972: (-85.21, -7.73), 21971: (-85.17, -7.7),
        21970: (-85.1, -7.8), 13607: (-85.21, -7.81), 2088: (-85.15, -7.03), 2090: (-85.18, -6.18), 2086: (-84.36, -7.85),
        1984: (-30.48, -1.61), 21127: (-31.01, -1.65)}                      # (the owner's save, ftlayout/current of 15:42Z)
NAME = "Sesuad'ra Rift"
ROUTE = 'w;w;w;w;w;w;w;w;w;nw;w;w;nw;w;n;n;nw;nw;nw;w;sw;sw;sw;sw;w;nw;nw;w;sw;w;w;w;w;w;w;w;w;w;w;w;w;w;n;cauldron;sw;enter'
VLARESCH = '#9 w;nw;#2 w;nw;w;#2 n;#3 nw;w;#4 sw;w;#2 nw;w;sw;#13 w;n;cauldron'
AT = [-86.5, -7.2]                                                           # the marker (0.6 from the line's end at 13608)
GAP = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."


def _segs(walk, at, route, end=None):
    """the traced line as unbroken pieces; up to the last time it reaches `end` (a marker on the line), else to its last placed room"""
    pts = [at(v) for v in walk(route)]
    idx = [i for i, q in enumerate(pts) if q and end and math.dist(q, end) < .02]
    if end and not idx: return None
    pts = pts[:idx[-1] + 1] if idx else pts[:max(i for i, q in enumerate(pts) if q) + 1]
    segs, cur = [], []
    for q in pts:
        if q is None:
            if cur: segs.append(cur); cur = []
        else: cur.append([round(q[0], 3), round(q[1], 3)])
    if cur: segs.append(cur)
    return segs


def _note(p, gap):
    n = (p.get('note') or '').replace(GAP, '').strip()
    p['note'] = (n + (' ' if n else '') + GAP) if gap else (n or None)


def apply(town, wild, pos):
    for v, q in SAVE.items(): pos[str(v)] = list(q)
    walk, at = maplib.tracer(pos, wild)
    rep = dict(retraced=[], kept=[])
    vl = next(p for p in wild['places'] if p['name'] == "V'laresch"); vl['route'] = VLARESCH
    for p in wild['places']:
        if not p.get('route') or p.get('noroute') or not ({*SAVE} & set(walk(p['route']))): continue
        s = _segs(walk, at, p['route'], p['path'][-1])
        if s and (len(s) < len(p['segs']) or p is vl):
            p['segs'] = s; p['path'] = [q for x in s for q in x]; _note(p, len(s) > 1); rep['retraced'].append((p['name'], len(s)))
        else: rep['kept'].append(p['name'])
    s = _segs(walk, at, ROUTE)
    assert math.dist(s[-1][-1], SAVE[13608]) < .02, s[-1][-1]
    p = dict(name=NAME, route=maplib.condense(ROUTE), room='The Misery of Mourning', dir='n', path=[q for x in s for q in x] + [AT], segs=s[:-1] + [s[-1] + [AT]],
             note=None, group='fot', at=AT)
    _note(p, len(s) > 1)
    wild['places'].append(p)
    rep['new'] = (NAME, p['route'], 'line pieces', len(s), 'marker', AT)
    return rep
