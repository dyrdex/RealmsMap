# Refreshes the editor's background (land, sea incl. seafill, trails, mazes) from the current map (owner, Oct 23: it showed the coast from before the Knights bay).
#   cd src && FINAL_DUMP=<f> NO_TILES=1 python3 build.py && python3 ../tools/barren_peaks_editor/refresh_ctx.py <f> ../tools/barren_peaks_editor/barren_peaks_editor.html
# Rooms and saves are untouched (the editor loads bplayout/current). Works for the other editors built the same way (D.ctx land/water/tracks/mazes).
import json, re, sys
from shapely.geometry import Polygon, box, MultiPolygon
from shapely.ops import unary_union
w = json.load(open(sys.argv[1])); F = sys.argv[2]
h = open(F, encoding='utf-8').read(); m = re.search(r'const D=(\{.*?\});\n', h); D = json.loads(m.group(1))
xs = [r['x'] for r in D['rooms']]; ys = [r['y'] for r in D['rooms']]
B = box(min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20)
def parity(L):
    g = Polygon()
    for p in L:
        if len(p) > 2: g = g.symmetric_difference(Polygon(p).buffer(0))
    return g
G = w['geo']
sea = unary_union([parity(G['water'])] + [Polygon(p).buffer(0) for p in G.get('seafill', []) if len(p) > 2]).intersection(B)
land = parity(G['land']).intersection(B).difference(sea)
def rings(g):
    g = g.simplify(0.03); out = []
    for P in (g.geoms if hasattr(g, 'geoms') else [g]):
        if P.geom_type != 'Polygon' or P.is_empty: continue
        for r in [P.exterior] + list(P.interiors):
            out.append([[round(x, 2), round(y, 2)] for x, y in list(r.coords)[:-1]])
    return out
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + list(w.get('etrtracks', [])) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + list(w.get('smrdash') or [])
C = D['ctx']; old = {k: len(v) for k, v in C.items()}
C['land'] = rings(land); C['water'] = rings(sea)
C['tracks'] = [rd(t) for t in trk if len(t) > 1]
C['mazes'] = [dict(poly=rd(q['poly'])) for q in w['fwmazes']]
h = h[:m.start(1)] + json.dumps(D, separators=(',', ':')) + h[m.end(1):]
a = '<span>The lake</span>'
if a in h: h = h.replace(a, '<span>Water (the sea and the lake), as on the map now</span>')
open(F, 'w', encoding='utf-8').write(h)
print('box', [round(c, 1) for c in B.bounds], 'old', old, 'new', {k: len(v) for k, v in C.items()}, 'land area', round(land.area), 'sea area', round(sea.area), 'KB', len(h) // 1024)
