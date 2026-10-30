"""Owner, Oct 30: Inishie's marker (Otherland, a map-only mob drawing) one room NE, at the end of the dock: from 13106 Afloat in the Harbor
of Ice to 13105, the room its routes pass just before (ne of 13106). Routes and lines unchanged; the marker is set by hand (`at`)."""

ROOM = '13105'


def apply(town, wild, pos):
    p = next(p for p in wild['places'] if p['name'] == 'Inishie')
    old = p.get('at') or p['path'][-1]
    p['at'] = [round(pos[ROOM][0], 3), round(pos[ROOM][1], 3)]
    return {'Inishie marker': (old, p['at'])}
