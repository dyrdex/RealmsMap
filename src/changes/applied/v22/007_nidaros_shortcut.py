"""Owner, Oct 19: the Nidaros Shortcut, placed in the Forest of Tears editor (save of 17:09Z): Forgotten Woods 5307 -> nw -> 5317 -> n -> 935 -> n ->
936 (Vale of Nidaros) -> sw -> spacer 5511 -> 5507 (Valley of Mysts) -> e -> Forgotten Woods 5510, far to the west: the 5511 -> 5507 step is one long
line, like the Ofcol Shortcut. Every route through it (Valley of Mysts, The Tower of Zenothir, Angel's Landing) is joined at the shortcut: its
line runs on unbroken from 5307 through these rooms to 5510 and on. Valley of Mysts also gets the unbroken line up to 5307 the other two have
(the same rooms; its own line had an old break by the Northern Trade Route's entrance). Markers stay. The rooms' spots go into the room
positions the route tracer uses; nothing else is drawn."""
import math
import maplib

SAVE = {5317: (38.16, -63.82), 935: (38.16, -64.82), 936: (38.16, -65.82), 5511: (37.16, -64.82), 5507: (-37.6, -66.37)}
A, B = 5307, 5510                                                    # where the shortcut leaves the Woods (east) and comes back (west)
GAP = "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
R = lambda q: [round(q[0], 3), round(q[1], 3)]


def apply(town, wild, pos):
    for v, q in SAVE.items(): pos[str(v)] = list(q)
    walk, at = maplib.tracer(pos, wild)
    pa, pb = at(A), at(B)
    mid = [R(SAVE[v]) for v in (5317, 935, 936, 5511, 5507)]
    users = [p for p in wild['places'] if p.get('route') and 936 in walk(p['route'])]
    # the unbroken line from Darkhaven Square to 5307, from a route whose first piece already runs there
    lead = next(s[:[math.dist(q, pa) < .02 for q in s].index(True) + 1] for p in users for s in p['segs'][:1] if s[0] == [0, 0] and any(math.dist(q, pa) < .02 for q in s))
    rep = []
    for p in users:
        tr = walk(p['route']); i = tr.index(936)
        assert tr[i - 3:i + 1] == [A, 5317, 935, 936] and 5507 in tr[i:i + 4], (p['name'], tr[i - 3:i + 4])
        flat = [q for s in p['segs'] for q in s]
        j = next(k for k, q in enumerate(flat) if math.dist(q, pb) < .02)            # the line picks up again at 5510 ...
        rest = []; k0 = 0                                                             # ... and runs on in the piece(s) that start there
        for s in p['segs']:
            if k0 + len(s) > j: rest.append(s[j - k0:] if k0 <= j else s)
            k0 += len(s)
        segs = [lead + mid + rest[0]] + rest[1:]
        before = len(p['segs']); p['segs'] = segs; p['path'] = [q for s in segs for q in s]
        n = (p.get('note') or '').replace(GAP, '').strip(); p['note'] = (n + (' ' if n else '') + GAP) if len(segs) > 1 else (n or None)
        rep.append((p['name'], before, len(segs)))
    return {'routes joined (pieces before, after)': rep}
