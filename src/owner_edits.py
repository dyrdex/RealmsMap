"""Small hand edits the owner asked for on the finished map (Oct 14), applied after every merge has run: lines taken out, places taken out.
Everything here is listed by what it is (endpoints, names), so a rebuild gives the same result and nothing else is touched."""
import math

DROP_LINES = {                                   # (layer, one end, the other end): a polyline with these two ends (either way round) is not drawn
    # the paths near Shattered Refuge (owner, Oct 14): the trail from the Intrigues of the Miden'nir cabins to it, its short continuation, and the trail that comes up to it from the south-west
    ('swtracks', (-9.0, 17.0), (-3.0, 21.0)),
    ('swtracks', (-3.0, 21.0), (-1.2, 20.6)),
    ('fwtracks', (-6.21, 26.66), (-1.81, 22.63)),
}
DROP_PLACES = {'Southern Mountain Range'}        # the marker, its text and its sidebar entry (owner, Oct 14: "Southern Mountain Rage" is the owner's typo)


def apply_edits(w):
    report = {'lines_dropped': [], 'places_dropped': []}
    for layer, a, b in sorted(DROP_LINES):
        keep = []
        for ln in w.get(layer, []):
            ends = (ln[0], ln[-1]) if len(ln) >= 2 else None
            hit = ends and ((math.dist(ends[0], a) < 0.03 and math.dist(ends[1], b) < 0.03) or (math.dist(ends[0], b) < 0.03 and math.dist(ends[1], a) < 0.03))
            if hit: report['lines_dropped'].append((layer, ln[0], ln[-1], len(ln)))
            else: keep.append(ln)
        w[layer] = keep
    before = len(w['places']); names = [p['name'] for p in w['places'] if p['name'] in DROP_PLACES]
    w['places'] = [p for p in w['places'] if p['name'] not in DROP_PLACES]
    report['places_dropped'] = names
    return w, report
