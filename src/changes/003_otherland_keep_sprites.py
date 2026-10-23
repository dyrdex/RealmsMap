"""Owner's Otherland save of Oct 23 (00:19Z; 5 rooms added round The Ziggurat, 19 Tundra Fields rooms moved), redrawn by the legacy build + rebase:
the plants, drifts and floes are scattered again in one random sequence over all of Otherland, so they all moved. Kept as they were (snapshot
`legacy/ol_keep_oct23.json`) everywhere except the area the save changed (ZONE: 1.5 round the moved/added rooms at old and new spots, the changed
trail stretches and the changed coast), where the new ones are used. Icebergs: the old ones, none added (dropped if now on land)."""
import json, os
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

LEG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'legacy')


def apply(town, wild, pos):
    K = json.load(open(os.path.join(LEG, 'ol_keep_oct23.json')))
    Z = Polygon(K['zone'], K['holes'])
    def at(x):
        while not isinstance(x[0], (int, float)): x = x[0]
        return Point(x[:2])
    rep = {}
    for name, cur, old in (('plants', wild['olflora'], K['olflora']), ('drifts', wild['olsnow']['drifts'], K['drifts']),
                           ('floes', wild['olsouth']['floes'], K['floes'])):
        keep = [x for x in old if not Z.contains(at(x))]; new = [x for x in cur if Z.contains(at(x))]
        cur[:] = keep + new
        rep[name + ' (kept, new in the area; old there dropped)'] = (len(keep), len(new), len(old) - len(keep))
    land = unary_union([Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2])
    bergs = [b for b in K['bergs'] if not Polygon(b[0]).buffer(0).intersects(land)]
    rep['icebergs (kept; dropped, now on land)'] = (len(bergs), len(K['bergs']) - len(bergs))
    wild['olharbor']['bergs'] = bergs
    return rep
