"""Owner, Oct 25: the Ashen Forest editor save of Oct 25 04:58Z (`legacy/ash_layout_oct25.json`): Moria 3347, 3348 and the Land of the Fire
Newts 3352-3360 (tools/ashen_forest_editor/add_moria.py), all shown, where the owner put them; one trail along their exits from Within the
Ashen Forest 1255 (1255 s 3347 e 3348 s 3352 ... 3359 s 3360), Woods-style like the forest's. The save moved no other room.
Runs before 005, so the Moria routes are traced over these rooms."""
import json, math, os, maplib

CHAIN = [1255, 3347, 3348, 3352, 3353, 3354, 3355, 3356, 3357, 3358, 3359, 3360]


def line(a, b, step=0.32):
    n = max(1, round(math.dist(a, b) / step))
    return [[round(a[0] + (b[0] - a[0]) * i / n, 2), round(a[1] + (b[1] - a[1]) * i / n, 2)] for i in range(n + 1)]


def apply(town, wild, pos):
    o = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'legacy', 'ash_layout_oct25.json')))
    sv = dict(zip(o['ids'], zip(o['xs'], o['ys'])))
    assert math.dist(sv[1255], pos['1255']) < 1e-6
    for v in CHAIN[1:]:
        assert str(v) not in pos and v not in o['hidden'], v
        pos[str(v)] = [round(c, 3) for c in sv[v]]
    rooms, exits = maplib.world()
    for a, b in zip(CHAIN, CHAIN[1:]): assert any(e['to'] == b for e in exits[a]), (a, b)
    tr = []
    for a, b in zip(CHAIN, CHAIN[1:]):
        seg = line(pos[str(a)], pos[str(b)]); tr += seg[1:] if tr else seg
    wild['fwtracks'].append(tr)
    return {'rooms placed': len(CHAIN) - 1, 'trail points': len(tr), 'spots': {v: pos[str(v)] for v in CHAIN[1:]}}
