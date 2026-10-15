"""Small hand edits the owner asked for on the finished map (Oct 14), applied after every merge has run: lines taken out, places taken out.
Everything here is listed by what it is (endpoints, names), so a rebuild gives the same result and nothing else is touched."""
import math

DROP_LINES = {                                   # (layer, one end, the other end): a polyline with these two ends (either way round) is not drawn
    # the paths near Shattered Refuge (owner, Oct 14): the trail from the Intrigues of the Miden'nir cabins to it and its short continuation. (The trail from the south-west, rooms 587-590, was dropped here at first and put back: it is a real path.)
    ('swtracks', (-9.0, 17.0), (-3.0, 21.0)),
    ('swtracks', (-3.0, 21.0), (-1.2, 20.6)),
}
DROP_LINES |= {('fwtracks', (-11.05, 76.59), (-12.62, 75.77))}   # the up/down link from the bridge to the river room below it (Edel bridge, owner, Oct 14): the stream is drawn instead
BRIDGE_TRIM = ((-11.16, 74.16), 76.9, -11.0)       # the trail from Edel's south gate south: its stretch under the gate road and the stone bridge (to y 76.9) is not drawn as a trail
OWNER_PATHS = [                                   # paths the owner describes instead of mapping (Oct 14): room 3422 (Miden'nir, Stuck in the Brambles) to the Moria marker, round the east side of the Mountains of Desolation
    ('fwtracks', [[11.0, 16.0], [12.6, 16.0], [14.3, 16.1], [15.5, 16.7], [16.3, 15.7], [16.2, 13.2], [15.8, 10.6], [15.4, 8.7], [14.9, 7.2], [14.0, 5.62]]),
]
FILL_HOLES = [(12.3, 8.8, 17.8, 18.0)]            # a gap in the land (no ground, no coast) under the 3422-to-Moria path (owner, Oct 15): its land polygon (a hole) is removed so the ground fills in
OWNER_TAGS = [[7.94, 43.55, 'Elemental Canyon', 0.5]]       # a plain text label on the map (not a marker), just north of room 172 (owner, Oct 15)
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
    for layer_, pl_ in OWNER_PATHS: w[layer_] = list(w.get(layer_, [])) + [[list(q) for q in pl_]]; report['owner_paths'] = report.get('owner_paths', 0) + 1
    for hb in FILL_HOLES:                                                              # land polygons (holes) wholly inside a box
        keep_ = []
        for pl in w['geo']['land']:
            xs_ = [q[0] for q in pl]; ys_ = [q[1] for q in pl]
            if hb[0] <= min(xs_) and max(xs_) <= hb[2] and hb[1] <= min(ys_) and max(ys_) <= hb[3]:
                from matplotlib.path import Path as _P
                from smr_merge import _hash as _h
                pth_ = _P(pl); opath_ = [q for ln_ in w['fwtracks'] for q in ln_ if hb[0] - 1 <= q[0] <= hb[2] + 1 and hb[1] - 1 <= q[1] <= hb[3] + 1]
                near_ = [(t[0], t[1]) for t in w['trees'] if hb[0] - 2 <= t[0] <= hb[2] + 2 and hb[1] - 2 <= t[1] <= hb[3] + 2]
                add_ = []
                for gx_ in [hb[0] + 0.5 * i_ for i_ in range(int((hb[2] - hb[0]) / 0.5) + 1)]:         # a jittered grid, thinned to about one tree a room
                    for gy_ in [hb[1] + 0.5 * j_ for j_ in range(int((hb[3] - hb[1]) / 0.5) + 1)]:
                        x_ = round(gx_ + (float(_h(gx_, gy_, 5)) - .5) * .45, 3); y_ = round(gy_ + (float(_h(gx_, gy_, 6)) - .5) * .45, 3)
                        if float(_h(x_, y_, 7)) > 0.42 or not pth_.contains_point((x_, y_)): continue
                        if any(math.dist((x_, y_), q) < 0.9 for q in opath_) or any(math.dist((x_, y_), q) < 0.95 for q in near_ + [(a[0], a[1]) for a in add_]): continue
                        add_.append([x_, y_, round(0.85 + 0.3 * float(_h(x_, y_, 2)), 2), ['w', 'w', 'd'][int(float(_h(x_, y_, 4)) * 3)], int(float(_h(x_, y_, 3)) * 3)])
                w['trees'] = list(w['trees']) + add_; report['hole_trees'] = len(add_)
                report['hole_filled_sq'] = round(0.5 * abs(sum(xs_[i] * ys_[(i + 1) % len(pl)] - xs_[(i + 1) % len(pl)] * ys_[i] for i in range(len(pl)))), 1)
            else: keep_.append(pl)
        w['geo']['land'] = keep_
    w['tags'] = list(w['tags']) + [list(t_) for t_ in OWNER_TAGS]
    (sx_, sy_), ty_, tx_ = BRIDGE_TRIM
    for ln in w.get('fwtracks', []):
        if len(ln) > 3 and math.dist(ln[0], (sx_, sy_)) < 0.03:
            rest = [p for p in ln if p[1] >= ty_]; ln[:] = [[tx_, ty_]] + rest; report['bridge_trim'] = len(rest)
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
