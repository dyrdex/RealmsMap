"""Owner, Oct 23: two new locations, Otherland (Northern) and Otherland (Southern), in the owner's words (directions in numbered form), one route
each, traced from Darkhaven Square as applied/v2.8/002's sub-areas: drawn over the drawn rooms, the marker where the route leaves them (gotcha 3);
a route through the hidden Blood Sea rooms (13072, 15259: route-only spots) is drawn in pieces, broken there, and its card says so."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
PLACES = {
    'Otherland (Northern)': 's;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;se;se;s;sw;s;s;w;sw;s;s;s;s;s;s;s;s;s;s',
    'Otherland (Southern)': 'nw;#2 w;#4 n;e;look painting;n;nw;#2 n;nw;w;#2 nw;#3 w;#2 nw;#2 sw;w;sw;w;nw;#2 n;nw;ne;#3 w;ne;nw;n;nw;w;nw;#4 n;d;nw',   # (owner, Oct 23: ends after d;nw)
}
ROUTE_ONLY = {13072, 15259}
WHERE = 'off Otherland'
GAP = 'This route goes down into the Blood Sea in the far north and comes up among the icebergs off Otherland, so the drawn line breaks there.'


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, raw in PLACES.items():
        assert not any(p['name'] == name for p in wild['places']), name
        route = maplib.condense(raw); t = walk(route)
        assert len(t) > 1, name
        last = max(i for i, v in enumerate(t) if at(v))
        out = next(e['name'] for e in exits[t[last]] if e['to'] == t[last + 1]) if last + 1 < len(t) else 'here'
        segs = [[]]
        for v in t[:last + 1]:
            if v in ROUTE_ONLY and segs[-1]: segs.append([])
            if not at(v): continue
            q = R(at(v))
            if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
        segs = [s for s in segs if s]
        p = dict(name=name, route=route, room=rooms[t[last]]['name'], dir=out, path=segs[0], segs=segs, group='af', where=WHERE, note=None)
        if len(segs) > 1: p['note'] = GAP                        # (as Dobra's card)
        wild['places'].append(p)
        rep[name] = dict(rooms=len(t) - 1, ends=(t[-1], rooms[t[-1]]['name']), marker=(t[last], rooms[t[last]]['name'], out), pieces=len(segs))
    return rep
