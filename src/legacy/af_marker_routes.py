"""One-time step: follow your own directions (from Darkhaven Square) through your TinTin map to each area that opens off the Ashen Forest
or the Eastern Trade Route (or is reached through them), and record the route and the room where it steps out. Writes af_marker_routes.json.
(The build then places the markers using the rooms' positions in your layout.)"""
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
AFSET = {v for v, r in rooms.items() if r['area'] in ('The Ashen Forest', 'Eastern Trade Route')}
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
# (name on the map, area the route ends in or passes into, the area's name in your list or None, your directions, extras)
FROM_LIST = [("King's Castle", "The King's Castle"), ("Mountains of Desolation", "Mountains of Desolation"), ("Shai'ghool", "Shai'Ghool"), ("Shadar Logoth", "Shadar Logoth"),
             ("Troll Den", "Troll Den"), ("Ocean Keep", "Ocean Keep"), ("Glimwinkle's Windmill", "Glimwinkle's Windmill"), ("White Pine Camp", "White Pine Camp")]
NEW = [
    ("Moria", "Moria", "#8 e;se;se;s;s", dict(where='off New Darkhaven', note="This pin marks where your directions from the east gate step into Moria, just south of the room where the southeast path from the gate ends.")),
    ("City of Eldestra", "City of Eldestra", "#13 e;ne;nw;w;ne;e;ne;#2 e;s;#2 e;s;se;e;s", {}),
    ("Land of the Fire Newts", "Moria", "#8 e;#2 se;#2 s;se;s;#4 e;#2 n;e;ne;#2 n;e", dict(pin=1255, pin_room=1255, dir='s', room='Within the Ashen Forest', where='through Moria', note="Your directions go on through Moria, which isn't drawn yet. One shared pin marks both this and Machine Dreams, at forest room 1255, whose south exit leads into Moria.")),
    ("Machine Dreams", "Machine Dreams", "#13 e;#3 s;w;s;w;w;n;w;w;s;s;se;e;e;ne;w;s;d", dict(pin=1255, pin_room=1255, dir='s', room='Within the Ashen Forest', where='through Moria', note="Your directions go on through Moria and the Land of the Fire Newts, which aren't drawn yet. One shared pin marks both this and the Land of the Fire Newts, at forest room 1255, whose south exit leads into Moria.")),
    ("Fire Station", "The Fire Station", "#8 e;#3 ne;#3 e;ne;se;e;ne;#3 se;ne;e;#2 ne;n;se", dict(rel=[0.686, 1.246], where='inside White Pine Camp', note="The Fire Station is inside White Pine Camp, so this pin sits just southeast of the White Pine Camp marker."))]
def to_entrance(route, goal=1235):
    # follow the directions step by step until they reach the entrance room, and write that part of them out in short form
    v = 764; steps = []
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
        for _ in range(n):
            e = [x for x in exits.get(v, []) if x['name'] == dd or x['cmd'].split(';')[-1] == dd or x['cmd'] == tok][0]
            v = e['to']; steps.append(dd); k = 0
            while isspacer(v) and k < 40:
                c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                if not c: break
                v = c[0]; k += 1
            if v == goal:
                out_ = []; i = 0
                while i < len(steps):
                    j = i
                    while j + 1 < len(steps) and steps[j + 1] == steps[i]: j += 1
                    out_.append(f"#{j - i + 1} {steps[i]}" if j > i else steps[i]); i = j + 1
                return ';'.join(out_)
    raise SystemExit('the directions never reach the entrance room')
out = []
def record(disp, area, route, extra):
    trail, fail = walk(route)
    assert fail is None, (disp, fail)
    assert any(rooms[v]['area'] == area for v in trail), f'{disp} never reaches {area}'
    inaf = [v for v in trail if v in AFSET]
    pin = inaf[-1] if inaf else next(v for v in reversed(trail) if v in ndpos or v in sgp)     # the last forest / trade-route room, or, if the route never uses one, the last Darkhaven room
    i_ = len(trail) - 1 - trail[::-1].index(pin)
    if i_ + 1 < len(trail): nxt = trail[i_ + 1]; pe = [e for e in exits[pin] if e['to'] == nxt][0]; code = pe['dir']
    else: code = 0
    pts = []
    for v in trail:
        p = ndpos.get(v) if v in ndpos else (sgp.get(v) if v in sgp else None)           # Darkhaven and Grove rooms are where they are on the map
        pts.append([v, rooms[v]['area'], list(p[:2]) if p else None])
    rec = dict(name=disp, route=route, pin=pin, room=rooms[pin]['name'], dir=DN[code], via='Eastern Trade Route' if rooms[pin]['area'] == 'Eastern Trade Route' else 'Ashen Forest', trail=pts)
    rec.update(extra); out.append(rec)
    print(f"{disp:24} pin {pin} '{rooms[pin]['name'][:30]}' [{rooms[pin]['area'][:10] or 'spacer'}] exit {DN[code]} | {len(trail)} rooms on the route")
EXTRA_FOR = {"King's Castle": dict(rel=[0.05, 0.95])}                     # set just southwest of where it was, right beside the junction at The King's Crossing
for disp, area in FROM_LIST: record(disp, area, user[disp], EXTRA_FOR.get(disp, {}))
ENTRANCE_ROUTE = to_entrance(user['White Pine Camp'])
print('route to the entrance of the Eastern Trade Route:', ENTRANCE_ROUTE)
NEW.append(("Eastern Trade Route", "Eastern Trade Route", ENTRANCE_ROUTE, dict(pin=1235, where='off New Darkhaven', note="This marks the entrance to the Eastern Trade Route. The directions are the first part of your directions to White Pine Camp, which step onto the road here.")))
for disp, area, route, extra in NEW: record(disp, area, route, extra)
json.dump(out, open('af_marker_routes.json', 'w'), separators=(',', ':'))
