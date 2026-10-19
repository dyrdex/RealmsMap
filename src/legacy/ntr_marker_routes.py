"""One-time step: follow your own directions (from Darkhaven Square) through your TinTin map to the areas that open off the Northern Trade Route,
and record each route and the road room where it leaves the road. Writes ntr_marker_routes.json."""
import io, contextlib, json, re, sys
g = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('fot_extract.py').read(), g)
rooms, exits, ndpos, sgp = g['rooms'], g['exits'], g['ndpos'], g['sgp']
sys.path.insert(0, '.'); import data as DT
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: 'here'}
user = {}
for line in DT.AREAS.strip().split('\n'):
    if '|' in line: n, r = line.split('|', 1); user[n.strip()] = r.strip().rstrip(';')
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
NTR = {v for v, r in rooms.items() if r['area'] == 'Northern Trade Route'}
def walk(route):
    v = 764; trail = [v]
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
        for _ in range(n):
            nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
            if not nx: return trail, tok
            v = nx[0]['to']; trail.append(v); k = 0
            while isspacer(v) and k < 40:
                c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                if not c: break
                v = c[0]; trail.append(v); k += 1
    return trail, None
out = []
for name, area, road_room in (('City of Salburg', 'The City of Salburg', 4098), ('Keep of Belial', 'The Keep of Belial', 4104), ("The Wolf's Den", "The Wolf's Den", 4065)):
    route = user[name]; trail, fail = walk(route)
    seq = []
    for v in trail:
        a = rooms[v]['area'] or '·'
        if a != '·' and (not seq or seq[-1] != a): seq.append(a)
    inn = [v for v in trail if v in NTR]
    print(f"{name}: route {'ok' if not fail else 'FAILED at ' + str(fail)} | ends in '{rooms[trail[-1]]['area']}' | areas passed: {' > '.join(a[:18] for a in seq)}")
    print(f"   uses {len(inn)} road rooms; the last one is {inn[-1] if inn else None}; expected {road_room}")
    pts = []
    for v in trail:
        p = ndpos.get(v) if v in ndpos else (sgp.get(v) if v in sgp else None)
        pts.append([v, rooms[v]['area'], list(p[:2]) if p else None])
    out.append(dict(name=name, route=route, road_room=road_room, trail=pts, last_road=inn[-1] if inn else None, room=rooms[inn[-1]]['name'] if inn else ''))
json.dump(out, open('ntr_marker_routes.json', 'w'), separators=(',', ':'))
