# python3 legacy/rebase.py <legacy base (BASE_DUMP=... from build_legacy)> <out>: apply changes/applied/v22, v23, v24 then v2.2, v2.3, v2.4, v2.5, v2.6, v2.7, v2.8, v2.9, v2.10, v2.11, v2.12, v2.13, v2.14, v2.15, v2.16 on it (as build.py does), write the new base
import json, os, sys, glob, importlib.util
os.chdir('/home/user/RealmsMap/src'); sys.path.insert(0, '.')
B = json.load(open(sys.argv[1])); town, w, pos = B['town'], B['wild'], B['room_pos']
for f in [f for d in ('v22', 'v23', 'v24', 'v2.2', 'v2.3', 'v2.4', 'v2.5', 'v2.6', 'v2.7', 'v2.8', 'v2.9', 'v2.10', 'v2.11', 'v2.12', 'v2.13', 'v2.14', 'v2.15', 'v2.16') for f in sorted(glob.glob(f'changes/applied/{d}/[0-9]*.py'))]:
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    r = m.apply(town, w, pos); print(f, str(r)[:300])
from maplib import condense
for p in w['places']:
    if p.get('route'): p['route'] = condense(p['route'])
    for o in p.get('opts') or []:
        if o.get('route'): o['route'] = condense(o['route'])
json.dump(dict(town=town, wild=w, room_pos=pos), open(sys.argv[2], 'w'), separators=(',', ':'))
