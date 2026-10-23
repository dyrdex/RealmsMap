"""Owner, Oct 23: the "Azure Sea" location (marker in the far north on the Northern Plains' Walking amongst the rushes, and its card) removed."""


def apply(town, wild, pos):
    n = len(wild['places'])
    wild['places'] = [p for p in wild['places'] if p['name'] != 'Azure Sea']
    assert len(wild['places']) == n - 1
    return {'places was -> now': (n, len(wild['places']))}
