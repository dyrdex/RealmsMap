# Rooms the Coral Depths editor owns (owner, Oct 23: "when I save this editor ... those rooms are in the exact same positions that they are in
# the Coral Depths editor"): 3245, 14360 become fixed rooms in the Ashen Forest editor (diamond, labelled CD, can't be moved), at their spots in
# the Coral Depths save (src/legacy/cd_layout_final.json); a saved layout no longer moves fixed rooms when it loads.
#   python3 fix_cd_rooms.py      (run from anywhere; edits ashen_forest_editor.html beside it)
import os, json, re
here = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.normpath(os.path.join(here, '..', '..', 'src'))
CD_ROOMS = [3245, 14360]
F = os.path.join(here, 'ashen_forest_editor.html'); h = open(F, encoding='utf-8').read()
m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1)); byid = {r['id']: r for r in D['rooms']}
C = json.load(open(os.path.join(SRC, 'legacy', 'cd_layout_final.json'))); cpos = dict(zip(C['ids'], zip(C['xs'], C['ys'])))
for v in CD_ROOMS:
    r = byid[v]; assert not r.get('fixed'), 'already fixed'
    x, y = cpos[v]; r.update(x=x, y=y, x0=x, y0=y, fixed=True, src='CD'); r['name'] = r['name'] or 'spacer room'
    print(v, 'fixed at', (x, y))
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
def sub(a, b):
    global h
    assert h.count(a) == 1, a; h = h.replace(a, b)
sub("if(pos.has(id))list.push([id,[o.xs[i],o.ys[i]]])", "if(pos.has(id)&&!byId.get(id).fixed)list.push([id,[o.xs[i],o.ys[i]]])")
sub("Fixed room on the finished map (DH, Grove, FW). Cannot be moved.", "Fixed room on the finished map (DH, Grove, FW; CD: placed in the Coral Depths editor). Cannot be moved.")
open(F, 'w', encoding='utf-8').write(h)
