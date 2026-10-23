"""The map's frame (owner, Oct 23), which the sea (changes/009) fills:
  - Otherland's routes ran to within 5.4 rooms of its south edge and 3.4 of its east edge (an awkward jut against the edge): the south and
    east edges moved out to MARGIN rooms beyond the farthest room, so the sea holds all of Otherland with room to spare;
  - the sea too narrow east to west: the west and east edges moved out a further WIDEN rooms each. The north edge is unchanged."""
import math

MARGIN, WIDEN = 20, 60


def apply(town, wild, pos):
    x0, y0, x1, y1 = wild['bounds']
    mx = max(q[0] for q in pos.values()); my = max(q[1] for q in pos.values())
    wild['bounds'] = [x0 - WIDEN, y0, max(x1, math.ceil(mx + MARGIN)) + WIDEN, max(y1, math.ceil(my + MARGIN))]
    return {'frame was -> now': ([x0, y0, x1, y1], wild['bounds'])}
