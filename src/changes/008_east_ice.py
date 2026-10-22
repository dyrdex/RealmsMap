# Otherland's east coast (owner, Oct 23): its floating ice and little icebergs, the same as along the rest of the shore (006's placement,
# limited to the east coast's new sea, so the ice already placed stays where it is).
import importlib.util, os
from shapely.geometry import box

EAST = box(56, 180, 110, 242)


def apply(town, wild, pos):
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '006_shore_ice.py')
    spec = importlib.util.spec_from_file_location('shore_ice', f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.place(wild, pos, 23233, only=EAST)
