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
| Otherland (Oct 21; `tools/otherland_editor/`) | https://claude.ai/artifact/5B5NWTeurkdsVpDwuPFphX | `ollayout/current` | `ol_layout_final.json` |

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
- **Sea everywhere** (owner, Oct 23; `changes/009`; frame widened by `008`: +60 W/E, S/E 20 past the farthest room): all open background inside `bounds` is sea, merged into `geo.water` (one shape, rings even-odd). New land drawn later must cut the sea (and redo its rings).
- **4316 - 4317** (owner, Oct 23; `changes/015`): 22557, 14314 evenly on the line 4316-4317 (4317 isn't in the Northern Plains editor; its save now has these spots, as `legacy/np_layout_final.json`).
- **Sea names** (owner, Oct 23; `changes/010`, `arealabels`): The Straight of Ahtborne (sea S of the Tower of Despair), Blood Sea (west) and Azure Sea (east; no "The", size 3.6 via `arealabels` fs) at the map's mid-height; Otherland's name N of the Ledge of Life.
- **Standard water path** (owner, Oct 23): every water path but type C has Otherland's trail bend (`maplib.warpline`, one field for the whole map; `changes/006` bends all B routes and the currents; `005` the Ocean Keep stream made B, `streams` now empty; draw new non-C paths with it). Ends of trails/C/dashed links meeting a B route sit on the bent line.
- **Water route styles** (owner, Oct 23): no solid routes (type A, `seaways`) any more: primary = `seawaysfaint` (B), secondary = `olharborways` (C). `changes/001` moves all `seaways` into `seawaysfaint`; new water routes go straight into B or C. Desert of Despair east coast: primary path 12984-12993, 15098, 15108, 15097, 6300 is B (`changes/002`, bent by 005); its other routes (links to the coastline/land) are C (`changes/003`; `seawaves` now empty map-wide). Coral Depths: primary 669-6286-6287-12597-12598-12956-12982-12983-12984 B, its 5 land links C (`changes/004`); 12598-12599, 669-1494-1495 and 2525-2531 stay B (owner, Oct 23). Sea of Sorrows currents: thinner, opacity .4 (template SEACUR).
- **Paths meeting a water route** end exactly on its line, never past it (Oct 19).
- **Route jumps** (owner, Oct 23; `changes/017`, template/site `routeD`): ONLY the jumps the owner names are drawn as a dashed arc on a picked route (painting, Ofcol, Nidaros, Dragon's Pass 8221-8195). Add new ones only when the owner asks.
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
- **Ashen Forest beach** (owner, Oct 23; `tools/ashen_forest_editor/add_azure_beach.py`): the Azure Sea rooms joined to the beach (25 rooms, 40 spacers) are in the Ashen editor (area 'AZ'), starting spots grown from the shore along e/w exits only (owner: ignore the other exits). Drawn only after the owner's save.
  3245 and 14360 belong to the Coral Depths editor (`fix_cd_rooms.py`): fixed in the Ashen editor (CD) at the Coral Depths save's spots; when drawing an Ashen save, never take a fixed room's spot from it.
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
  Added Oct 23 (grp 'ss', `tools/wastelands_editor/add_ahtborne_gap.py`): 18041, 18039, 18042, 18043 (the mob routes' gap 17991-18040). When the
  Save Oct 23 01:00Z drawn (rebase). The sea is grown round the rooms (SEA_R): moving rooms shrinks it; `changes/005` keeps the old west edge
  (`legacy/sos_keep_water_oct23.json`, merged into its water ring: no seam). New Wastelands save: check sea lost vs the previous base.
  One-way exits (owner, Oct 20): wavy currents with an arrowhead 0.4 short of the room (`seacurrents`, template SEACUR). Winterlight Island
  (`changes/002`, `snowisles`, template SNOWISLE; re-fitted Oct 22 as a rounded blob, see Otherland): an irregular teardrop, a rounded end at 9842 (not a point), widening SW,
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
- **Otherland** (owner, Oct 21): joins the map ONLY at 22534 -> 13379, 22535 -> 13380, 18071 -> 22511 and 18066 -> 22512; all its other exits out are left off for now.
  The owner's map flattens it: an up/down exit to the same room as a flat exit is ignored (the flat one is drawn).
  Frost Mansion 22248-22250 (Asgard Nexus) is in the Otherland editor (grp 'an', owner Oct 21), joined at 22247 and 21819.
  Azure Sea east coast (owner, Oct 22; grp 'az', `tools/otherland_editor/add_azure_east.py`; drawn by `changes/001_azure_east.py`): water rooms at sea, the
  Otherland east-coast rooms on land, the coast between them, worked out ONCE (owner: no fill-then-cut; Voronoi line between sea rooms/routes and
  land rooms/trails). 15154 = a one-room iceberg, sea to its west. Coastal path (6179 .. 15250, 15255, 15606) = `seawaysfaint`, straight room to room
  (strictly on the layout, owner); routes east off it = `seawaves` (DD east coast style). Sea-land exits (up/down shown, owner) switch to `oltracks`
  exactly at the coast. Not drawn: 5987-22496 (owner), 15606 -> Grey Beach.
  Every `seafill` and `water` ring is trimmed to the final land (each ring on its own, evenodd-safe): no blue strips or shore strokes under land
  (owner, Oct 22: hairlines along old coasts). Check: visible sea fill inside land.buffer(-0.08) must be 0.
  East routes redrawn (owner, Oct 22; `changes/005_east_routes.py`, from the exits): coastal path cut at 6187 / 15171, via The Iceberg 15154 (its links are
  sea-land exits); EVERY sea-land exit = `seawaysfaint` over the water, and a run of sea rooms from the path to a room going ashore; The Iceberg 15154
  is not land for this (only its path links + climb primary); outer routes = `olharborways` style (harbour, not `seawaves`).
  North sea edge (owner, Oct 22; `changes/006`): the Northern Plains' water strip's straight cuts (x 83.1, y 153.6) are under seafill, notch filled (BOX).
  Harbour routes: width .06, opacity .26 (owner: a touch more visible).
  East cliff (owner, Oct 22; `CLIMBS` in 001_azure_east): ONE continuous cliff face along the coast's edge from the northernmost climb landing
  to the southernmost (`wild.olcliff`, template OLCLIFF, OLLEDGE style); climbs from a land room (22524, 15741) go up where that room's exit from
  the sea comes ashore (owner: no cliffs inland); every exit coming ashore across the face gets steps on the face only (as smrclimb). No coastal ice/bergs there for now (owner). The save's az rooms are those not in `legacy/ol_editor_edges.json`.
  A new Otherland save: replace `legacy/ol_layout_final.json`, then `legacy/rebase.py` on a legacy dump (the v2.4/v2.5 files redraw from it).
  Unlocked there (grp 'un', owner Oct 21): 18052-18075, 6174, 18047, 13379, 13380, 6166, 6180, 6650, 15410-15418; a save may move these map rooms.
  Drawn Oct 21 as a BASIC render (`changes/001_otherland.py`): plain trails, plain snow (`geo.snow`, template --snow, also a `geo.land` piece);
  the owner will customise later (water rooms, sub-areas, graphics): don't add any unasked.
  Not drawn (owner, Oct 21): up/down AND one-way exits (both dashed in the editor). Snow texture: `wild.olsnow` (template OLSNOW).
  North coast (owner, Oct 22; `001` NBOX): water rooms = sea (incl. the 3 'The Sea of Sorrows' rooms in the Tundra Fields); 'Over the Cliff'
  (683, 14428) is a maze for later, water for now; The Iceberg (owner, Oct 22) = 6166, 13379, 22534, 22532, 22531, 22533, 22535, 13380, 6180:
  a little WHITE island (`geo.iceisle`), sea between it and the mainland, which hugs its rooms tightly near it. NW water routes = `seawaysfaint`.
  Otherland's trails are `wild.oltracks` (template OLTRACK: snow tracks; owner, Oct 22), not fwtracks. Snow #8C969B (owner: not bright). The Iceberg in the same snow (owner, Oct 22; `geo.iceisle` empty).
  `oltracks` warped by one smooth field (TRACK_A .16, TRACK_L 7): a gentle long wave. 6180-15128 (Azure) as `seawaysfaint` (owner, Oct 22).
  Harbor of Icebergs (owner, Oct 22): open sea (WBOX), `wild.olharbor` {ice, cracks, bergs, dock} (template OLHARBOR, OLDOCK); dock =
  13100-13101-13102-13105. Harbour routes: `wild.olharborways` (thin, nearly transparent, slightly wavy). The bay between 13150 and
  the harbour's NE shore is land (FILL1). The sea grows SEA_W off the land inside the boxes, never cut by a box line. Morte's Peak: its height shading REMOVED (owner, Oct 22: too unlike the rest of the map; `olhill` keeps only Death's Spire). A computed top-down relief (faces/crests/hachures) was ALSO rejected (Oct 22: 'basically the same'): don't retry height-field renders. Heart path (8 Heart rooms + The Concealed Horror + Lost in the Darkness, from The Sudden Stop 15703: one line): thin dashed `oltunnels` (`v2.5/003`). Was: shading of the snow from above (`wild.olhill`, template OLHILL, blurred; owner, Oct 22: no peak sprites,
  no dashed passages); heights from the trail climb (ridges along its trails, the Heart the top) and Tirebaen's Gorge + the Fissure
  (`wild.olgorge`, template OLGORGE) (owner, Oct 22). Also (owner, Oct 22): Death's Spire (shading); NO relief on the west/south land (Gods, hills, the
  Mountain, the Den: removed, owner); Bed of the Runoff (`olrunoff`); the south shore
  (SBOX: sea, `olsouth` beach + floes, its icebergs in `olharbor.bergs`). Shacks (owner, Oct 22): `wild.olshacks` [cx, cy, w, h] (template OLSHACK), over The Desolate Outpost's main section and
  The Hunter's Outpost 14419. Water path 22530-22531 (`seawaysfaint`). Clearings (owner, Oct 22): ONLY the Tundra Fields (13492's clump); A Tunnel in the Snow / A Cold Lair (13322's clump) is an icy maze
  blob of the same outline, no label.
  Land west/south of 13287 (FILL1, owner Oct 22): no sea inlets there. Sub-area markers (owner, Oct 23; `changes/002_otherland_places.py`): Wild Tundra, The Ziggurat, Valley of Crucifixion, Cursed Lands; routes South (default) + North (via the Blood Sea wrap: line in 2 pieces), the owner's room counts; routes kept in the change file, not data.py.
  Editor rooms added Oct 23 (grp 'sa', `tools/otherland_editor/add_sub_areas.py`): 13285, 13282, 13283, 13284, 15749 shown (to arrange; not drawn until saved);
  13072, 15259 HIDDEN (`hidden0`: kept hidden when a save doesn't list them), route-only: give them map spots for the tracer (not drawn), and NO line
  5967 -> 13072 / 5970 -> 15259 (the North routes' break stays there; owner).
  Save Oct 23 00:19Z drawn (rebase). The legacy rebuild reshuffles Otherland's plants/drifts/floes everywhere: `changes/003_otherland_keep_sprites.py`
  restores them from `legacy/ol_keep_oct23.json` outside the save's changed area (do the same after any new Otherland save). New editor rooms must be
  added to `legacy/ol_editor_edges.json` (else v2.6/001 treats them as Azure Sea rooms). 13072/15259: `track` cx spots (002), never drawn.
  Winterlight Island re-fitted (owner, Oct 22, `changes/001_winterlight_island.py`): a smooth irregular blob (oval + low harmonics, rounded end at 9842), the biggest 0.9 clear of the paths; fit kept in `FIT` (`REFIT=1` re-searches, ~30 s).
  Cramped Tunnel rooms (+ those leading only to them): `oltunnels`, drawn as JUST a thin dashed line (owner, Oct 22, after rejecting
  glimpse/strip styles and the SMR underground-river style: don't retry those). Icy mazes (`fwmazes` style 'ice', `lines` = label lines):
  Over the Cliff Maze (14428-683: sea only, east edge = the coast, never over land or trails; now a ~2-room band along the coast, its two paths cut 1 room past the coast: owner Oct 23, `changes/020`), The Maze of Ice (+ Frost Mansion `olmansion`, inside it). The Ledge of Life: `olledge`.
  South of 6143 (FILL_S; 6147, 6148 as land): regular land, no beach, no inlet (owner, Oct 22).
  Saves from Oct 22 18:39Z on keep the west/south 3 east: applied/v2.4/001's hand-set west shapes (WBOX, HARBOR, SBOX west edge, FILL_S, FILL1's
  harbour pieces, NBOX's west box) are translated by `WS = 3.0` (and 006's SBOX). A new save that moves them again: move these with it.
  Otherland's sea (001_azure_east step 2) is rebuilt as ONE evenodd-visible shape minus the land (+ background specks at the coast filled); land
  closed by 0.06 (no hairline cracks); no lagoons without a sea room. Checks after any coast change: sea under land 0, background at coast 0.
  Fissure vs gorge (owner, Oct 22; `changes/002_fissure.py`): 'The Fissure' rooms are DOWN paths to the gorge floor: the descents 13180->13179,
  13222->13221 = narrow clefts widening downwards (`wild.olfissure`, template OLFISSURE) with steps + down chevrons; `olgorge` only round the
  Floor of Tirebaen's Gorge rooms (flat ground at the bottom).
  Gorge (owner, Oct 22): never touches the A Tunnel in the Snow maze (wall cut back, `v2.5/004`); its floor carries rocks/gravel/cracks (`olgorge.rocks/gravel/cracks`, `v2.5/005`), clear of its trail.
  East coast (owner, Oct 22; `v2.5/007`): bay east of Morte's Peak filled (closed r 5 in BAY), sea EBOX SEA_W 6 (seafill + seashore); its ice `v2.5/008` (v2.5/006).
  Trail crossings without a room (owner, Oct 22; `v2.5/009`): electrical-style jumpers (half-circle hop, up-left; tunnel or shorter line hops); NO gaps or marks.
  Mountains (owner, Oct 22): drawn from straight above as the owner's examples (several peaks per massif): stepped terraces, inked edges, hachured cliff
  faces deepest lower right, flat ledges, faceted summit caps (`wild.olmassif`, template OLMASSIF; Morte's Peak `changes/002_morte_massif.py`: base = circle
  (65.88, 193.37) r 10.78, summit The Fury of Morte's Peak). NEVER height shading/blurred relief. Lines EXTREMELY subtle (owner, Oct 22: trails must read clearly over them). Base outline not drawn, ledges unfilled = the snow itself (owner, Oct 22: blend in). Plants/drifts kept round it; cleared only on the terraces (level 1 + its face).
  Each peak's top two tiers a little lighter (`crown`, owner Oct 22; a shared tier split by nearest peak). Zenith of the Gods (`changes/003_gods_massif.py`, 002's `build()`): base
  = `wild.olmtnbase[1]` from `changes/001` (holds the Maze of Ice + Frost Mansion, off the sea; not drawn), summit The Zenith of the Gods 15663 (0.77 from
  the coast-side base edge: terraces stack into one sheer face there, `sheer`); the Maze of Ice is drawn over the east peak.
  Even cover (owner, Oct 22; `changes/004_even_cover.py`): plants/drifts everywhere on the snow, no bare patches (gap fill: plant if none within 1.6,
  drift if none within 3.3). Re-run its check after land changes: open snow >1.5 from a plant was 2.6%.
  Plants (owner, Oct 22; `v2.5/010`, `wild.olflora` [x,y,scale,kind p/b/s/g,variant], template OLFLORA sprites op*/ob*/os*/og*): density by the nearest room name's land kind (DENS).
  Shore ice (owner, Oct 22): floes + small bergs along the WHOLE sea coast at the south shore's density (`v2.5/006`, appended to `olsouth.floes` / `olharbor.bergs`).
