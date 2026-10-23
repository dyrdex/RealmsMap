"""Owner, Oct 22: sub-area markers for Otherland, each with two routes on its card (owner, Oct 23): South (the default, drawn when picked) and North,
in the owner's words and room counts. Traced from Darkhaven Square; drawn over the drawn rooms (rooms not on the map skipped), the marker where the
route leaves the drawn rooms (gotcha 3; both routes leave at the same room). North goes down into the Blood Sea in the far north and comes up off
Otherland: its line is drawn in two pieces, broken there (as Dobra's).
Owner, Oct 23 (save 00:19Z): the hidden Blood Sea rooms 13072 and 15259 get their saved spots for the route tracer only (`track` cx..., never drawn);
the links down to them from 5967 / 5970 have no path, so the North line breaks just before them."""
import json, os
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
S0 = 's;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;se;se;s;sw;s;s;w;sw;s;s;s;s;s;s;s;s;s;s;e;e;se;se;'
N0 = 'nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;'
PLACES = {   # name: [(option, rooms (owner's count), directions)], the default first
    'Wild Tundra': [('South', 58, S0 + 'e;u;w;nw;s;d'), ('North', 52, N0 + 'd;se;e;nw;nw;u;w;nw;s;d')],
    'The Ziggurat': [('South', 58, S0 + 'w;nw;sw;w;s;s'), ('North', 53, N0 + 'd;se;e;nw;nw;u;w;nw;e;s;s')],
    'Valley of Crucifixion': [('South', 58, S0 + 'w;nw;sw;w;s;e'), ('North', 53, N0 + 'd;se;e;nw;nw;u;w;nw;e;s;e')],
    'Cursed Lands': [('South', 71, S0 + 'e;se;se;se;se;sw;sw;sw;sw;sw;sw;w;w;nw;nw;ne;e;nw;n'), ('North', 52, N0 + 'n;n;n;d;nw;nw;ne;e;nw;n')],
}
ROUTE_ONLY = [13072, 15259]                                                           # (hidden in the editor; the line breaks before them)
AT = {}
LEG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'legacy')
WHERE = 'off Otherland'
GAP = 'This route goes down into the Blood Sea in the far north and comes up among the icebergs off Otherland, so the drawn line breaks there.'


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    S = json.load(open(os.path.join(LEG, 'ol_layout_final.json'))); P = dict(zip(S['ids'], zip(S['xs'], S['ys'])))
    for v in ROUTE_ONLY:
        assert v in S['hidden'] and str(v) not in pos; wild['track']['cx%d' % v] = [P[v][0], P[v][1]]
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, routes in PLACES.items():
        assert not any(p['name'] == name for p in wild['places']), name
        opts, leave = [], set()
        for d, n, raw in routes:
            route = maplib.condense(raw); t = walk(route)
            assert len(t) > 1 and rooms[t[-1]]['area'] not in ('', 'Otherland'), (name, d, t[-1])   # (it reaches the sub-area itself)
            last = max(i for i, v in enumerate(t) if at(v))
            out = next(e['name'] for e in exits[t[last]] if e['to'] == t[last + 1]) if last + 1 < len(t) else 'here'
            segs = [[]]
            for v in t[:last + 1]:
                if v in ROUTE_ONLY and segs[-1]: segs.append([])
                if not at(v): continue
                q = R(at(v))
                if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
            opts.append(dict(dir=d, rooms=n, note=None, route=route, segs=segs, gap=GAP if len(segs) > 1 else None))
            leave.add((t[last], out)); end = t[-1]
        assert len(leave) == 1, (name, leave)                                            # (both leave the map at the same room)
        (v, out), = leave
        p = dict(name=name, route=opts[0]['route'], room=rooms[v]['name'], dir=out, path=opts[0]['segs'][0], segs=opts[0]['segs'], group='af',
                 where=WHERE, note=None, opts=opts)
        if name in AT: p['at'] = list(AT[name])
        wild['places'].append(p)
        rep[name] = dict(leaves_map_at=(v, out), marker=p.get('at') or p['path'][-1], options=[(o['dir'], o['rooms'], len(o['segs'])) for o in opts])
    return rep
