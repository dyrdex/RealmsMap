"""One-time step: follow your own directions (from Darkhaven Square) through your TinTin map to each area that opens off the Northern Plains,
and record the route and the Plains room where it steps into the area. Areas with no directions in your list (or whose directions don't
pass through the Plains) get the Plains room they open from. Writes np_marker_routes.json (the build then places the markers using the
rooms' positions in your layout). Same method as bp_marker_routes.py."""
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
NP = 'Northern Plains'
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
# (name on the map, the area in your TinTin map, the name in your list or None). Not included, waiting on the owner:
# Asgard Nexus (on the Peaks it was renamed Z'hyal) and World Housing (removed from the Peaks on request).
AREAS = [("Azure Sea", "Azure Sea", "Azure Sea"), ("Crystalmir Lake", "Crystalmir Lake", "Crystalmir Lake"),
         ("From the Stars", "From the Stars", "From The Stars"), ("Opallinoc", "Opallinoc", "Opallinoc (Half-Ogre)"),
         ("Temple of the Moon", "Temple of the Moon", "Temple of the Moon"), ("The Blood Sea", "The Blood Sea", None),
         ("The City of Iniquity", "The City of Iniquity", None), ("The Dunhill Demesnes", "The Dunhill Demesnes", "The Dunhill Demesnes"),
         ("The Island of Irrybis", "The Island of Irrybis", None), ("Town of Solace", "Town of Solace", "Town of Solace"),
         ("Unholy Grounds", "Unholy Grounds", "Unholy Grounds"), ("Valley of the Elves", "Valley of the Elves", "Valley of the Elves")]
def doors(area):                                            # Plains rooms that open into the area (directly, or through a string of spacer rooms)
    out = set()
    for v in rooms:
        if rooms[v]['area'] != NP: continue
        for e in exits.get(v, []):
            t = e['to']; seen = {v}; k = 0
            while t in rooms and isspacer(t) and k < 30:
                seen.add(t); nx = [x['to'] for x in exits.get(t, []) if x['to'] not in seen]
                if not nx: break
                t = nx[0]; k += 1
            if t in rooms and rooms[t]['area'] == area: out.add(v)
    return sorted(out)
out = []
for name, area, listed in AREAS:
    d = doors(area); rec = dict(name=name, area=area, doors=d, route=None, trail=[], door=d[0] if d else None, ok=False)
    if listed:
        route = user.get(listed) or next(r for k, r in user.items() if k.startswith(listed.split(' (')[0])); trail, fail = walk(route)
        np_in = [i for i, v in enumerate(trail) if rooms[v]['area'] == NP]
        ends = rooms[trail[-1]]['area']
        last = trail[np_in[-1]] if np_in else None
        print(f"{name}: route {'ok' if not fail else 'FAILED at ' + str(fail)} | ends in '{ends}' | last Plains room {last} (doors {d})")
        if np_in: rec.update(route=route, trail=[[v, rooms[v]['area']] for v in trail[:np_in[-1] + 1]], door=last, ok=not fail and ends == area)
        else: rec.update(other_way=route)               # the directions reach the area without crossing the Plains
    else:
        print(f"{name}: no directions in your list | doors {d}")
    out.append(rec)
json.dump(out, open('np_marker_routes.json', 'w'), separators=(',', ':'))
