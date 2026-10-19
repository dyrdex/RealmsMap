"""Two paths that tie Darkhaven's eastern gate (Darkpass) to the Ashen Forest, taken from the rooms in your TinTin map.

 1. The road east: Outside Darkpass (708, at 8,0) - Outside Darkpass (1229, at 9,0) - a spacer room (1342, at 10,0) -
    The Cross Roads on the Hilltop (1230, at 11,0). From the Cross Roads the road already runs on east (the fixed Darkhaven
    rooms 1236, 1239, 1240) and to the entrance of the Eastern Trade Route (1235).
 2. The path southeast: from the Cross Roads (1230, at 11,0) - spacer (2833, at 12,1) - An Abandoned Trail (1237, at 13,2) -
    Standing in the Dirt (1238, at 14,3) - spacer (20902, at 14,4) - Paths Diverge at the Edge of the Trees (2854, at 14,5),
    where the Ashen Forest's path (through the spacer rooms 20908, 20907, 20906 to forest room 2853) already begins.
"""
import math
import numpy as np
from scipy.spatial import cKDTree

EAST_ROAD = [(8.2, 0.0), (9.0, 0.0), (10.0, 0.0), (11.0, 0.0)]      # starts on the trail that runs round the town, just outside the gate
SOUTHEAST_PATH = [(11.0, 0.0), (12.0, 1.0), (13.0, 2.0), (14.0, 3.0), (14.0, 4.0), (14.0, 5.0)]


def add_darkhaven_paths(w):
    paths = [[list(p) for p in EAST_ROAD], [list(p) for p in SOUTHEAST_PATH]]
    w['fwtracks'] = list(w['fwtracks']) + paths                         # drawn like the other trails
    pts = []
    for ln in paths:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / 0.1)); pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    tree = cKDTree(np.array(pts)); cleared = {}
    for key in ('trees', 'tufts', 'hills', 'thorns'):                   # nothing grows on the paths
        keep = [q for q in w[key] if q[0] < 8.4 or tree.query([q[0], q[1]])[0] > 0.6]
        cleared[key] = len(w[key]) - len(keep); w[key] = keep
    return w, dict(paths=len(paths), points=[len(p) for p in paths], cleared=cleared)
