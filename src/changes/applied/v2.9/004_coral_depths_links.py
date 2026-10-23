"""Coral Depths (owner, Oct 23): the water routes linking its primary water path (669 - 6286 - 6287 - 12597 - 12598 - 12956 - 12982 - 12983 - 12984,
on into the Desert of Despair's, changes/002) to the land drawn as type C, as changes/003 did on the Desert of Despair east coast: 6286 - 6302,
6287 - 6303, 6287 - 6288, 12983 - 6292, 12984 - 6329 (the last drawn in one line with 12983 - 12984: split there, 12983 - 12984 stays B).
The primary path is untouched."""
import importlib.util, math, os

C3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '003_dd_east_coast_secondary.py')
LINKS = [(6286, 6302), (6287, 6303), (6287, 6288), (12983, 6292)]
SPLIT = (12983, 12984, 6329)                         # one line 12983 - (15029) - 12984 - 6329: up to 12984 B, the rest C


def apply(town, wild, pos):
    spec = importlib.util.spec_from_file_location('c3', C3); c3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c3)
    P = [tuple(v[:2]) for v in pos.values()]
    at = lambda v: tuple(pos[str(v)][:2])
    same = lambda q, v: math.dist(q[:2], at(v)) < 0.02
    ends = lambda l, a, b: (same(l[0], a) and same(l[-1], b)) or (same(l[0], b) and same(l[-1], a))
    F = wild['seawaysfaint']; out, gone = [], set()
    for a, b in LINKS:
        c = [i for i, l in enumerate(F) if len(l) > 1 and ends(l, a, b)]
        assert len(c) == 1, (a, b, c)
        gone.add(c[0]); out.append(c3._wave(c3._knots(F[c[0]], P)))
    a, m, b = SPLIT
    c = [i for i, l in enumerate(F) if len(l) > 1 and ends(l, a, b)]
    assert len(c) == 1, c
    l = F[c[0]]; l = l if same(l[0], a) else l[::-1]
    k = max(i for i, q in enumerate(l) if same(q, m))
    F[c[0]] = l[:k + 1]                                # 12983 ... 12984 (the curve's doubled room point kept at its end)
    out.append(c3._wave(c3._knots(l[k:], P)))
    wild['seawaysfaint'] = [l for i, l in enumerate(F) if i not in gone]
    wild['olharborways'].extend(out)
    return {'links to type C (lines, length)': (len(out), round(sum(math.dist(p, q) for l in out for p, q in zip(l, l[1:])), 1))}
