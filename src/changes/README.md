Changes on top of the frozen map (`../base/map.json`), applied by `../build.py` in file-name order.
One file per change, named `NNN_short_name.py` (e.g. `001_inahir_village.py`), each with

    def apply(town, wild, pos):     # town = the town data, wild = everything else, pos = room id (text) -> [x, y]
        ...
        return {'what changed': numbers}       # printed in the build log

Helpers: `maplib.world()`, `maplib.tracer(pos)`, `maplib.condense(route)`.
When a new version is saved, the changes are folded into a new base (`python3 build.py --freeze`) and their files removed.
