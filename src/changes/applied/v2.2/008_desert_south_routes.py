"""Owner, Oct 20: new directions for the south-going route (the default 'River: Safest Route' option) of Blasted Lands and the Great Eastern Desert.
Both run west of the old River route through the desert's north (6366-6369) to 9057; Blasted Lands' line runs on to its marker on 22145
('scan for entrance'), as before. The East option is unchanged. data.py's AREAS keep the East routes (the places' first directions)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
NEW = {
    'Blasted Lands': ('s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;s;w;nw;w;w;w;sw;w;w;sw;s;s;e;scan for entrance', 9057, 22145),
    'Great Eastern Desert': ('s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;s;w;nw;w;w;w;sw;w;w;sw;s;s;e', 9057, None),
}


def apply(town, wild, pos):
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, (raw, end, extra) in NEW.items():
        p = next(p for p in wild['places'] if p['name'] == name)
        o = next(o for o in p['opts'] if o['dir'] == 'River')
        assert p['route'] == o['route'], name                                       # (River is the default)
        route = maplib.condense(raw); t = walk(route)
        assert t[-1] == end and all(at(v) for v in t), (name, t[-1])
        seg = [R(at(v)) for v in t] + ([R(at(extra))] if extra else [])
        old = len(p['path'])
        p['route'] = o['route'] = route; p['path'] = seg; p['segs'] = o['segs'] = [seg]; p['note'] = None; o['gap'] = None
        if 'path' in o: o['path'] = seg
        rep[name] = dict(route=route, steps=len(t), points=(old, len(seg)), ends=seg[-1])
    return rep
