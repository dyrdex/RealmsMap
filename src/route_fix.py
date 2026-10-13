"""Selected routes (owner, Oct 13): every place's route is traced again over the rooms of the final layouts, so a route that runs along a
trade route (the Northern, Western and Eastern Trade Routes, the Plains) is drawn along it without a break, and the Ofcol Shortcut is a portal.
The Ofcol Shortcut: the directions that start '#6 n;#3 nw;w;n;#4 e;s;w;sw' leave the map at Ofcol's gate (w), cross Ofcol's streets (n;#4 e;s;w, not drawn)
and the last 'sw' sets you down in the Forgotten Woods: the line runs from the gate straight to that Woods room and goes on, like the painting portal.
Markers do not move: a route is replaced only where the new trace ends at the marker and has fewer breaks."""
import re, math
import ashen_forest as AF

GAP_SENTENCE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
OFCOL = '#6 n;#3 nw;w;n;#4 e;s;w;sw'
DIRS = {'n', 'e', 's', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'}
PORTAL = {4222}


def fix_routes(w, layouts):
    rooms, exits = AF._world()
    isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    pos = {}
    for L in layouts:                                                           # earlier layouts win; hidden rooms still have their place on the line
        for v, x, y in zip(L['ids'], L['xs'], L['ys']): pos.setdefault(v, (x, y))
    track = w.get('track') or {}
    def at(v):
        if v in pos: return pos[v]
        t = track.get('cx' + str(v)); return tuple(t[:2]) if t else None
    def walk(route):
        v = 764; trail = [v]
        for tok in [x.strip() for x in route.split(';') if x.strip()]:
            tok = re.sub(r'^l ', 'look ', tok)
            m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
            for _ in range(n):
                nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
                if not nx and dd not in DIRS: break
                if not nx: return trail
                v = nx[0]['to']; trail.append(v); k = 0
                while isspacer(v) and k < 40:
                    c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                    if not c: break
                    v = c[0]; trail.append(v); k += 1
        return trail
    report = dict(retraced=0, joined=[], ofcol=[], kept=0, skipped=[])
    for p in w['places']:
        route = (p.get('route') or '').strip()
        if not route or p.get('noroute') or p['name'] == 'Along the Forest Path': continue
        route = route.rstrip(';')
        trail = walk(route)
        ofcol = route.startswith(OFCOL)
        if ofcol:                                                               # the streets of Ofcol (n;#4 e;s;w) are skipped: gate to the Woods room the 'sw' leads to
            skip_to = None
            for i, v in enumerate(trail):
                if rooms[v]['area'] in ('The Forgotten Woods',) and i > 8: skip_to = i; break
            skip = set(trail[[i for i, v in enumerate(trail) if rooms[v]['area'] == 'Shadow Grove'][-1] + 1:skip_to]) if skip_to else set()
        else: skip = set()
        end = p['path'][-1]
        pts = []
        for v in trail:
            q = at(v)
            pts.append(None if (q is None and (v in skip or v in PORTAL)) else ([round(q[0], 3), round(q[1], 3)] if q else 0))
        idx = [i for i, q in enumerate(pts) if q and math.dist(q, end) < 0.02]
        if not idx:                                                             # the marker sits off the trail (a site in the area): only the portal join is made
            if ofcol and skip_to:
                a = at(trail[skip_to - len(skip) - 1]); b = at(trail[skip_to])
                a = [round(a[0], 3), round(a[1], 3)]; b = [round(b[0], 3), round(b[1], 3)]
                ss = p['segs']
                for i in range(len(ss) - 1):
                    if math.dist(ss[i][-1], a) < 0.02 and math.dist(ss[i + 1][0], b) < 0.02:
                        ss[i:i + 2] = [ss[i] + ss[i + 1]]; p['path'] = [q for s_ in ss for q in s_]; report['ofcol'].append(p['name']); break
                if len(ss) == 1 and p.get('note'): p['note'] = p['note'].replace(GAP_SENTENCE, '').strip() or None
            else: report['skipped'].append(p['name'])
            continue
        pts = pts[:idx[-1] + 1]
        segs = []; cur = []
        for q in pts:
            if q is None: continue                                              # a portal / the streets of Ofcol: the line runs straight on
            if q == 0:
                if cur: segs.append(cur); cur = []
            else: cur.append(q)
        if cur: segs.append(cur)
        if not segs: continue
        if len(segs) < len(p['segs']):
            p['segs'] = segs; p['path'] = [q for s in segs for q in s]; report['retraced'] += 1
            if len(segs) == 1 and p.get('note'):
                n_ = p['note'].replace(GAP_SENTENCE, '').strip(); p['note'] = n_ or None
            report['joined'].append((p['name'], len(segs)))
            if ofcol: report['ofcol'].append(p['name'])
        else: report['kept'] += 1
    return w, report
