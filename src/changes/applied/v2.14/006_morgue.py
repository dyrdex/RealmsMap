"""Owner, Oct 25: new directions for Abishai's Morgue (they now end at Amid the Tombs of the Affluent 7809, then 'window'; all drawn:
the line runs the whole way, marker on 7809), a mausoleum drawing at -42.8, 7.5 (template SPRITE.mausoleum; 2.2 wide), and three small huts in a row over room 1223 (template SPRITE.lakehut)."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ROUTE = 'w;w;w;w;w;w;w;w;w;sw;w;w;w;w;s;sw;w;w;s;s;se;s;window'   # (owner, Oct 25)
MAUSOLEUM = dict(k='mausoleum', at='xy', x=-42.8, y=7.5, w=2.2, h=2.0)   # (owner, Oct 25: much bigger; was 0.9 x 0.82)
HUTS = [dict(k='lakehut', at='xy', x=round(-20.39 + dx, 2), y=-34.75, w=0.7, h=0.63, v=v) for v, dx in enumerate((-0.8, 0, 0.8))]   # three small huts in a row
                                                    # east-west over The Main Road of Loch Pyga 1223, the middle one on the room (owner, Oct 25; was one hut)


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    walk, at = maplib.tracer(pos, wild)
    p = next(p for p in wild['places'] if p['name'] == "Abishai's Morgue")
    route = maplib.condense(ROUTE); t = walk(route)
    assert all(at(v) for v in t), [v for v in t if not at(v)]
    path = []
    for v in t:
        if not path or path[-1] != R(at(v)): path.append(R(at(v)))
    p.update(route=route, path=path, segs=[path], room=rooms[t[-1]]['name'], note=None); p.pop('at', None)
    wild['gfx'].append(dict(MAUSOLEUM)); wild['gfx'].extend(dict(h) for h in HUTS)
    return {"Abishai's Morgue": {'route': route, 'ends at': (t[-1], rooms[t[-1]]['name']), 'marker': path[-1], 'drawn points': len(path)}, 'mausoleum': MAUSOLEUM, 'huts': HUTS}
