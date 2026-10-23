"""Area names (owner, Oct 23), drawn as the primary area labels (`arealabels`: italic 2.4, letter-spacing .55, pale halo, gentle arc), the owner's
wording as given:
  - "The Straight of Ahtborne" (2 lines) in the sea south of the Tower of Despair, north of Over the Cliff Maze: centred north/south in that
    sea along the Tower's line (x -8; open sea there from the coast at y 129.4 to the maze at 163.9);
  - "Otherland" on the open snow north of the Ledge of Life (the spot there farthest from any path: 6.8 rooms clear);
  - "Blood Sea" in the western sea, "Azure Sea" in the eastern sea (owner: no "The", bigger, SEA_FS): centred north/south on the whole map (the frame's middle) and
    east/west in the open sea at that height (between the frame and the coast)."""
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

LH, YOFF = 2.6, 0.6                                  # line spacing; baseline below the visual centre of a line
SEA_FS = 3.6                                         # the two sea names: half as big again as the other area names (owner, Oct 23), letter-spacing in step


def apply(town, wild, pos):
    g = wild['geo']; x0, y0, x1, y1 = wild['bounds']
    ground = unary_union([Polygon(p).buffer(0) for k in ('land', 'snow') for p in g[k] if len(p) > 2] + [Polygon(m['poly']) for m in wild['fwmazes']])
    def gap(line):
        s = line.difference(ground); s = max(getattr(s, 'geoms', [s]), key=lambda q: q.length); return s.coords[0], s.coords[-1]
    a, b = gap(LineString([(-8, 125), (-8, 175)]))
    yc = (a[1] + b[1]) / 2
    ym = (y0 + y1) / 2
    w0, w1 = gap(LineString([(x0, ym), (-60, ym)])); e0, e1 = gap(LineString([(40, ym), (x1, ym)]))
    new = [{'x': -8.0, 'y': round(yc - LH / 2 + YOFF, 2), 'lh': LH, 'sag': 1.0, 'hw': 12, 'lines': ['The Straight', 'of Ahtborne']},
           {'x': 28.0, 'y': round(223.5 + YOFF, 2), 'lh': LH, 'sag': 1.0, 'hw': 10, 'lines': ['Otherland']},
           {'x': round((w0[0] + w1[0]) / 2, 2), 'y': round(ym + SEA_FS / 2.4 * YOFF, 2), 'lh': LH, 'sag': 1.5, 'hw': 16, 'fs': SEA_FS, 'lines': ['Blood Sea']},
           {'x': round((e0[0] + e1[0]) / 2, 2), 'y': round(ym + SEA_FS / 2.4 * YOFF, 2), 'lh': LH, 'sag': 1.5, 'hw': 16, 'fs': SEA_FS, 'lines': ['Azure Sea']}]
    wild['arealabels'] = list(wild.get('arealabels') or []) + new
    return {'labels (x, y)': [(' '.join(L['lines']), L['x'], L['y']) for L in new],
            'open sea used (strait north/south; west, east at mid-map)': ((round(a[1], 1), round(b[1], 1)), (round(w0[0], 1), round(w1[0], 1)), (round(e0[0], 1), round(e1[0], 1)))}
