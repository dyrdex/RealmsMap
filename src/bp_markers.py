"""Markers for the areas that open off the Barren Peaks of Tahjliera (bp_marker_routes.json, made by bp_marker_routes.py).
Each marker sits on the Peaks room the area opens from (where your directions step out of the Peaks); if you hid that room in the editor,
on the nearest room you kept. The card traces your directions over every room that is on the map; where they pass through areas that
aren't drawn yet (the Northern Plains, through the painting) the traced line breaks. Areas with no directions in your list get a marker only."""
import math
GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
SITE_ROOM = {'Drow City': 7015, 'Reign of Madness': 21610, 'The Slime Pit': 18139}      # owner's choices (Oct 10): the marker sits on this room
SITE_XY = {'The Crimson Caverns': (-33.74, -94.82)}                                   # owner's choice (Oct 10): the marker sits here
RENAME = {'Asgard Nexus': "Z'hyal"}
DROP = {'World Housing', 'Asgard Nexus'}   # Asgard Nexus (shown as Z'hyal) removed on request (Oct 12)
WOODS = {'Tower of Enlightenment': (5644, 1.2)}                                       # markers in the Forgotten Woods: just south of this room (rooms)
GFX = [dict(k='keep', label="Barrik's Keep", at='above-pin', w=1.9, h=2.9, dx=-1.75, dy=1.85),          # just west of the pin
       dict(k='palisade', at='xy', x=-14.03, y=-135.38, w=2.2, h=1.65),          # owner asked for about (-16.63,-133.88); nudged 3 rooms NE (and drawn a little smaller) to clear the village's label, pins and paths              # barbarian village: palisade of sharpened poles
       dict(k='stonecity', label='Drow City', at='above-pin', w=2.6, h=2.15),                          # north of the pin
       dict(k='stonecity', label='Revelation City', at='above-text', w=2.6, h=2.15, dy=0.4),   # sits close above its name
       dict(k='ruin', at='xy', x=-32.0, y=-110.87, w=2.0, h=1.4),          # owner's spot, bumped east off the marker
       dict(k='darkpeak', at='xy', x=-39.16, y=-131.36, w=3.6, h=2.4)]                   # a big dark scary mountain, 2.6 rooms east of the Mountain of Lost Souls marker (owner, Oct 12; was at -30.42,-130.49)                    # south of the pin: a dilapidated stone building
NO_ROUTE = "There are no directions for this area in your list yet; the marker shows the Peaks room it opens from."


PORTAL = {4222}             # 'Before the Graveyard', where the painting in Alms for the Poor (783) sets you down, next to the Plains


def add_bp_subareas(w, bp_layout, ntr_layout, routes, np_layout=None):
    hidden = set(bp_layout['hidden'])
    pos = dict(zip(bp_layout['ids'], zip(bp_layout['xs'], bp_layout['ys'])))
    for v, x, y in zip(ntr_layout['ids'], ntr_layout['xs'], ntr_layout['ys']): pos.setdefault(v, (x, y))
    track = w.get('track') or {}
    shown = [v for v in pos if v not in hidden and v in set(bp_layout['ids'])]
    npos = {v: (x, y) for v, x, y in zip(np_layout['ids'], np_layout['xs'], np_layout['ys']) if v not in set(np_layout['hidden'])} if np_layout else {}
    def at(v):
        if v in pos: return pos[v]
        if v in npos: return npos[v]                                     # routes across the Northern Plains (owner, Oct 12)
        t = track.get('cx' + str(v)); return tuple(t[:2]) if t else None
    placed = []
    for r in routes:
        if r['name'] in DROP: continue
        door = r['door']; trail = r['trail']; name = RENAME.get(r['name'], r['name'])
        if r['name'] in WOODS:
            v0, dy = WOODS[r['name']]; c = track['cx' + str(v0)]; site = (c[0], c[1] + dy)
        elif r['name'] in SITE_XY: site = SITE_XY[r['name']]
        elif r['name'] in SITE_ROOM:
            v0 = SITE_ROOM[r['name']]; site = pos[v0]
            ids = [q[0] for q in trail]
            if v0 in ids: trail = trail[:ids.index(v0) + 1]
        else: site = pos[door] if door not in hidden else min((pos[v] for v in shown), key=lambda p: math.dist(p, pos[door]))
        segs = []; cur = []
        for v, area in trail:
            p = at(v)
            if p: cur.append([round(p[0], 3), round(p[1], 3)])
            elif v in PORTAL: continue                                   # the painting: the line runs straight on to the Plains (owner, Oct 12)
            elif cur: segs.append(cur); cur = []
        cur.append([round(site[0], 3), round(site[1], 3)]); segs.append(cur)
        woods = r['name'] in WOODS
        pl = dict(name=name, route=r['route'], room='the Forgotten Woods' if woods else 'the Barren Peaks', dir='here', path=[q for s in segs for q in s], segs=segs,
                  group='fw' if woods else 'af', where='in the Forgotten Woods' if woods else 'off the Barren Peaks of Tahjliera', note=None if len(segs) == 1 else GAP_NOTE)
        if not r['route']: pl.update(noroute=True, note=NO_ROUTE, path=[cur[-1]], segs=[[cur[-1]]])
        w['places'].append(pl); placed.append((name, round(site[0], 1), round(site[1], 1), 'moved off a hidden room' if door in hidden and r['name'] not in SITE_XY and r['name'] not in SITE_ROOM and not woods else ''))
    w['gfx'] = list(w.get('gfx', [])) + [dict(x) for x in GFX]
    return w, placed
