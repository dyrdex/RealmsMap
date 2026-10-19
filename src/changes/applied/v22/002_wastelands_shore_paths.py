"""Owner, Oct 19: in the Wastelands, the paths down to the coast's water route end exactly on it (one ran 0.36 past it, leaving a stub;
others stopped just short or ran a little past). Each path's end is moved along the path to where it meets the water route's line."""
import math

BOX = (-30, 60, 85, 140)                                           # (the Wastelands' south shore)


def _cross(a, b, c, d):                                            # where the line a->b (extended) meets the segment c-d: (t along a->b, point)
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a[:2], b[:2], c[:2], d[:2]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12: return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den; u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    return (t, (x1 + t * (x2 - x1), y1 + t * (y2 - y1))) if 0 <= u <= 1 else None


def apply(town, wild, pos):
    sea = [s for s in wild['seaways'] if all(BOX[0] < q[0] < BOX[1] and BOX[2] < q[1] < BOX[3] for q in s)]
    moved = []
    for L in wild['fwtracks']:
        if len(L) < 2 or not all(BOX[0] < q[0] < BOX[1] and BOX[2] < q[1] < BOX[3] for q in L): continue
        for end, prev in ((-1, -2), (0, 1)):
            a, b = L[prev], L[end]
            hits = [h for s in sea for c, d in zip(s, s[1:]) for h in [_cross(a, b, c, d)] if h and 0.5 < h[0] < 1.6]   # (the end's own stretch, give or take)
            if not hits: continue
            t, q = min(hits, key=lambda h: abs(h[0] - 1))
            if abs(t - 1) * math.dist(a, b) < 0.01: continue
            moved.append((round(b[0], 2), round(b[1], 2), round((t - 1) * math.dist(a, b), 2)))
            L[end] = [round(q[0], 3), round(q[1], 3)] + list(b[2:])
    return {'path ends moved onto the water route (x, y, change in length)': moved}
