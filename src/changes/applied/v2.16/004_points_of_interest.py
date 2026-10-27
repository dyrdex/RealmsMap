"""Owner, Oct 27: the sidebar's Mobs section is now 'Points of Interest' (site_template): Sonoria, Camelot Reparations (was
'Karl - Camelot Reparations') and Jokaan's Repair Shop. The other mobs keep their markers and names on the map exactly as they were,
but only as drawings (`deco`): not clickable, no sidebar entry, no card."""
DECO = ['Dobra', 'Catobeplas', 'Vaellys el Notrune', 'The Kirre', 'Inishie', 'Kujrajgi', 'Jarl']


def apply(town, wild, pos):
    P = {p['name']: p for p in wild['places'] + town['places']}
    k = P.pop('Karl - Camelot Reparations'); k['key'] = k.get('key') or k['name']; k['name'] = 'Camelot Reparations'
    for n in DECO: P[n]['deco'] = True
    return {'renamed': 'Camelot Reparations', 'map-only mobs': len(DECO)}
