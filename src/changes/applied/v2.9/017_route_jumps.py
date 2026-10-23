"""Owner, Oct 23: the jumps in routes the owner names (portals / shortcuts) are drawn differently from the rest of a picked route: a thin
dashed arc (template / site JUMP) where the route line jumps between the two rooms, the rest as usual. ONLY these, as the owner decides; to add
one, add its two rooms here (the line's jump runs from the first room to the second)."""

JUMPS = [  # (name, room the jump starts at, room it lands at)
    ('look painting', 783, 4221),                     # Alms for the Poor (New Darkhaven) -> The Forest's Grasp (Northern Plains)
    ('Ofcol Shortcut', 1363, 5333),                   # The Shadow Grove (Ofcol's gate) -> A Sparse Trail (Forgotten Woods)
    ('Nidaros Shortcut', 5511, 5507),                 # (936 sw) 5511 -> A Bubbling Creek
    ("Dragon's Pass to the Mire", 8221, 8195),        # The Foot of Dragon's Pass -> A Path Amongst the Mire (The Mire (Central))
]


def apply(town, wild, pos):
    wild['jumps'] = [[round(pos[str(a)][0], 2), round(pos[str(a)][1], 2), round(pos[str(b)][0], 2), round(pos[str(b)][1], 2), n] for n, a, b in JUMPS]
    used = {n: 0 for n, _, _ in JUMPS}
    for p in wild['places']:
        for s in [p.get('segs') or [p['path']]] + [o['segs'] for o in p.get('opts') or []]:
            for seg in s:
                for q, r in zip(seg, seg[1:]):
                    for j in wild['jumps']:
                        if {(round(q[0], 2), round(q[1], 2)), (round(r[0], 2), round(r[1], 2))} == {(j[0], j[1]), (j[2], j[3])}: used[j[4]] += 1
    return {'jumps (route lines using each)': used}
