# The Zenith of the Gods (owner, Oct 22): a mountain from straight above, as Morte's Peak (002's builder, same style), on the base set in 001.
# Peaks from the room names: The Zenith of the Gods the summit (owner); a north peak (Zenith of the Gods Pass in the saddle to it); an east
# peak under the Maze of Ice, The Throne of a God at its top (the maze is drawn over it); a low plateau above Just Below the Plateau.
# The Gullet of the Gods runs down the valley between them.
import importlib.util, os
from shapely.geometry import Polygon, box

_spec = importlib.util.spec_from_file_location('ol_massif', os.path.join(os.path.dirname(os.path.abspath(__file__)), '002_morte_massif.py'))
MS = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(MS)
PEAKS = [((-5.0, 192.0), 7.0, 5, 0.9),      # The Zenith of the Gods 15663: the summit (owner)      (centre, height in steps, ridge arms, arm turn)
         ((3.5, 185.2), 4.0, 4, 0.5),       # north: the pass rooms (-2.5, 188), (5, 188) in its saddle
         ((17.5, 193.0), 5.0, 4, 0.3),      # east: under the Maze of Ice; The Throne of a God, Frost Mansion at its top
         ((8.0, 197.3), 3.0, 4, 0.7)]       # a low plateau above Just Below the Plateau
SHEER_W, SHEER_X = 1.6, -3.0                # the summit is 0.77 from the base's (coast-side) edge: its terraces stack into one sheer face there


def apply(town, wild, pos):
    base = Polygon(wild['olmtnbase'][1])
    names = ('The Zenith of the Gods', 'Zenith of the Gods Pass', 'The Gullet of the Gods', 'The Western Face', 'The Icy Cliffs', 'The Southern Face of the Gods',
             'The Throne of a God', 'Deep Within the Shadows', 'Just Below the Plateau', 'Skirting the Shards')
    sheer = base.difference(base.buffer(-SHEER_W)).intersection(box(-99, 186.5, SHEER_X, 196.5))   # the coast by the summit: one sheer face
    return MS.build(wild, pos, base, PEAKS, 300, names, 'The Zenith of the Gods', sheer)
