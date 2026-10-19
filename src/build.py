# Build the map: python3 build.py  ->  ../realm_map.html, then the tiled site (../site/)
# Starts from the frozen map (base/map.json, the state of Oct 19 after v20) and applies the changes in changes/ in file-name order.
#   NO_TILES=1                  skip the tile bake
#   FINAL_DUMP=<file>           also write the finished map data (for building layout editors)
#   python3 build.py --freeze   fold the changes into a new base/map.json (when saving a version; then delete the change files)
# The old pipeline that drew the map from the world file is kept in legacy/ (python3 legacy/build_legacy.py).
import json, os, sys, glob, subprocess, importlib.util
os.chdir(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '.')
from maplib import condense
B = json.load(open('base/map.json'))
town, w, pos = B['town'], B['wild'], B['room_pos']
for f in sorted(glob.glob('changes/[0-9]*.py')):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    print(os.path.basename(f) + ':', m.apply(town, w, pos))
for p in w['places']:                                           # every route in numbered form, '#N dir' (owner, Oct 18)
    if p.get('route'): p['route'] = condense(p['route'])
    for o in p.get('opts') or []:
        if o.get('route'): o['route'] = condense(o['route'])
if '--freeze' in sys.argv:
    json.dump(dict(town=town, wild=w, room_pos=pos), open('base/map.json', 'w'), separators=(',', ':'))
    print('base/map.json written: delete the files in changes/ now'); sys.exit()
if os.environ.get('FINAL_DUMP'): json.dump(w, open(os.environ['FINAL_DUMP'], 'w'))
w['track'] = {k: v for k, v in w['track'].items() if not k.startswith(('ft', 'wt'))}    # (the Forest of Tears editor's room spots: kept in the base, not on the page)
nd = dict(town); nd['wild'] = w
open('../realm_map.html', 'w').write(open('template.html').read().replace('__DATA__', json.dumps(nd, separators=(',', ':'))).replace('__VERSION__', open('VERSION').read().strip()))
print('wrote realm_map.html')
if not os.environ.get('NO_TILES'):
    subprocess.run([sys.executable, 'site_build.py'], check=True)
