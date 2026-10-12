"""One-time step: follow your own directions (from Darkhaven Square) through your TinTin map to each area that opens off the Barren Peaks,
and record the route and the Peaks room where it steps into the area. Areas with no directions in your list get the Peaks room they open
from. Writes bp_marker_routes.json (the build then places the markers using the rooms' positions in your layout)."""
import io, contextlib, json, re, sys
g = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('fot_extract.py').read(), g)
rooms, exits = g['rooms'], g['exits']
sys.path.insert(0, '.'); import data as DT
user = {}
for line in (DT.AREAS + '\n' + DT.HOMETOWNS + '\n' + DT.MORE_DIRECTIONS).strip().split('\n'):
    if '|' in line: n, r = line.split('|', 1); user[n.strip()] = r.strip().rstrip(';')
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
BP = 'Barren Peaks of Tahjliera'
DIRS = {'n', 'e', 's', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'}
def walk(route):
    v = 764; trail = [v]
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
        for _ in range(n):
            nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
            if not nx and dd not in DIRS: break                    # not a move (open a door, look at something, a note): carry on
            if not nx: return trail, tok
            v = nx[0]['to']; trail.append(v); k = 0
            while isspacer(v) and k < 40:
                c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                if not c: break
                v = c[0]; trail.append(v); k += 1
    return trail, None
# (name on the map, the area in your TinTin map, the name in your list or None)
AREAS = [("Reign of Madness", "Reign of Madness", "Reign of Madness"), ("Kingdom of Juargan", "Kingdom of Juargan", "Kingdom of Juargan"),
         ("Drow City", "Drow City", "Drow City"), ("Revelation City", "Revelation City", "Revelation City"),
         ("Qetag's Reach", "Qetag's Reach", "Qetag's Reach (Dwarf)"), ("Village of Tar'pa Cithm", "The Village of Tar'pa Cithm", "Village of Tar'pa Cithm"),
         ("Serpentine Coils", "Serpentine Coils", "Serpentine Coils"), ("The Crimson Caverns", "The Crimson Caverns", None),
         ("The Slime Pit", "The Slime Pit", "The Slime Pit"), ("World Housing", "World Housing", None),
         ("Mountain of Lost Souls", "The Mountain of Lost Souls", "Mountain of Lost Souls"), ("Barrik's Keep", "Barrik's Keep", "Barrik's Keep"),
         ("Asgard Nexus", "Asgard Nexus", None), ("Morgul Vale", "Morgul Vale", "Morgul Vale")]
ROUTES = {"The Crimson Caverns": "#6 n;#3 nw;w;n;#4 e;s;w;sw;s;sw;#2 s;#2 sw;#2 s;#2 ne;n;nw;w;#2 nw;w;#3 nw;#3 w;se;w;sw;w;u;nw;#3 w;#3 nw;#2 w;u;nw;w;n;d;#2 ne;#2 e;se;s;e"}   # owner's directions (Oct 10)
EXTRA = [("Tower of Enlightenment", "Tower of Enlightenment")]   # not off the Peaks: a marker in the Forgotten Woods (owner's request); the whole route is kept
def doors(area):                                            # Peaks rooms that open into the area
    out = set()
    for v, l in exits.items():
        for e in l:
            t = e['to']
            if t not in rooms: continue
            if rooms[v]['area'] == BP and rooms[t]['area'] == area: out.add(v)
            if rooms[t]['area'] == BP and rooms[v]['area'] == area: out.add(t)
    return sorted(out)
out = []
for name, area, listed in AREAS:
    d = doors(area); rec = dict(name=name, area=area, doors=d)
    if listed or name in ROUTES:
        route = ROUTES.get(name) or user.get(listed) or next(r for k, r in user.items() if k.startswith(listed.split(' (')[0])); trail, fail = walk(route)
        bp_in = [i for i, v in enumerate(trail) if rooms[v]['area'] == BP]
        ends = rooms[trail[-1]]['area']
        last = trail[bp_in[-1]] if bp_in else None
        print(f"{name}: route {'ok' if not fail else 'FAILED at ' + str(fail)} | ends in '{ends}' | last Peaks room {last} (doors {d})")
        rec.update(route=route, trail=[[v, rooms[v]['area']] for v in trail[:bp_in[-1] + 1]] if bp_in else [], door=last, ok=not fail and ends == area)
    else:
        print(f"{name}: no directions in your list | doors {d}")
        rec.update(route=None, trail=[], door=d[0] if d else None, ok=False)
    out.append(rec)
for name, listed in EXTRA:
    route = user[listed]; trail, fail = walk(route)
    print(f"{name}: route {'ok' if not fail else 'FAILED at ' + str(fail)} | ends in '{rooms[trail[-1]]['area']}' at {trail[-1]}")
    out.append(dict(name=name, area=None, doors=[], route=route, trail=[[v, rooms[v]['area']] for v in trail], door=None, ok=not fail))
json.dump(out, open('bp_marker_routes.json', 'w'), separators=(',', ':'))
