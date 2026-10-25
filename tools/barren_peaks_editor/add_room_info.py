# Adds the exits to every room of the Barren Peaks + Forgotten Woods editor that has none (owner, Oct 23: the Woods,
# Darkhaven, Shadow Grove and Northern Trade Route rooms showed no connections), and makes the tooltip say "(fixed)" only for rooms that
# really are fixed (the Woods rooms are movable since Oct 19; their tooltip still said "fixed"):
#   python3 add_room_info.py   (edits barren_peaks_editor.html beside it)
import sys, os, json, re
here = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.normpath(os.path.join(here, '..', '..', 'src'))]
import maplib
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd'}
rooms, exits = maplib.world()
F = os.path.join(here, 'barren_peaks_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1)); inD = {r['id'] for r in D['rooms']}
n = 0; nt = 0
for r in D['rooms']:
    if r.get('ex') or r['id'] not in rooms: continue
    v = r['id']
    r['ex'] = [f"{DN.get(e['dir'], e['cmd'])} → {rooms[e['to']]['name'] or 'spacer room'}" + (f" ({rooms[e['to']]['area']})" if rooms[e['to']]['area'] and rooms[e['to']]['area'] != rooms[v]['area'] else '')
               + ('' if e['to'] in inD else ' · not in this editor') for e in exits.get(v, []) if e['to'] in rooms]
    n += 1
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
a = "[r.src]+' (fixed)'"; assert h.count(a) == 1
h = h.replace(a, "[r.src]+(r.fixed?' (fixed)':' (movable)')")
open(F, 'w', encoding='utf-8').write(h)
print('exits added to', n, 'rooms')   # (terrain left as it was: TinTin calls the Woods rooms 'City', which would recolour them)
