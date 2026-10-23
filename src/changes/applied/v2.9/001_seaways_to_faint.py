"""All solid water routes (type A, 'seaways') drawn as the softer semi-transparent ones (type B, 'seawaysfaint'), map-wide (owner, Oct 23):
the lines move unchanged into seawaysfaint; seaways is left empty."""


def apply(town, wild, pos):
    moved = wild.get('seaways') or []
    wild.setdefault('seawaysfaint', []).extend(moved)
    wild['seaways'] = []
    return {'water routes A -> B (lines, points)': (len(moved), sum(len(l) for l in moved))}
