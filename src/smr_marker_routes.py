"""One-time step (Southern Mountain Range + Southern Mountain Trade Route, Oct 14): follow your own directions (from Darkhaven Square) through your TinTin map to each area that opens off the range or its trade route,
and record the route and the Plains room where it steps into the area. Areas with no directions in your list (or whose directions don't
pass through the Plains) get the Plains room they open from. Writes smr_marker_routes.json (the build then places the markers using the
rooms' positions in your layout). Same method as np_marker_routes.py."""
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
SM = {'Southern Mountain Range', 'The Southern Mountain Trade Route'}
DIRS = {'n', 'e', 's', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'}
def walk(route):
    v = 764; trail = [v]
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        tok = re.sub(r'^l ', 'look ', tok)                 # 'l painting' = 'look painting'
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
# (name on the map, the area in your TinTin map, the name in your list or None). Left off: areas that already have a marker or are drawn (Azure Sea, Bartok Grove, Forest of Tears, Miden'nir, New Darkhaven, The Ashen Forest) and World Housing (owner, Oct 12).
AREAS = [("Desert of Despair", "Desert of Despair", "Desert of Despair"), ("Dragon's Pass", "Dragon's Pass", "Dragon's Pass"), ("Elemental Canyon", "Elemental Canyon", "Elemental Canyon"),
         ("Emerald Hills", "Emerald Hills", "Emerald Hills"), ("Lamech's Abandoned Manor", "Lamech's Abandoned Manor", "Lamech's Abandoned Manor"), ("MacMillan Family Farm", "MacMillan Family Farm", "MacMillan Family Farm"),
         ("Mithril Hall", "Mithril Hall", "Mithril Hall"), ("The Mire", "The Mire", "The Mire"), ("Seth's Fortress", "Seth's Fortress", "Seth's Fortress"),
         ("Steading of the Hill Giants", "Steading of the Hill Giants", "Steading of the Hill Giants"), ("The Castle of Rol Na Feinne", "The Castle of Rol Na Feinne", "The Castle of Rol Na Feinne"),
         ("The Ruins of T'man", "The Ruins of T'man", "The Ruins of T'man"),
         ("Old Pottswort's Fields", "Old Pottswort's Fields", "Old Pottswort's Fields"), ("Black Dagger Outlaws Hideout", "Black Dagger Outlaws Hideout", "Black Dagger Outlaws Hideout"),
         ("The Curse of Prosperity", "The Curse of Prosperity", "Curse of Prosperity"), ("Dawn to Dusk", "Dawn to Dusk", "Dawn to Dusk"), ("The Von Deusen Mausoleum", "The Von Deusen Mausoleum", "The Von Deusen Mausoleum"), ("The Wilds", "The Wilds", "The Wilds"),
         ("Transylvania", "Transylvania", "Transylvania"), ("Wastelands", "Wastelands", "Wastelands")]
def doors(area):                                            # Plains rooms that open into the area (directly, or through a string of spacer rooms)
    out = set()
    for v in rooms:
        if rooms[v]['area'] not in SM: continue
        for e in exits.get(v, []):
            t = e['to']; seen = {v}; k = 0
            while t in rooms and isspacer(t) and k < 30:
                seen.add(t); nx = [x['to'] for x in exits.get(t, []) if x['to'] not in seen]
                if not nx: break
                t = nx[0]; k += 1
            if t in rooms and rooms[t]['area'] == area: out.add(v)
    for v in rooms:                                         # (and rooms of the area whose exits lead into the range or its trade route)
        if rooms[v]['area'] != area: continue
        for e in exits.get(v, []):
            t = e['to']
            if t in rooms and rooms[t]['area'] in SM: out.add(t)
    return sorted(out)
out = []
for name, area, listed in AREAS:
    d = doors(area); rec = dict(name=name, area=area, doors=d, route=None, trail=[], door=d[0] if d else None, ok=False)
    if listed:
        route = user.get(listed) or next(r for k, r in user.items() if k.startswith(listed.split(' (')[0])); trail, fail = walk(route)
        np_in = [i for i, v in enumerate(trail) if rooms[v]['area'] in SM]
        ends = rooms[trail[-1]]['area']
        last = trail[np_in[-1]] if np_in else None
        print(f"{name}: route {'ok' if not fail else 'FAILED at ' + str(fail)} | ends in '{ends}' | last Plains room {last} (doors {d})")
        if np_in: rec.update(route=route, trail=[[v, rooms[v]['area']] for v in trail[:np_in[-1] + 1]], door=last, ok=not fail and ends == area)
        elif d and any(e['to'] in d for e in exits.get(trail[-1], [])):   # the directions end right beside the Plains room it opens from
            rec.update(route=route, trail=[[v, rooms[v]['area']] for v in trail], door=next(e['to'] for e in exits[trail[-1]] if e['to'] in d), ok=not fail and ends == area)
        else: rec.update(other_way=route)               # the directions reach the area without crossing the Plains
    else:
        print(f"{name}: no directions in your list | doors {d}")
    out.append(rec)
json.dump(out, open('smr_marker_routes.json', 'w'), separators=(',', ':'))
