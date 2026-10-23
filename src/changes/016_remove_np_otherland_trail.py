"""Owner, Oct 23: the 'Otherland' watery trail north-west of the Northern Plains (gfx 'waterway' at -47.33, -202.02) and its small label removed.
(changes/013 copied it, mirrored, for 15606 first; that one stays.)"""


def apply(town, wild, pos):
    G, T = wild['gfx'], wild['tags']
    g = [i for i, g in enumerate(G) if g['k'] == 'waterway' and abs(g['x'] + 47.33) < 0.01 and abs(g['y'] + 202.02) < 0.01]
    t = [i for i, t in enumerate(T) if t[2] == 'Otherland' and abs(t[0] + 45.23) < 0.01 and abs(t[1] + 205.07) < 0.01]
    assert len(g) == 1 and len(t) == 1, (g, t)
    del G[g[0]]; del T[t[0]]
    return {'removed (sprite, label)': (1, 1)}
