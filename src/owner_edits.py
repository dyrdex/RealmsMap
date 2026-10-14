"""Small hand edits the owner asked for on the finished map (Oct 14), applied after every merge has run: lines taken out, places taken out.
Everything here is listed by what it is (endpoints, names), so a rebuild gives the same result and nothing else is touched."""
import math

DROP_LINES = {                                   # (layer, one end, the other end): a polyline with these two ends (either way round) is not drawn
    # the paths near Shattered Refuge (owner, Oct 14): the trail from the Intrigues of the Miden'nir cabins to it and its short continuation. (The trail from the south-west, rooms 587-590, was dropped here at first and put back: it is a real path.)
    ('swtracks', (-9.0, 17.0), (-3.0, 21.0)),
    ('swtracks', (-3.0, 21.0), (-1.2, 20.6)),
}
DROP_PLACES = {'Southern Mountain Range'}        # the marker, its text and its sidebar entry (owner, Oct 14: "Southern Mountain Rage" is the owner's typo)


SLIDE_NORTH = -0.4                                # ... and 0.4 north, so the lowest cabin clears the 'Intrigues of the Miden'nir' label
SLIDE_EAST = 3.2                                  # the Shattered Refuge cabins and their little path move this far east (owner, Oct 14): east edge ~ 1 room west of its dot (-2.6, 21.0)
CABIN_BOX = (-10.5, 15.5, -6.5, 22.5)             # the cabins (nameless w.buildings) in this box
SLIDE_LINES = {('swtracks', (-9.0, 17.0), (-8.0, 21.04)), ('swtracks', (-8.0, 20.7), (-8.0, 21.04))}


def apply_edits(w):
    report = {'lines_dropped': [], 'places_dropped': [], 'slid_east': {}}
    for layer, a, b in sorted(DROP_LINES):
        keep = []
        for ln in w.get(layer, []):
            ends = (ln[0], ln[-1]) if len(ln) >= 2 else None
            hit = ends and ((math.dist(ends[0], a) < 0.03 and math.dist(ends[1], b) < 0.03) or (math.dist(ends[0], b) < 0.03 and math.dist(ends[1], a) < 0.03))
            if hit: report['lines_dropped'].append((layer, ln[0], ln[-1], len(ln)))
            else: keep.append(ln)
        w[layer] = keep
    moved = []                                    # the cabins and the little path between them, slid east
    for b in w['buildings']:
        if not b.get('name') and CABIN_BOX[0] <= b['x'] <= CABIN_BOX[2] and CABIN_BOX[1] <= b['y'] <= CABIN_BOX[3]: b['x'] = round(b['x'] + SLIDE_EAST, 3); b['y'] = round(b['y'] + SLIDE_NORTH, 3); moved.append((b['x'], b['y']))
    nl = 0
    for layer, a, b in sorted(SLIDE_LINES):
        for ln in w.get(layer, []):
            ends = (ln[0], ln[-1])
            if (math.dist(ends[0], a) < 0.03 and math.dist(ends[1], b) < 0.03) or (math.dist(ends[0], b) < 0.03 and math.dist(ends[1], a) < 0.03):
                for p in ln: p[0] = round(p[0] + SLIDE_EAST, 3); p[1] = round(p[1] + SLIDE_NORTH, 3)
                nl += 1; moved.append(('line', ln[0], ln[-1]))
    for key in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):          # nothing grows under them where they are now
        w[key] = [t for t in w[key] if not any(isinstance(m[0], float) and abs(t[0] - m[0]) < 0.9 and abs(t[1] - m[1]) < 0.7 for m in moved)]
    report['slid_east'] = {'cabins': len([m for m in moved if m[0] != 'line']), 'lines': nl}
    before = len(w['places']); names = [p['name'] for p in w['places'] if p['name'] in DROP_PLACES]
    w['places'] = [p for p in w['places'] if p['name'] not in DROP_PLACES]
    report['places_dropped'] = names
    return w, report
