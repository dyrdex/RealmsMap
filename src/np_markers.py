"""Markers for the areas that open off the Northern Plains (np_marker_routes.json, made by np_marker_routes.py).
Each marker sits on the Plains room where your directions step out of the Plains into the area. Areas with no directions in your list, or
whose directions reach them another way (not across the Plains), get a marker only, on the Plains room they open from; when there are
several such rooms, the one nearest the middle of them; a room you hid in the editor is replaced by the nearest room you kept."""
import math
NO_ROUTE = "There are no directions for this area in your list yet; the marker shows the Plains room it opens from."
OTHER_WAY = "Your directions reach this area another way, not across the Northern Plains; the marker shows the Plains room it opens from."
DROP = {'The Blood Sea'}                                                   # removed on request (Oct 12)
GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."


def add_np_subareas(w, np_layout, routes):
    hidden = set(np_layout['hidden'])
    pos = dict(zip(np_layout['ids'], zip(np_layout['xs'], np_layout['ys'])))
    track = w.get('track') or {}
    shown = [v for v in pos if v not in hidden]
    def at(v):
        if v in pos and v not in hidden: return pos[v]
        t = track.get('cx' + str(v)); return tuple(t[:2]) if t else None
    def site_of(v):
        return pos[v] if v not in hidden else min((pos[u] for u in shown), key=lambda p: math.dist(p, pos[v]))
    placed = []
    for r in routes:
        name = r['name']
        if name in DROP: continue
        if r['route']:
            site = site_of(r['door'])
            segs = []; cur = []
            for v, area in r['trail']:
                p = at(v)
                if p: cur.append([round(p[0], 3), round(p[1], 3)])
                elif cur: segs.append(cur); cur = []
            cur.append([round(site[0], 3), round(site[1], 3)]); segs.append(cur)
            pl = dict(name=name, route=r['route'], room='the Northern Plains', dir='here', path=[q for s in segs for q in s], segs=segs,
                      group='af', where='off the Northern Plains', note=None if len(segs) == 1 else GAP_NOTE)
        else:
            ds = [v for v in r['doors'] if v in pos and v not in hidden] or r['doors']
            cx = sum(site_of(v)[0] for v in ds) / len(ds); cy = sum(site_of(v)[1] for v in ds) / len(ds)
            site = min((site_of(v) for v in ds), key=lambda p: math.dist(p, (cx, cy)))
            q = [round(site[0], 3), round(site[1], 3)]
            pl = dict(name=name, route=r.get('other_way') or '', room='the Northern Plains', dir='here', path=[q], segs=[[q]],
                      group='af', where='off the Northern Plains', noroute=True, note=OTHER_WAY if r.get('other_way') else NO_ROUTE)
        w['places'].append(pl); placed.append((name, round(site[0], 1), round(site[1], 1)))
    return w, placed
