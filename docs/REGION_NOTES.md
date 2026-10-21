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
- `geo.land` is drawn as one evenodd path: a land polygon inside another cancels it (bare holes; `changes/004` removed three). Never add an
  overlapping land piece: union it into the big one. Same for ground tints: extend the area's own polygon, never a separate piece (seams;
  owner, Oct 20).
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
| Desert of Despair | https://claude.ai/artifact/JKaM8hA8ih8XHfNJQifgqA | `ddlayout/current` | `dd_layout_final.json` |

## Standing owner rules, by region
- **Everywhere**: routes and room counts are the owner's own (`data.py`: `MORE_DIRECTIONS`, `ROUTE_OPTIONS`), never computed;
  directions in numbered form. A route's marker goes where the route leaves the area. Asgard Nexus and World Housing stay off
  the map (Oct 12). Castle Darkhawk has no route yet.
- **Cities**: every city is the standard round marker + the `stonecity` drawing above it (`gfx` at 'above-pin'); no walled-town
  emblem (`kind: 'town'`) any more (Oct 19).
- **East coast cliff (Coral Depths to the north)**: the sea meets the cliff-top path's hachures directly from y 13 to the bay north of the
  Coral Depths marker (owner, Oct 20; `changes/005`): no land between cliff and sea there.
- **Desert of Despair terrain** (owner, Oct 20; `changes/007`, `wild.ddsand`, template DDSAND, over geo.sand 16): grain + wind texture,
  ripple fields, dunes, dry lake beds, rocks, scrub, very few cacti; its own look, not the Wastelands' (no grass tufts or crags).
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
  Editor v3 (Oct 20, `tools/wastelands_editor/build_wl3_editor.py`, reads base/map.json; save format 'wl-layout-3'): grp 'ss' the owner's 47 Sea of
  Sorrows / Blood Sea rooms + 45 joining spacers (17768, Machine Dreams, left off); grp 'wl' the 22 beach rooms + 38 placed spacers unlocked; rest fixed.
  Drawn (save 20:39Z, `legacy/wl3_layout_final.json`) by `changes/001_sea_of_sorrows_rooms.py`: water routes
  straight room to room (every point doubled), in `seawaysfaint` (template SEAFAINT, opacity .4: open-sea routes are faint, owner Oct 20); bay water
  extended inside a box; bounds y1 161.
  One-way exits (owner, Oct 20): wavy currents with an arrowhead 0.4 short of the room (`seacurrents`, template SEACUR). Winterlight Island
  (`changes/002`, `snowisles`, template SNOWISLE): an irregular teardrop, a rounded end at 9842 (not a point), widening SW,
  outline rounded (no spits), its SE coast an even, nearly straight run NE-SW (owner: natural,
  not an oval, not following the paths), the biggest that fits 0.9 clear of them; old-map style (muted, ink lines, no glossy art); no label.
- **Desert of Despair** (editor Oct 20, `tools/desert_of_despair_editor/`): builder reads `base/map.json`'s room_pos directly (not the legacy saves):
  `FINAL_DUMP=<f> NO_TILES=1 python3 build.py`, then `python3 build_dd_editor.py <f> desert_of_despair_editor.html` (~1 min; RES 0.2). Unlocked (Oct 20): grp 'un' 6365; grp 'wl' the 198 Wastelands rooms shown round the desert (spacers incl.); grp 'cd' the 34 rooms shown from the Coral Depths editor. Moving them means redrawing their trails.
  Added Oct 21 (`add_azure_coast.py`, run once on the built editor): grp 'az', the Azure Sea coast south of the Docks (25 rooms: the Pale, Sandy Coastline /
  Salt and waves string from 6329, 6307, 12986 + the Azure and Green rooms joined to it; 70 spacers); start spots spread from dd_layout_final.json.
  Rebuilding with build_dd_editor.py drops them: rerun the add script after, then `add_dd_rooms.py 15038 12988 15049 15055 15054 15056`, then `add_dd_rooms.py 15128 6650 15410 15411 15412 15413 15414 15415 15416 15417 15418 6180 13380 6166 13379` (owner's extra rooms, Oct 21). Drawn (save Oct 21 14:20Z, `legacy/dd_layout_az.json` + `dd_editor_edges_az.json`) by `changes/applied/v2.3/001_azure_sea_coast.py` (frozen in 2.3): land-land exits
  (via spacers) = desert `fwtracks`, the rest = `seawaves` (template SEAWAVE, opacity .15, wavelength 2.5, amp .12: owner Oct 21, open ocean routes very faint + gently wavy); sand (geo.sand 16 = ddsand.poly) extended under off-land coastline rooms; sea = water 9
  carried south inside BOX (closed 4 against the coast, no pockets); bounds x1 113, y1 186. dd_layout_final.json left as it was (the legacy draw).
  Drawn (Oct 20, save 14:39Z) by the LEGACY pipeline: `legacy/dd_merge.py` (land chained last into smr_merge's land_edit, kept off the WL south
  sea; one `sand` ground; clearings by the range's cell rule; `fwtracks`), wired in `build_legacy.py`: the save's 'wl' rooms (+ hidden) go into
  the WL layout, 'cd'/'un' rooms into the CD layout (6365 then into the SMR layout; smr's window pinned at 6365's old spot so the range doesn't
  re-roll). smr_merge's grid: x to GF.X1 + 24, y to 170. cd_merge's sea reaches 2 rooms past its swimming rooms. New base = `BASE_DUMP=<f>
  NO_TILES=1 python3 legacy/build_legacy.py`, then `python3 legacy/rebase.py <f> base/map.json` (re-applies applied/v22 + v23; without the
  DD save this reproduces the old base exactly). No sprites/labels yet (not asked).
  Owner (Oct 20): desert trails straight through every room (`exact`, no smoothing). Arid Steppes clearing grows over rooms reached from the
  steppes by n/s/e/w exits <= 2.6 inside `STX_BOX` (44..56, 88..116), merged with the old steppes polygon. DD rooms named An Ancient Road =
  `dirtroads` (+ their links to WL road rooms).
  The template draws lines as curves through midpoints (they cut corners): `ntr_merge._sharp` doubles a room's point so the curve passes it
  exactly (all desert lines; cd_merge for rooms in `EXACT` = moved in the DD editor). `dd_merge.drop_dangling`: trails left ending at a
  spacer whose far room moved away (181-19863) are removed.
  Editor v5 (Oct 20): grp 'ge' = 10 added Great Eastern Desert tunnel rooms (6549-9070, 9057, spacers 22630, 22145), start spread from the save;
  rebuild with `DD_BASE=<git show ae3db68:src/base/map.json>` (the pre-desert base) so the other starts stay. dd_merge draws 'ge' as desert rooms (not in the steppes' grid search).
  Desert route options (River default, East alt, no room counts: card shows none) in `changes/applied/v24/001_desert_places.py` `RIVER`, not data.py.
  Desert places, mazes, the (Emerald Hills) label: `changes/applied/v24/001_desert_places.py` (frozen into the base in v24; rebase.py re-applies it after a legacy redraw). Mazes:
  fwmazes style 'desert' + `nolabel` (template). Owner's marker rules: Barren Wastes ends at 13061; markers on hidden 6561 / 929 (routes over them).
  `dd_merge.EXTRA_CLEAR`: hand-picked clearings (rooms + exits, holes filled), e.g. the ruins round 6464 with its east/west single rooms.
- **The Mire**: no Mire sea; don't touch the sea unless asked (Oct 18). Unsaved editor rooms are never drawn.
