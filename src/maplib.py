"""Helpers for changes made on top of the frozen map (base/map.json).
world()        the parsed world file (rooms, exits), parsed once per build, a fresh copy each call
tracer(pos, w) walk(route) -> the rooms the directions pass through from Darkhaven Square; at(room) -> its spot on the map (or None)
condense(r)    directions in numbered form: 'n;n;#2 n' -> '#4 n' (owner, Oct 18)
warp(x, y)     the standard water path's slight imperfect bend (owner, Oct 23): one smooth field for the whole map, Otherland's trail warp
warpline(l)    a water path's points (room to room, straight) -> the line in that bend, every 0.2 rooms; every water path but type C (olharborways)"""
import re, os, pickle, math, random

DIRS = {'n', 'e', 's', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'}
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = None


def world():
    global _WORLD
    if _WORLD is None:
        ns = {}; cwd = os.getcwd(); os.chdir(_HERE)
        try: exec(open('parse_world.py').read(), ns)
        finally: os.chdir(cwd)
        _WORLD = pickle.dumps((ns['rooms'], ns['exits']), protocol=pickle.HIGHEST_PROTOCOL)
    return pickle.loads(_WORLD)


def tracer(pos, wild=None):
    """pos: base['room_pos'] (room id as text -> [x, y]); wild: the map data, for the rooms only it places (its 'track')"""
    rooms, exits = world()
    isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    def at(v):
        q = pos.get(str(v)) or ((wild or {}).get('track') or {}).get('cx' + str(v)); return tuple(q[:2]) if q else None
    def walk(route):
        v = 764; trail = [v]
        for tok in [x.strip() for x in route.split(';') if x.strip()]:
            tok = re.sub(r'^l ', 'look ', tok)
            m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
            for _ in range(n):
                nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
                if not nx and dd not in DIRS: break
                if not nx: return trail
                v = nx[0]['to']; trail.append(v); k = 0
                while isspacer(v) and k < 40:
                    c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                    if not c: break
                    v = c[0]; trail.append(v); k += 1
        return trail
    return walk, at


def condense(route):
    out = []
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, d = (int(m.group(1)), m.group(2).strip()) if m else (1, tok)
        if d in DIRS and out and out[-1][1] == d: out[-1][0] += n
        else: out.append([n, d] if (d in DIRS or not m) else [1, tok])
    return ';'.join(f'#{n} {d}' if n > 1 else d for n, d in out)


WARP_A, WARP_L = 0.16, 7.0                          # applied/v2.4/001's TRACK_A, TRACK_L (Otherland's trails): this strong, this long
_ph = random.Random(13287); _A1, _A2, _A3, _A4 = (_ph.uniform(0, 2 * math.pi) for _ in range(4))   # (its phases)


def warp(x, y):
    return (x + WARP_A * (0.7 * math.sin(2 * math.pi * y / WARP_L + _A1) + 0.3 * math.sin(2 * math.pi * (x + y) / (WARP_L * 1.6) + _A3)),
            y + WARP_A * (0.7 * math.sin(2 * math.pi * x / WARP_L + _A2) + 0.3 * math.sin(2 * math.pi * (x - y) / (WARP_L * 1.6) + _A4)))


def warpline(line):
    pts = [tuple(line[0][:2])] + [tuple(q[:2]) for a, q in zip(line, line[1:]) if math.dist(a[:2], q[:2]) > 1e-6]
    if len(pts) == 1: return [[round(c, 3) for c in warp(*pts[0])]]
    out = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(2, int(math.dist((ax, ay), (bx, by)) / 0.2))
        out += [[round(c, 3) for c in warp(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)] for i in range(0 if not out else 1, n + 1)]
    return out
