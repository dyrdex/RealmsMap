"""Owner, Oct 26: deities. No pin on the map for a deity; the site shows its locations (purple markers, template-free: site_template
DEITY) only while the deity is selected, and its card lists them; picking one draws its route. Each location: who (the deity itself, or
its Naos), the sub-area it is in, the owner's directions (numbered form, never edited).
A line is traced from Darkhaven Square over the drawn rooms: when it passes the sub-area's marker (within 1.0) it stops there and ends on
that marker; otherwise it stops at the last drawn room on the way (as changes v2.14/001). Its location marker is the line's end.
V'laresch keeps its one location (its old route and line) until the owner gives its list."""
import math
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
DEITIES = {
    "A'enari": [   # (who, sub-area, owner's directions)
        ('deity', 'Pixie Forest', '#8 e;ne;ne;ne;#3 e;ne;e;ne;#2 e;#5 n;sw;nw;w;#4 n;enter;ne;w'),
        ('deity', "King's Castle", '#8 e;se;se;s;se;se;se;se;ne;ne;e;ne;ne;e;#2 s;sw;s;se;s;se;#2 e;ne;ne;e;open nw;nw;w;ne;w'),
        ('naos', 'Emerald Hills', '#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;#3 ne;#5 e;ne;e;n;ne;'),
        ('naos', 'Town of Solace', 'nw;#2 w;#4 n;e;look painting;open n;n;nw;#2 n;nw;w;nw;nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#4 n;#4 e;n'),
    ],
}


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    P = {p['name']: p for p in wild['places']}
    def end_of(p):                                                   # a place's marker spot (as the template places it)
        return tuple(p['at']) if p.get('at') else tuple(p['path'][-1])
    rep = {}
    for name, locs in DEITIES.items():
        p = P[name]; opts = []
        for who, sub, raw in locs:
            route = maplib.condense(raw); t = walk(route); m = end_of(P[sub])
            near = [(math.dist(at(v), m), i) for i, v in enumerate(t) if at(v)]
            d, i = min(near)
            cut = i if d <= 1.0 else max(i for i, v in enumerate(t) if at(v))
            path = []
            for v in t[:cut + 1]:
                if at(v) and (not path or path[-1] != R(at(v))): path.append(R(at(v)))
            if d <= 1.0 and path[-1] != R(m): path.append(R(m))
            gap = None if cut == len(t) - 1 else \
                f"The rest of the way isn't mapped yet, so the drawn line stops at the {sub} marker." if d <= 1.0 else \
                f"The rest of the way isn't mapped yet, so the drawn line stops at {rooms[t[cut]]['name']}."
            opts.append(dict(dir=('Naos' if who == 'naos' else name) + ' · ' + sub, who=who, sub=sub, route=route, segs=[path], at=path[-1], gap=gap))
            rep[f'{name} / {sub}'] = {'walked': len(t) - 1, 'ends at': (t[-1], rooms[t[-1]]['name']), 'line stops at': (t[cut], rooms[t[cut]]['name']),
                                      'on the sub-area marker': d <= 1.0, 'marker': path[-1], 'drawn points': len(path)}
        p.update(route=opts[0]['route'], segs=opts[0]['segs'], path=opts[0]['segs'][0], opts=opts, deity=True, nopin=True, note=None)
        p.pop('at', None)
    p = P["V'laresch"]                                               # one location for now: its old route and line, marker at the old pin
    m = R(p['segs'][-1][-1])
    p.update(opts=[dict(dir="V'laresch · Forest of Tears", who='deity', sub='Forest of Tears', route=p['route'], segs=p['segs'], at=m,
                        gap="The rest of the way (inside the Asgard Nexus) isn't mapped yet, so the drawn line stops where it opens off the Forest of Tears.")],
             deity=True, nopin=True, note=None)
    rep["V'laresch"] = {'locations': 1, 'marker': m}
    return rep
