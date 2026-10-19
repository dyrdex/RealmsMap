"""Route options (owner, Oct 15): places the owner gives more than one route to. Every route is the owner's own (data.ROUTE_OPTIONS), with the
owner's direction word, room count and note; nothing here is worked out from the map except the traced line. The default route becomes the
place's route (the one drawn when the place is picked); the others are listed under 'Alternate routes' on its card and can be picked instead.
A route is kept only if it is traced to the place's marker (same start and end room as the default); otherwise it is reported and left off."""
import math
from route_fix import make_tracer, GAP_SENTENCE, OFCOL


def parse(text):
    out = {}
    for line in (text or '').strip().splitlines():
        if not line.strip() or line.lstrip().startswith('#!'): continue
        name, kind, dir_, rooms, note, route = [x.strip() for x in line.split('|', 5)]
        assert kind in ('default', 'alt'), line
        out.setdefault(name, []).append(dict(default=kind == 'default', dir=dir_, rooms=int(rooms), note=note or None, route=route.rstrip(';')))
    for name, opts in out.items():
        assert sum(o['default'] for o in opts) == 1, f'{name}: exactly one default route needed'
        opts.sort(key=lambda o: not o['default'])                               # the default first, then the alternates in the owner's order
    return out


def add_route_options(w, layouts, text):
    rooms, walk, at = make_tracer(w, layouts)
    wanted = parse(text)
    report = dict(places=[], dropped=[], missing=[n for n in wanted if not any(p['name'] == n for p in w['places'])])
    for p in w['places']:
        opts = wanted.get(p['name'])
        if not opts: continue
        end = p['path'][-1]; kept = []
        tail = []
        if len(p['path']) > 1 and not any(math.dist(q, end) < 0.02 for q in p['path'][:-1]):   # a marker set off its room (an OFFSET): trace to the room, then on to the marker
            tail = [end]; end = p['path'][-2]
        for o in opts:
            if o['route'].startswith(OFCOL): report['dropped'].append((p['name'], o['dir'], 'Ofcol Shortcut not handled')); continue
            pts = []
            for v in walk(o['route']):
                q = at(v); pts.append([round(q[0], 3), round(q[1], 3)] if q else 0)
            idx = [i for i, q in enumerate(pts) if q and math.dist(q, end) < 0.02]; tl = tail
            if not idx and tail:                                                # (the marker is a room this route reaches itself: trace straight to it)
                idx = [i for i, q in enumerate(pts) if q and math.dist(q, tail[0]) < 0.02]; tl = []
            if not idx: report['dropped'].append((p['name'], o['dir'], 'does not reach the marker')); continue
            segs = []; cur = []
            for q in pts[:idx[-1] + 1]:
                if q == 0:
                    if cur: segs.append(cur); cur = []
                else: cur.append(q)
            if cur: segs.append(cur)
            if tl: segs[-1] = segs[-1] + tl
            kept.append(dict(o, segs=segs, gap=GAP_SENTENCE if len(segs) > 1 else None))
        if not kept or not kept[0]['default']:
            report['dropped'].append((p['name'], 'all', 'default route not traced')); continue
        d = kept[0]
        p['route'] = d['route']; p['segs'] = d['segs']; p['path'] = [q for s in d['segs'] for q in s]
        if p.get('note'): p['note'] = p['note'].replace(GAP_SENTENCE, '').strip() or None   # (the gap sentence goes with each route that has a gap)
        p['opts'] = [{k: v for k, v in o.items() if k != 'default'} for o in kept]
        report['places'].append((p['name'], [(o['dir'], o['rooms'], len(o['segs'])) for o in kept]))
    return w, report
