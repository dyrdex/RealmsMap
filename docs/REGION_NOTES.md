# Region notes (current rules only)

The map was frozen on Oct 19, 2026 (after v20, with the Miden'nir routes and Fog Cliffs fixes) into `src/base/map.json`.
This file keeps only what still applies when changing the map. The full history of how each region was drawn (v1 to v20, the old
pipeline's decisions, numbers, file names) is in `docs/archive/REGION_NOTES_to_v20.md`: search it with grep for a region or room
number, don't read it whole.

## The frozen map (`src/base/map.json`)
- `town`: New Darkhaven (`town`, `places`). `wild`: everything else. `room_pos`: room id (text) -> [x, y] for 6,088 placed rooms
  (from all editor saves; earlier saves win, as the old route tracers did). `wild.track['cx<id>']` holds more rooms (the town,
  Shadow Grove, Forgotten Woods); `maplib.tracer(pos, wild)` uses both.
- Places (`wild.places`, 131): `name`, `route` (owner's directions), `room`, `dir`, `path`/`segs` (the traced line, one list per
  unbroken piece), `note`, `group`, `where`; some `kind` (town emblem), `opts` (route options), `at` (marker spot off its room),
  `nolabel`, `small`, `key` (old name, for label tweaks).
- Drawing layers: sprites `trees`, `tufts`, `peaks`, `crags`, `boulders`, `hills`, `brush`, `wheattufts`, `reeds`, `thorns`
  (lists of [x, y, size, ...]); ground tints `geo.<name>` (polygons: land, deep, wheat, barren, cliff, ...); lines `fwtracks` (dirt
  trails), `etrtracks` (trade roads), `dirtroads`, `seaways`, `streams`, `smr*`, `mdfaint`, `pffaint`; drawings `gfx` (sprite
  name + spot, e.g. `stonecity`, `volcano`, `saloon`, `text`), `buildings`, `smrhouses`, `smrtowns`, `wltown`.
  `geo.seafill` + `seashore` (sea filling gaps after a coast change, drawn over the sea), `talltrees` ([x, foot y, height, variant]; template TALL), `camps` (palisade wall polygon + gates, tents, long house, corral, fire pit; template CAMPS). How each is drawn: `src/template.html`.
- Changes go in `src/changes/NNN_name.py` (see its README). Never edit `base/map.json` by hand; `build.py --freeze` rewrites it.

## Layout editors
Republished Oct 19 in the owner's current claude.ai organization (the old links in `docs/archive/` are in another organization and are not
used any more); each was loaded with the owner's latest save (its `<key>/current` document), so it opens where the owner left off.
New areas: rooms go into a layout editor first; drawn only after the owner places them and saves (owner, Oct 18).
Starting spots from `src/editor_spread.py` (`spread_clear`), with its numbers reported (owner, Oct 16).
To make a new editor: copy the newest builder (`tools/mire_editor/build_mi_editor.py`, run from anywhere; it reads the old saves
from `src/legacy/`) and feed it `FINAL_DUMP=<file> NO_TILES=1 python3 build.py`. Then draw the owner's save with a change file.
The other builders run inside `src/legacy`.

| Region | Editor | Save key | Save on file (`src/legacy/`) |
|---|---|---|---|
| Ashen Forest + Eastern Trade Route | https://claude.ai/artifact/SGxdtXWz9KmTx136HRoqXp | `ashlayout2/current` | `ashen_layout_final.json` |
| Northern Trade Route | https://claude.ai/artifact/TCMYDB44YJcBNyHHCbncEi | `ntrlayout/current` | `ntr_layout_final.json` |
| Barren Peaks | https://claude.ai/artifact/5ew6mZt2c4uTadZffTyYsW | `bplayout/current` | `bp_layout_final.json` |
| Northern Plains | https://claude.ai/artifact/WRfbZ3YQQoFZznCYY7Utbe | `nplayout/current` | `np_layout_final.json` |
| Azure Sea Coast | https://claude.ai/artifact/QzE74CZTXFsz5x9LjVpgP7 | `azlayout/current` | `az_layout_final.json` |
| Forest of Tears + Lake + Western Trade Route | https://claude.ai/artifact/84fj2gshfLkwJHdiWoGG5P | `ftlayout/current` | `ft_layout_final.json` |
| Southern Mountain Range + its Trade Route | https://claude.ai/artifact/CGhes5s64FvHYSJgKQaiJk | `smrlayout/current` | `smr_layout_final.json` |
| Miden'nir | https://claude.ai/artifact/AQ6TJxfjMapiknTNtij2XA | `mdlayout/current` | `md_layout_final.json` |
| Pixie Forest | https://claude.ai/artifact/3MJzJ4g1ezZKRgZR8H3A2M | `pflayout/current` | `pf_layout_final.json` |
| Coral Depths | https://claude.ai/artifact/Mjng42RvVc8q3s44UEKjEa | `cdlayout/current` | `cd_layout_final.json` |
| Angel's Landing, Village of Edo, Grimdog | https://claude.ai/artifact/M8TS87UDLLEyPDgKUKRLFD | `nalayout/current` | `na_layout_final.json` |
| Wastelands | https://claude.ai/artifact/XtoCQTMrpPQCLZREeczD7L | `wllayout/current` | `wl_layout_final.json` |
| The Mire | https://claude.ai/artifact/QAUXkaXfwFS1fgDRiXzHmo | `milayout/current` | `mi_layout_final.json` |
| Desert of Despair | https://claude.ai/artifact/JKaM8hA8ih8XHfNJQifgqA | `ddlayout/current` | (none yet) |

## Standing owner rules, by region
- **Everywhere**: routes and room counts are the owner's own (`data.py`: `MORE_DIRECTIONS`, `ROUTE_OPTIONS`), never computed;
  directions in numbered form. A route's marker goes where the route leaves the area. Asgard Nexus and World Housing stay off
  the map (Oct 12). Castle Darkhawk has no route yet.
- **Cities**: every city is the standard round marker + the `stonecity` drawing above it (`gfx` at 'above-pin'); no walled-town
  emblem (`kind: 'town'`) any more (Oct 19).
- **Paths meeting a water route** end exactly on its line, never past it (Oct 19).
- **Shortcuts in routes** (long straight lines): the Ofcol Shortcut (legacy route_fix, OFCOL) and the Nidaros Shortcut
  (936 sw 5511 -> 5507; `changes/007`). A new shortcut: place its rooms in an editor, then join the routes' pieces at it (as 007).
- **Trade routes** (Eastern, Northern, Western, Southern Mountain): one continuous formal road; off-ramp pads where paths or
  sub-area links join; dirt trails elsewhere. Spacer rooms drawn only between two real rooms.
- **Older-area clearings** (Forgotten Woods, Ashen Forest, Barren Peaks; Oct 19): only the clear-cut clumps the owner picks; ground of their own
  spot, a little lighter (`wild.clearings`, template CLEAR, drawn over the dirt trails, under the trade roads).
- **Settlement drawings** (owner, Oct 19): plan view like Edel (solid shapes, dark outlines, soft shadows, the map's own trails), not
  thin side-view ink line-work. Inahir Camp: `wild.camp2`, template CAMP2 (`changes/003`).
- **Barren Peaks**: no coasts unless the owner asks with a clear picture.
  Editor republished Oct 19 (v2) with all 592 Forgotten Woods rooms unlocked (green outline; `D.unlocked`, saves now v:3 so older
  saves don't re-lock them). A save that moves or hides FW rooms means redrawing their Woods trails too.
- **Azure Sea Coast**: the owner's name for the 49-room Azure Sea pathway; a blue water route at the foot of the cliff.
- **Forest of Tears**: Fog Cliffs mountains reach 2 rooms east of the cliff path (Oct 19, so the Tree of Life is in the forest).
- **Miden'nir**: the painting (Black Forest, brambles, Mount Doom) stays; the tunnels under Mount Doom are left out; Forest rooms
  are faint wavy dashed trails, 1049-1051/1060 regular paths.
- **Southern Mountain Range**: paths widen where rooms are directly adjacent; clumps of touching rooms are clearings (hand-made
  ones in `legacy/smr_clearings.json`). Up/down exits drawn as small dirt lines except 291-292.
- **Wastelands**: quick, broad-strokes work. Never change the Southern Mountains (clearings, ground, sprites) when working here.
  One ground (`wheat`) under everything, no other tint over it. Coast path is a water route in the sea. Hidden: 8700, 8754;
  rooms 8722-8889 not drawn. Open: Mulciber's Forge's directions break at 8557 ('#3 s' after 8562): ask the owner.
- **Desert of Despair** (editor Oct 20, `tools/desert_of_despair_editor/`): builder reads `base/map.json`'s room_pos directly (not the legacy saves):
  `FINAL_DUMP=<f> NO_TILES=1 python3 build.py`, then `python3 build_dd_editor.py <f> desert_of_despair_editor.html` (~1 min; RES 0.2). Unlocked (grp 'un', Oct 20): 6365, Wastelands 8605, 8607, 8609, 8714, 6538 (moving them means redrawing their trails).
- **The Mire**: no Mire sea; don't touch the sea unless asked (Oct 18). Unsaved editor rooms are never drawn.
