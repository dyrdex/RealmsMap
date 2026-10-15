"""Markers for the areas that open off the Southern Mountain Range and its trade route (smr_marker_routes.json, made by smr_marker_routes.py).
Each marker sits on the range room where your directions step out of the range into the area. Areas with no directions in your list, or
whose directions reach them another way (not across the range), get a marker only, on the range room they open from; when there are
several such rooms, the one nearest the middle of them; a room you hid in the editor is replaced by the nearest room you kept."""
import math
NO_ROUTE = "There are no directions for this area in your list yet; the marker shows the range room it opens from."
OTHER_WAY = "Your directions reach this area another way, not across the Southern Mountain Range; the marker shows the range room it opens from."
DROP = set()                                                   # removed on request (Oct 12)
PORTAL = set()             # 'Before the Graveyard', where the painting in Alms for the Poor (783) sets you down, one step from the range's first room
                            # (4221): the traced line jumps there, which is not a gap in the map (owner, Oct 12)
EXTEND = {'Desert of Despair': [19863, 6365]}               # the marker moved on to these rooms (owner, Oct 15: down to room 6365)
GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."


def add_smr_subareas(w, smr_layout, routes):
    hidden = set(smr_layout['hidden'])
    pos = dict(zip(smr_layout['ids'], zip(smr_layout['xs'], smr_layout['ys'])))
    track = w.get('track') or {}
    shown = [v for v in pos if v not in hidden]
    def at(v):
        if v in pos: return pos[v]                                   # (the rooms you hid keep their place: the line runs through them)
        t = track.get('cx' + str(v)); return tuple(t[:2]) if t else None
    def site_of(v):
        return pos[v] if v not in hidden else min((pos[u] for u in shown), key=lambda p: math.dist(p, pos[v]))
    placed = []
    for r in routes:
        name = r['name']
        if name in DROP: continue
        if r['route']:
            site = site_of(r['door'])
            segs = []; cur = []; gaps = 0
            for v, area in r['trail']:
                p = at(v)
                if p: cur.append([round(p[0], 3), round(p[1], 3)])
                elif v in PORTAL: continue                  # the painting: the line runs straight on from Alms for the Poor to the range (owner, Oct 12)
                elif cur:
                    segs.append(cur); cur = []
                    if v not in PORTAL: gaps += 1
            for v_ in EXTEND.get(name, []):
                if v_ in pos: cur.append([round(pos[v_][0], 3), round(pos[v_][1], 3)]); site = pos[v_]
            cur.append([round(site[0], 3), round(site[1], 3)]); segs.append(cur)
            pl = dict(name=name, route=r['route'], room='the Southern Mountain Range', dir='here', path=[q for s in segs for q in s], segs=segs,
                      group='af', where='off the Southern Mountain Range', note=GAP_NOTE if gaps else None)
        else:
            ds = [v for v in r['doors'] if v in pos and v not in hidden] or r['doors']
            cx = sum(site_of(v)[0] for v in ds) / len(ds); cy = sum(site_of(v)[1] for v in ds) / len(ds)
            site = min((site_of(v) for v in ds), key=lambda p: math.dist(p, (cx, cy)))
            q = [round(site[0], 3), round(site[1], 3)]
            pl = dict(name=name, route=r.get('other_way') or '', room='the Southern Mountain Range', dir='here', path=[q], segs=[[q]],
                      group='af', where='off the Southern Mountain Range', noroute=True, note=OTHER_WAY if r.get('other_way') else NO_ROUTE)
        w['places'].append(pl); placed.append((name, round(site[0], 1), round(site[1], 1)))
    return w, placed
