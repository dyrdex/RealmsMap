"""Markers for the areas that open off the Ashen Forest and the Eastern Trade Route (or are reached through them).
Each sits at the room where your own directions step out into the area (recorded in af_marker_routes.json), at that room's position in
your layout, so it follows the layout if you rearrange it. The route line you see when you pick one follows your directions room by room,
and breaks wherever it passes through rooms that are not drawn."""

GAP_NOTE = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."


def add_af_markers(w, layout, routes):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    before = len(w['places'])
    w['places'] = [p for p in w['places'] if not (p['name'] == 'Moria' and p.get('group') == 'mid')]       # Moria has one entry on the map, the one off the Ashen Forest; the one at Miden'nir is retired
    retired = before - len(w['places'])
    placed = []; skipped = []
    for r in routes:
        if r['pin'] not in pos: skipped.append(r['name']); continue
        trail = r['trail']
        if r['pin'] in [q[0] for q in trail]:                      # the traced route stops at the room where it leaves the forest: the pin hangs from that room
            last = len(trail) - 1 - [q[0] for q in trail][::-1].index(r['pin']); trail = trail[:last + 1]
        segs = []; cur = []
        for v, area, static in trail:
            p = pos.get(v) or static                               # rooms of the new area from your layout; Darkhaven and the Grove where they are
            if p: cur.append([round(p[0], 3), round(p[1], 3)])
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        direction = r['dir']
        if r.get('pin_room'):                                      # a pin that hangs off a different room from the one the route passes (shared with another area)
            end = [round(pos[r['pin_room']][0], 3), round(pos[r['pin_room']][1], 3)]; segs.append([end])
        elif r.get('rel'):                                           # a marker set a little way from the room it hangs off (the pin is then exactly where it is drawn)
            x, y = pos[r['pin']]; end = [round(x + r['rel'][0], 3), round(y + r['rel'][1], 3)]; direction = 'here'
            if segs: segs[-1] = segs[-1] + [end]
            else: segs = [[end]]
        else:
            end = [round(pos[r['pin']][0], 3), round(pos[r['pin']][1], 3)]
        via = r.get('where') or ('off the Eastern Trade Route' if r['via'] == 'Eastern Trade Route' else 'off the Ashen Forest')
        w['places'].append(dict(name=r['name'], route=r['route'], room=r['room'] or 'a spacer room', dir=direction, path=[q for s in segs for q in s], segs=segs, group='af', where=via,
                                note=r.get('note') or (None if len(segs) == 1 else GAP_NOTE)))
        placed.append((r['name'], end, direction))
    return w, dict(placed=placed, skipped=skipped, retired_moria_markers=retired)
