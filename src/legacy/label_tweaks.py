"""Positions of the two big area names."""
import numpy as np

def place_labels(w):
    # The Forgotten Woods: in the open forest just north of Dobra, clear of every trail, marker and maze
    L = w['fwlabel']; half = (L['x1'] - L['x0']) / 2
    cx, cy = 1.0, -48.0                         # where the name's middle sits (the arc rises about 0.7 above its y)
    w['fwlabel'] = dict(L, x0=round(cx - half, 2), x1=round(cx + half, 2), y=round(cy + 0.7, 2))
    # Forest of Tears: centred on the pines it names, and set in the same size as The Forgotten Woods
    F = w['label']
    if F.get('fixed'): return w, dict(woods=w['fwlabel'], forest=F)                 # set by the Forest of Tears merge (the middle of its field)
    pines = np.array([[t[0], t[1]] for t in w['trees'] if str(t[3]) == 'd' and F['x0'] + 4 < t[0] < F['x1'] - 4 and -20 < t[1] < 25])
    centre = float(np.median(pines[:, 1])) if len(pines) else F['y']
    w['label'] = dict(F, y=round(centre + 0.8, 2))
    return w, dict(woods=w['fwlabel'], forest=w['label'], pines_median_y=round(centre, 2))


def place_lake_label(w):
    """Lake Tich's name: smaller, set across the middle of the lake's wide part, with its marker just below it."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import partition as P
    if w['lakelabel'].get('fixed'): return w, w['lakelabel']                      # set by the Forest of Tears merge (across the new lake)
    water = P.inpolys(w['geo']['water'])
    cy = -29.0                                              # the middle of the lake's wide part (it is about 20 rooms across there)
    row = np.nonzero(water[int((cy - P.Y0) * P.RES)])[0] / P.RES + P.X0
    cx = float((row.min() + row.max()) / 2)
    w['lakelabel'] = dict(x=round(cx, 2), y=cy, a=-5.0, size=1.5, ls=0.28, drop=1.85)
    return w, w['lakelabel']
