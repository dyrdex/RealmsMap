"""Owner, Oct 23: the squiggle by Walking amongst the rushes 4316. Its nw exit runs through the connecting rooms 22557 and 14314 to Rocky
Coastline 4317, but the Northern Plains saves (Oct 19; Oct 23 05:18Z) put those two west of / north of 4317, so routes went past it and
doubled back (4317 is not in that editor, so it could not be lined up there). Fixed at the owner's request: the two rooms evenly spaced on
the straight line from 4316 to 4317. Every route line through their old spots (location cards) follows them; no trail is drawn through them."""

ROOMS = ('22557', '14314')                           # in order from 4316 to 4317


def apply(town, wild, pos):
    a, b = pos['4316'], pos['4317']
    old = {r: tuple(pos[r][:2]) for r in ROOMS}
    new = {r: [round(a[0] + (b[0] - a[0]) * (i + 1) / 3, 2), round(a[1] + (b[1] - a[1]) * (i + 1) / 3, 2)] for i, r in enumerate(ROOMS)}
    n = [0]
    def fix(o):
        if isinstance(o, list):
            if len(o) >= 2 and all(isinstance(v, (int, float)) for v in o[:2]):
                for r, q in old.items():
                    if abs(o[0] - q[0]) < 0.006 and abs(o[1] - q[1]) < 0.006: o[0], o[1] = new[r]; n[0] += 1
                return
            for x in o: fix(x)
        elif isinstance(o, dict):
            for x in o.values(): fix(x)
    fix(wild['places'])
    for r in ROOMS: pos[r][:2] = new[r]
    return {'rooms was -> now': {r: (old[r], new[r]) for r in ROOMS}, 'route points moved': n[0]}
