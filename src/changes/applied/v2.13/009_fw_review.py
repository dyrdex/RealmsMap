"""Owner, Oct 24: a full review of the Forgotten Woods' paths. The checks (trail ends on a room, a trail or a road; trails passing rooms that
aren't joined by exits; exits between drawn rooms with no trail; trails lying on other trails) found, apart from what 002b now fixes, trails
drawn twice: a second copy of the same exit lying on another trail (most since the old pipeline), which shows as a doubled or thicker line.
Those copies are removed: a trail is a copy if at least SHARE of it lies within GAP of a longer (or equal, then later) trail and both its
ends lie within END of that trail; only the Woods' trails (a Woods room within 0.4), at least MIN_LEN long (short spurs at junctions
are real links). Runs last (later change files never refer to trails by number)."""
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
import maplib

SHARE, GAP, END, MIN_LEN = 0.6, 0.2, 0.25, 0.5
AREA = 'The Forgotten Woods'


def apply(town, wild, pos):
    fw = wild['fwtracks']
    ids = [i for i, l in enumerate(fw) if len(l) > 1]
    G = {i: LineString([q[:2] for q in fw[i]]) for i in ids}; tree = STRtree([G[i] for i in ids])
    rooms, _ = maplib.world()
    woods = [Point(p[:2]) for k, p in pos.items() if int(k) in rooms and rooms[int(k)]['area'] == AREA]
    WT = STRtree(woods)
    drop = {}
    for i in ids:
        s = G[i]
        if s.length < MIN_LEN or not any(s.distance(woods[k]) < 0.4 for k in WT.query(s.buffer(0.4))): continue
        for k in tree.query(s.buffer(GAP)):
            j = ids[k]
            if j == i or j in drop: continue
            l = G[j]
            if l.length < s.length or (l.length == s.length and j < i): continue
            if s.intersection(l.buffer(GAP)).length >= SHARE * s.length and max(l.distance(Point(s.coords[0])), l.distance(Point(s.coords[-1]))) <= END:
                drop[i] = (j, round(s.length, 2), round(max(l.distance(s.interpolate(t / 20, normalized=True)) for t in range(21)), 2)); break
    wild['fwtracks'] = [l for i, l in enumerate(fw) if i not in drop]
    return {'trails drawn twice, removed (trail: lies on, its length, max gap)': drop}
