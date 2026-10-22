# Morte's Peak (owner, Oct 23): its height shading (the first 7 levels of wild.olhill) is removed; Death's Spire's levels stay.
from shapely.geometry import Polygon


def apply(town, wild, pos):
    L = wild['olhill']['levels']
    morte = lambda l: all(Polygon(r).centroid.y < 214 for r in l['rings'] if len(r) > 2)       # Morte's Peak y 183-212, Death's Spire ~220
    keep = [l for l in L if not morte(l)]
    wild['olhill']['levels'] = keep
    return {"Morte's Peak shading removed (levels, rings; levels left)": (len(L) - len(keep), sum(len(l['rings']) for l in L if morte(l)), len(keep))}
