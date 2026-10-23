"""Owner, Oct 23: two stale breaks fixed.
  - Dobra: its line broke after Bleeding Wildflowers 4015 (traced before the Northern Trade Route rooms 752, 753, 754, 4082 were drawn); traced
    again over the drawn rooms, one line to its marker (unchanged). maplib.tracer stops at spacer 20886 (its 'ne' bends north), so spacer rooms
    are followed here by their one other exit.
  - Catobeplas: its two pieces joined across the Ofcol Shortcut (gate 1363 -> 5333), as on the other routes through Ofcol (changes/017 draws
    that as a jump).
Both lose the "areas that aren't drawn yet" note."""
import math, re
import maplib

R = lambda q: [round(q[0], 3), round(q[1], 3)]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    _, at = maplib.tracer(pos, wild)
    isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    def walk(route):
        v = 764; trail = [v]
        for tok in [x.strip() for x in route.split(';') if x.strip()]:
            m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
            for _ in range(n):
                nx = [e for e in exits.get(v, []) if e['name'] == dd]
                assert nx, (v, dd)
                prev, v = v, nx[0]['to']; trail.append(v)
                while isspacer(v):
                    c = [x['to'] for x in exits[v] if x['to'] != prev]
                    if len(c) != 1: break
                    prev, v = v, c[0]; trail.append(v)
        return trail
    rep = {}
    p = next(p for p in wild['places'] if p['name'] == 'Dobra')
    t = walk(p['route']); assert all(at(v) for v in t), [v for v in t if not at(v)]
    path = []
    for v in t:
        q = R(at(v))
        if not path or path[-1] != q: path.append(q)
    assert math.dist(path[-1], p['path'][-1]) < 0.02, (path[-1], p['path'][-1])          # (ends at its marker, as before)
    was = len(p['segs']); p.update(path=path, segs=[path], note=None)
    rep['Dobra (rooms, pieces was -> now)'] = (len(t) - 1, was, 1)
    p = next(p for p in wild['places'] if p['name'] == 'Catobeplas')
    a, b = R(at(1363)), R(at(5333)); S = p['segs']
    assert len(S) == 2 and math.dist(S[0][-1], a) < 0.02 and math.dist(S[1][0], b) < 0.02
    p['segs'] = [S[0] + S[1]]; p['path'] = p['segs'][0]; p['note'] = None
    rep['Catobeplas (pieces was -> now; points)'] = (2, 1, len(p['path']))
    return rep
