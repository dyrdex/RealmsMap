"""Owner, Oct 25: new directions for Abishai's Morgue (they now end at Amid the Tombs of the Affluent 7809, then 'window'; all drawn:
the line runs the whole way, marker on 7809), a mausoleum drawing at -42.8, 7.5 (template SPRITE.mausoleum; 2.2 wide), and a small shack (the hut sprite) over room 1223."""
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]
ROUTE = 'w;w;w;w;w;w;w;w;w;sw;w;w;w;w;s;sw;w;w;s;s;se;s;window'   # (owner, Oct 25)
MAUSOLEUM = dict(k='mausoleum', at='xy', x=-42.8, y=7.5, w=2.2, h=2.0)   # (owner, Oct 25: much bigger; was 0.9 x 0.82)
SHACK = dict(k='hut', at='xy', x=-20.39, y=-34.75, w=0.8, h=0.69)        # a small shack over The Main Road of Loch Pyga 1223 (owner, Oct 25)


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
    wild['gfx'].append(dict(MAUSOLEUM)); wild['gfx'].append(dict(SHACK))
    return {"Abishai's Morgue": {'route': route, 'ends at': (t[-1], rooms[t[-1]]['name']), 'marker': path[-1], 'drawn points': len(path)}, 'mausoleum': MAUSOLEUM, 'shack': SHACK}
