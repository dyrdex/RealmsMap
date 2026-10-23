"""Owner, Oct 23: five mobs in Otherland (the Mobs list), each with two routes on its card: South (the default, drawn when picked) and North, in the
owner's words and room counts. The marker is on the mob's room ('found at'). Traced from Darkhaven Square over the drawn rooms; North's line breaks
before the hidden Blood Sea rooms 13072 / 15259 (no path up from 5967 / 5970; their spots come from 002), as the sub-area cards'.
Inishie's and Tirebaen's North directions as given start 'w;w;w', which stops on Horizon Road after 4 rooms; every other North route starts
'nw;w;w', and with that both reach their mob: used 'nw' (owner to confirm)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ROUTE_ONLY = {13072, 15259}
GAP = 'This route goes down into the Blood Sea in the far north and comes up among the icebergs off Otherland, so the drawn line breaks there.'
WHERE = {'Tirebaen': 'in the Frost Mansion (Asgard Nexus), in Otherland'}
MOBS = [
 ('The Kirre', 15673, [('South', 77, "s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;sw;sw;sw;s;s;sw;s;s;se;se;se;se;s;s;se;d;s;se;s;se;se;se;e;s;s;e;se;e;d;se;s;sw;e;s;sw;e;s;s;e;sw;e;u;u;w;sw;sw;sw;d;se;ne;u;e;d;d;n;d;d"),
                       ('North', 69, "nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;d;se;u;nw;w;w;w;d;d;w;u;nw;w;w;w;sw;sw;d;se;ne;u;e;d;d;n;d;d")]),
 ('Inishie', 13106, [('South', 86, "s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;sw;sw;sw;s;s;sw;s;s;se;se;se;se;s;s;se;d;s;se;s;se;se;se;e;s;s;e;se;e;d;se;s;sw;e;s;sw;e;s;s;sw;se;sw;w;se;sw;e;e;e;se;sw;d;d;w;w;sw;sw;w;s;sw;e;d;d;nw;nw;d;n;nw;sw;sw;sw"),
                     ('North', 78, "nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;n;n;n;d;nw;nw;w;u;ne;u;u;nw;w;d;nw;w;sw;d;w;nw;nw;sw;e;d;sw;w;nw;n;nw;nw;d;n;nw;sw;sw;sw")]),
 ('Tirebaen', 22250, [('South', 91, "s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;sw;sw;sw;s;s;sw;s;s;se;se;se;se;s;s;se;d;s;se;s;se;se;se;e;s;s;e;se;e;d;se;s;sw;e;s;sw;e;s;s;sw;se;w;s;w;se;sw;nw;nw;w;sw;sw;sw;d;se;ne;u;e;d;d;d;w;se;e;e;u;u;nw;sw;n;nw;sw;ne;s;n;nw;sw"),
                      ('North', 83, "nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;d;se;u;nw;w;w;w;d;d;w;u;nw;w;w;w;sw;sw;d;se;ne;u;e;d;d;d;w;se;e;e;u;u;nw;sw;n;nw;sw;ne;s;n;nw;sw")]),
 ('Kujrajgi', 15688, [('South', 87, "s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;sw;sw;sw;s;s;sw;s;s;se;se;se;se;s;s;se;d;s;se;s;se;se;se;e;s;s;e;se;e;d;se;s;sw;e;s;sw;e;s;s;sw;se;w;s;w;se;sw;nw;nw;w;sw;sw;sw;d;se;ne;u;e;d;d;w;sw;se;s;d;d;e;sw;se;ne;d;sw;d"),
                      ('North', 79, "nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;d;se;u;nw;w;w;w;d;d;w;u;nw;w;w;w;sw;sw;d;se;ne;u;e;d;d;w;sw;se;s;d;d;e;sw;se;ne;d;sw;d")]),
 ('Jarl', 17132, [('South', 74, "s;s;s;s;s;s;ne;s;s;se;e;e;s;sw;sw;s;e;e;u;e;e;e;s;s;s;se;e;e;e;s;se;se;s;sw;s;s;w;sw;s;s;s;s;s;s;s;s;s;s;e;e;se;se;e;se;se;se;u;w;w;u;w;w;d;sw;d;se;e;e;ne;u;w;nw;sw;d"),
                  ('North', 62, "nw;w;w;n;n;n;n;e;look painting;n;nw;n;n;nw;w;nw;nw;w;w;w;nw;nw;sw;sw;w;sw;w;nw;n;n;nw;ne;w;w;w;ne;nw;n;nw;w;nw;n;d;se;u;u;w;u;w;w;d;sw;d;se;e;e;ne;u;w;nw;sw;d")]),
]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    rep = {}
    for name, end, routes in MOBS:
        assert not any(p['name'] == name for p in wild['places']), name
        opts = []
        for d, n, raw in routes:
            route = maplib.condense(raw); t = walk(route)
            assert t[-1] == end and at(end), (name, d, t[-1])
            segs = [[]]
            for v in t:
                if v in ROUTE_ONLY and segs[-1]: segs.append([])
                if not at(v): continue
                q = R(at(v))
                if not segs[-1] or segs[-1][-1] != q: segs[-1].append(q)
            opts.append(dict(dir=d, rooms=n, note=None, route=route, segs=segs, gap=GAP if len(segs) > 1 else None))
        wild['places'].append(dict(name=name, route=opts[0]['route'], room=rooms[end]['name'], dir='here', path=opts[0]['segs'][0], segs=opts[0]['segs'],
                                   kind='mob', group='af', where=WHERE.get(name, 'in Otherland'), note=None, opts=opts, vnum=end))
        rep[name] = dict(room=(end, rooms[end]['name']), at=R(at(end)), options=[(o['dir'], o['rooms'], len(o['segs'])) for o in opts])
    return rep
