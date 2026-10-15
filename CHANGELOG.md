# Realm Map changelog

## In progress

- Route options: a place can now have a default route plus alternate routes, each with your direction word, room count and note. The pop-up shows the default, then "Alternate routes:"; tick one to draw it on the map instead. Routes and counts come only from your list (`ROUTE_OPTIONS` in `src/data.py`).

- Transylvania: River (37 rooms, Safest Route) is now the default; East (28 rooms) and South (36 rooms) are its alternates. All three end in room 688. River and East draw without a break; South keeps its gap through undrawn areas.

- Route options for 5 more places, River the default, East and South the alternates (your room counts): The Von Deusen Mausoleum (40 / 22 / 30), The Wilds (37 / 24 / 27), The Ruins of T'man (39 / 21 / 29), Old Pottswort's Fields (37 / 28 / 35), Emerald Hills (34 / 28 / 35). River and East draw without a break for all five; South has a gap through undrawn areas for all five.

- `pull branch` added before the last `n` in all three Von Deusen Mausoleum routes, as in its earlier directions.

- All route options (Transylvania's too) written in numbered form (`#8 e;#2 se;...`).

- Transylvania's route notes copied to the other five places' routes: River "Safest Route", East "May encounter mobs at night (requires hide)", South "May encounter mobs (requires hide)" (15 routes).

- Miden'nir rooms from your editor save (Oct 15, 18:41Z) drawn on the painted Miden'nir: 37 rooms shown, 11 hidden. Forest rooms (except 1051), the six Stuck in the Brambles rooms and the inn's 1030 + 1031: a faint, wavy dashed trail marking (36 lines, incl. 1041's up-link to room 590 in the Southern Mountains). 1060 (with its link up to 679), 1049, 1050, 1051, 22569, 22568, 22564: regular trails (6 lines, incl. 1051 to the Darkhaven spacer 22565). The old fading path from the rusted bridge into the forest is replaced by the 22568-22564 trail.

- Double path south of the stone bridge into Miden'nir cleaned up: the new 1051 -> 22565 trail is gone; the old path to Miden'nir already runs there and now ends at room 1051.

- Suds 'n Stones is a destination: listed under Areas, with your directions (`#8 w;sw;s;#2 sw;s;#2 w;#2 sw;w;se;sw;se;sw;se;#2 sw;se;#2 s;sw;s;sw;s;se;e;ne;se;s;se;e`), which end on the road outside the inn (room 9301; the inn is `n` from there). A small dot just west of its label; the label is unchanged.

- V'laresch moved to the Mobs list (its pin is now a mob pin).

- A'enari added under Mobs (`#8 e;#3 ne;#3 e;ne;e;ne;#2 e;#5 n;sw;nw;w;#4 n;enter;ne;w`): the line follows the map to Markings of Possession (where the Reomyr Village pin is), then runs on through the 6 undrawn Pixie Forest rooms (placed roughly, 0.8 apart) to where your directions say `enter`; the pin is there, about 4 rooms north-west of Reomyr Village.

- Pixie Forest rooms from your editor save (Oct 15, 21:26Z): the 14 Pixie Forest / Asgard Nexus rooms drawn only as a very faint dashed trail (15 lines, fainter than Miden'nir's). Forgotten Woods rooms 4017, 4018, 4019 moved to your spots (4019 by 7 rooms) and still the usual pathway: the Woods trail bends through them on to 4084 (10 trees cleared off its new course).

- Routes through the Pixie Forest now follow your layout in full: A'enari's line runs to Serenity (pin there, no more rough placement); Reomyr Village's line runs on to 5004, the room it is up (u) from, and its pin moved there; Nevermore's line follows the moved Woods rooms.

- New directions: Pixie Forest (`#8 n;ne;w;n;ne;nw;e;ne;n;e;ne;#2 n;#2 ne;nw;n`): the line runs into the Pixie Forest at 4993 and ends at 4994 A Grassy Clearing, where its pin now sits (was beside Bleeding Wildflowers). A'enari (`#8 n;ne;w;n;ne;nw;e;ne;n;e;ne;#2 n;#2 ne;#2 e;n;ne;nw;w;#4 n;enter;ne;w`): now through the Woods and 4017-4019; pin unchanged at Serenity. Reomyr Village: your directions were already the ones on the map. All three lines unbroken.

## Version 14 · The Southern Mountain Range, its Trade Route and the Darkhaven River tunnel · October 15, 2026

- Canyon redrawn to read as a pit going down: 4 levels instead of 6 (rim, two wall levels, floor), east and west walls close-set so they look like steep cliffs (wider ledges only on the south side), darker toward the floor, an inner shadow around the floor, and longer hatching on the east and west walls.

- All sub-area directions are now in numbered form (`#N dir`; repeated moves merged, e.g. `sw;sw` -> `#2 sw`); 60 routes tidied. Commands like `open n` or `look painting` are kept as they are.

- Black Dagger Outlaws Hideout directions updated to your new route (`#7 w;sw;s;w;#2 sw;...`; I read the commas in your first group as semicolons).

- The Darkhaven River now ends at room 1 and turns south into a cave mouth. Its tunnel (rooms 1 to 13) is drawn as a faded, see-through ghost layer with dashed walls and flow arrows toward the mouth. Per room: a lake (5) with a grotto (6) joined to it and a dashed surface exit, rapids (3), a downpour (4), stalactites (11, 12), a bend (2), and a twin-fork waterfall with a tunnel mouth beyond room 13. The tunnel rooms are no longer drawn as dirt paths. Config: `undergrounds` in `src/smr_clearings.json`.

- Edel's new south gate: a gatehouse with two round towers in the town's south wall, a paved road from the street to it, and a stone bridge (paved deck, parapets, corner posts) leading south over a short stream (the river rooms 119/124 run under it; the trail pieces under the bridge are not drawn). Rooms from your save of Oct 14 22:44Z (rooms 108 to 116, 14898, 14900, 19374, 124, 9282 moved; 108, 109, 110 unhidden).

- The Darkhaven River continues beyond the waterfall (room 13) as a stream, a little wider than a path, through rooms 18, 16, 28, 27, 31, 44, 41, 124, 119 and the spacer rooms between them (14899, 14897, 14898, 14900, 123, 20697), down past Edel, under its bridge (the short stream drawn for the bridge is replaced by this). From 119 it widens into a still pool at 120, then spreads into a wide flooded area at 125 and is lost in a marsh (126: puddles, reeds, dark wet ground). Config: `river` in `src/smr_clearings.json`.

- Darkhaven tunnel: the passage from room 5 to the grotto at 6 is now part of the underground river (same faded blue ghost layer; the grotto graphic stays); from 6 to room 7 a dry, brown underground cavern (dashed pale-brown walls, loose rocks, a cave mouth at 7); 7 to 8 stays a normal pathway. The open ground round the lake, grotto and cavern is filled with the area's hills and ground (it was a gap), and the underground rooms no longer set the terrain above them.
- The Enormous Canyon (box -25.2,23.0 to -17.9,29.3): drawn from above as terraced, hachured rock walls closing in to a shadowed floor, with the innermost layer as the floor and a narrow ledge path of hairpins (thin, broken stretches) from the top entrance at room 348 (south) down to the base entrance at 118 (north), and small caves in the walls. The hidden rooms are not drawn; sprites inside the box are cleared.

- Darkhaven tunnel exit: the cavern mouth after room 12 moved down-southwest so it touches the little waterfall at room 13 (the river now runs on unbroken).
- A new path from room 3422 (Miden'nir, Stuck in the Brambles) to the Moria marker, drawn from your description: east across the brambles, a bend south-east, rounding out and north round the east side of the Mountains of Desolation (slightly east of the Moria marker), then north-west into the marker. Drawn as a dirt path; no rooms are mapped for it (`OWNER_PATHS` in `src/owner_edits.py`).
- Markers and traced routes for the 16 areas that open off the Southern Mountain Range and its Trade Route: Desert of Despair, Dragon's Pass, Elemental Canyon, Emerald Hills, Lamech's Abandoned Manor, MacMillan Family Farm, Mithril Hall, The Mire, Seth's Fortress, Steading of the Hill Giants, The Castle of Rol Na Feinne, The Ruins of T'man, The Von Deusen Mausoleum, The Wilds, Transylvania, Wastelands. Each sits on the range room where your directions step out (three with no directions in your list sit on the room they open from). Areas that already have a marker or are drawn (Azure Sea, Bartok Grove, Forest of Tears, Miden'nir, New Darkhaven, The Ashen Forest) and World Housing are not added again.

- Layout editor: room 6365 (Dry foothills, Desert of Despair) added, unlocked, south-east of room 181 with the spacer 19863 between them. It is not drawn on the map until you place it and save.

- Layout save of Oct 15 (00:10Z): room 6365 and its spacer 19863 are on the map, and rooms 7 to 10 (the cavern mouth, Mount Anagon and the trail east of it), 572, 109, 119, 180 to 182 and 9248 are where you moved them.

- The 7 to 8 path (cavern mouth to Mount Anagon) now winds with a few bends like the other trails (`bent_links` in `src/smr_clearings.json`).

- The gap in the land under the Miden'nir-to-Moria path is filled (ground and eight trees).
- Directions added for Lamech's Abandoned Manor, The Castle of Rol Na Feinne and The Ruins of T'man (condensed with `#N dir`); they now have traced routes. New markers with routes for Old Pottswort's Fields, Black Dagger Outlaws Hideout, The Curse of Prosperity and Dawn to Dusk (areas that open off Trade Route rooms 9249, 9315, 9320, 9321). The Old Pottswort's Fields directions stop short at their last step (`n`), so its route ends at room 9248, beside the door 9249.
- Marker names: Southern Plains, Shattered Refuge and Intrigues of the Miden'nir on the left of their dots; Lamech's Abandoned Manor and Emerald Hills to the right; Seth's Fortress centred above; The Castle of Rol Na Feinne and The Ruins of T'man to the left. The Desert of Despair marker and name moved to room 6365. A plain text label "Elemental Canyon" (not a marker) just north of room 172.
- Southern Mountain Trade Route: the road now runs exactly through rooms 9282 to 9286 (it was smoothed away from them, round the bottom of the Rough Terrain), and there are off-ramps at 9282 (to 327) and at 9285 (into the Rough Terrain, to 615 and 622).
- A farm graphic (fenced holding, three crop fields, barn, house, silo, hay, pond) centred on -26.4, 78.4 (`farms` in `src/smr_clearings.json`).

- Layout save of Oct 15 (00:48Z): rooms 9282 and 9283 moved; the Trade Route's road runs through rooms 9282 to 9286 without the spike, with off-ramps at 9282 and at 9285 (into the Rough Terrain).
- MacMillan Family Farm: the top-down farm is replaced by the usual side-view graphic, a red barn with a silo.
- Old Pottswort's Fields: your new directions (`#13 s;#2 e;#2 u;e;#3 se;d;s;#2 se;#4 s;#2 se;#2 ne;n;se`) trace cleanly; its marker sits south-east of the roadway with its name on the right.
- The Ruins of T'man: smaller marker and smaller name. The Von Deusen Mausoleum's name is centred above its marker.
- Along the path from room 72 to room 73: five small medieval homes (cottages, a longhouse, a hut, a shop, a barn-house) north and south of the road, and in the north-west spot the Forestmen's Hideout: a great gnarled tree with a tree house in its branches, a rope ladder and a log palisade round its base (side view), with a small label.

- The hamlet by room 72 to 73: the homes are now drawn in front view (timber cottage, longhouse, thatched hut, shop with awning, two-storey townhouse, stone cottage), with one more home east on both sides (3 north, 4 south).
- Forestmen's Hideout redrawn as a secret fortress: a huge dark tree with several major limbs, four wooden archery platforms with hooded archers, a plank room with glowing arrow slits, rope bridges and a ladder, a double log palisade with an iron-banded gate, torches, skulls on stakes and ground spikes, and a glint of eyes in the trunk hollow.

- Around room 9248: the Trade Route's road now runs exactly through the rooms that have an off-ramp (it was smoothed 1.3 rooms away from 9248, so the link to room 181 ended on empty ground). All the other lines there match edges in your layout; the two long diagonals are real edges (571 to 572, which you moved far south-east, and 181 through spacer 19863 to room 6365).
- The Forestmen's Hideout is 60% of its size; the MacMillan Family Farm barn is 0.3 further north.
- The links from the southern mountain rooms to the Sparse Woodlands trail are now thin dashed lines in the path colour that end on the trail itself (`smrdash`).

- The last Sparse Woodlands link (the path from room 366 to room 20002, which sits on the trail) is a thin dashed line like the others.
- The Southern Mountain Trade Route no longer has the dark semi-transparent verge and shadow round it (the other trade routes keep theirs).
- The link from room 181 to the off-ramp at 9248 is drawn whole (it was cut short at the clearing, leaving a gap).
- No sea along the west of the Southern Mountain Range, its Trade Route, or the west end of the Sparse Woodlands trail (`west_sea.py`: nothing at x -75 to -20 below y 4).

- Room 181: the path through it now runs exactly through the room (it was smoothed past it, leaving a gap before the link to 9248).
- MacMillan Family Farm barn nudged a little further north.
- The homes by the Forestmen's Hideout are now medieval: a little castle, a tower, a wooden fort, an English cottage, a rustic stone cottage with a turf roof, a Renaissance house with a stepped gable, and a fantasy tower-house.
- Selected routes that cross the Ashen Forest to the southern mountains (The Von Deusen Mausoleum and others) no longer break there: the lines now run through the Ashen rooms at the positions of your Ashen layout (they had no position in the route tracer, so it dropped them).

## Version 13 · The Forest of Tears, Lake of Tich'Pyga and Western Trade Route · October 13, 2026

- Selected routes that run along the trade routes are drawn unbroken (they were cut at the Darkhaven gate because the road rooms were missing from the old traces): `route_fix.py` traces every route again over the final layouts.
- Directions for Serpentine Coils, Drow City and Revelation City replaced with your new lists (condensed with `#N dir`).
- The Ofcol Shortcut is a portal: routes starting `#6 n;#3 nw;w;n;#4 e;s;w;sw` run to the Ofcol gate, then one long connective line to the Forgotten Woods room, and on. Their "aren't drawn yet" note is gone where no other gap remains (Valley of Mysts and The Tower of Zenothir still have a later, separate gap).
- Redrawn from the layout you saved in the editor (`src/ft_layout_final.json`): the Forest of Tears is now a field of forest ground with no rooms or paths; the Lost Between Woods, Sparse Woodlands, Alongside a Swampland and Fog Cliffs paths are dirt trails round it, with impassable dense forest between them and the field and a short band of dense forest beyond them.
- The north fills with dense forest out to a smooth coast that meets the Forgotten Woods' coast; the long Lost Between Woods path runs on to the Forgotten Woods.
- The Fog Cliffs are their own terrain: dark rock, jagged peaks, crags, drifting mist and dark fog, with the sea to the west.
- The Lake of Tich'Pyga is drawn inside the ring of its shore rooms (a dirt trail round it), with four small dirt paths to the Forgotten Woods; its name sits across it.
- The Western Trade Route is one formal road from Darkhaven to the Thalos gate, with 8 off-ramp pads where it meets Forest of Tears rooms.
- The sub-area markers inside the forest (Bartok Grove, Major Oak, The Shire, ...) and their routes follow your rooms; the Forgotten Woods trail through Widow's Peak (5634-5638) follows their new place.

- The sea now runs along the whole west coast, from the south-west of the Forest of Tears up round the Forgotten Woods, the Barren Peaks and the Northern Plains to the sea in the north.
- A small wooden shack with a dock reaching out to sea on the north-west coast at about (-94.3, -16.4).
- The Falcon's Nest Tavern drawing moved to the west side of the road, across from its marker; the long Lost Between Woods path merges into the Forgotten Woods trail along its line, and the link to the lake path joins both paths cleanly.
- A short path from the Fog Cliffs' north end (room 1661) into the field at 1648.
- Third pass: room 1891 hidden; a short link from the Lost Between Woods thread to the lake's south shore (1124 to 839); the connector from the road to Darkhaven's gate is road; the Along the Forest Path trail now leaves the Darkhaven path at room 820; a new off-ramp pad at room 2319; the field is one terrain (the different strip between x -49 and -40 is gone).
- Second pass from your new save: the path west out of Darkhaven stops at room 822 where the field begins; short dirt links run from the Lost Between Woods path into the field at 1754 and 1736; the Western Trade Route near Darkhaven follows the rooms you moved.

## Earlier in progress · Southern Mountain Range
- Southern Mountain Range, its Southern Mountain Trade Route and the moved Sparse Woodlands trail are on the map from your saved layout: wide paths and clearings follow your rooms (neighbouring rooms widen the path; a clump of touching rooms is one open dirt patch), the Trade Route is a formal road with off-ramps, the Forest of Tears redrawn round the moved trail, sea along the range's west coast, the map now reaches y 113.
- New layout editor for the Southern Mountain Range (597 rooms + 99 spacers, anchored to the Forest of Tears); nothing drawn on the map yet.
- Edel has a grand paved road and a town gate where room 134 joins it to the cartyard; the Shattered Refuge cabins and path moved east beside its dot; the trail through rooms 588-590 is back; room 558's path shows; the path 593-591 shows faintly inside Rough Terrain; room 19997 joins its clearing; Suds 'n Stones is an inn with a label at room 9303.
- Edel is drawn as a small top-down village (streets, plaza and well, church, inn, houses) in its box, with its name; the climb is a plain wide path with faint stair steps; the river south of Darkhaven ends further east and curves north into a thread; Shattered Refuge's paths are gone and its name sits beside its dot; the Southern Mountain Range marker, name and sidebar entry are removed.
- Paths stop at the edge of any clearing they run into (they only show that the path leads in); Rough Terrain shows its inner paths faintly with crags and boulders; a rocky climb joins rooms 153/152 to 150/149; clearings extended: canyon-rim strip (rooms 681 ... 365), 686, 310, 167, 174, 157.
- Rough Terrain (-26.5,11.5 to -16.4,17.5) is one dirt clearing, only the Sparse Woodlands trail paths into it are drawn; room 157 joins the clearing south of it. Hand-made clearings are listed in `src/smr_clearings.json`.
- 'Along the Forest Path': trail removed, marker moved to the end of its directions (the Southern Trail room, -22.4, 2.0).
- Southern Mountain Trade Route off-ramps all sit on the drawn road.
- Up/down exits between shown rooms are drawn as small dirt lines (11), except 291 - 292.
- The visual-only connection from room 559 up to Ashen Forest room 670 is on the map: a standard dirt path through standard forest (the Ashen trail follows 670 to its new spot).
- Editor: the Sparse Woodlands trail of the Forest of Tears (38 rooms incl. spacers) unlocked; the Southern Mountain Trade Route (126 rooms) added.

## Earlier in progress · Forest of Tears + Lake of Tich'Pyga editor
- New layout editor for the Forest of Tears (683 rooms) and the Lake of Tich'Pyga (276 rooms) together, with the spacer rooms that join them (`tools/forest_of_tears_editor`, October 12). Nothing on the map changes until you save an arrangement.
- The 53 Western Trade Route rooms in that editor are unlocked (movable).
- Forgotten Woods rooms 5634-5638 are unlocked in that editor too.

## Version 12 · The Azure Sea Coast and the Village of Edo · October 12, 2026
- New layout editor for the Azure Sea rooms that join the map (`tools/azure_sea_editor`, October 12): 49 rooms in the end (under the Barren Peaks cliffs, the shore walk to the Ashen beach, the coast north to the Plains, the path to the Village of Edo, and spacers 14314 and 22557).
- The Azure Sea Coast is on the map (October 12), from the layout saved in the editor: a dark blue water route along the foot of the cliffs, from room 14265 north round the Plains to 7746.
- At its south end, 14257 to 14265 is a small stream winding over the land, a little wider than a path; the land there is unchanged.
- Open sea east of the mainland, from the coast out past the route (about 8 rooms beyond it), 3,320 sq rooms; only 14 sq of land cut back where the route lay on it (no new land).
- A cliff edge (dark band and hachures) all along the coast that faces the new sea.
- The links of the five hidden rooms (14273, 14275, 14278, 14279, 14287) are small dashed lines (15); the shown rooms' links to the mainland are ordinary trails (6, two of them 42-43 rooms long, from 14271 and 14272 to the Peaks).
- A Village of Edo marker at 7746, with your directions traced on its card (the line joins straight across 5965, which is not in the editor).
- The Azure Sea Coast's links to the mainland are now all small dashed lines (8, including those from the hidden rooms 14278 and 14279); no solid trails, and the hidden rooms' other links are no longer drawn.
- Every destination whose directions go through the painting (13: the Plains areas, the Village of Edo, and Village of Tar'pa Cithm, Mountain of Lost Souls and Morgul Vale in the Peaks) now shows one unbroken route line from Alms for the Poor to the Northern Plains; the three Peaks routes are now traced across the Plains too, and lose their "areas that aren't drawn yet" note.
- The sea now runs along the whole north coast of the Northern Plains, joining the north-west sea to the Azure Sea (452 sq rooms added).
- The small bay just north of Ocean Keep is now part of the Azure Sea (35 sq rooms).
- The name "Azure Sea Coastal Path" on the water beside the route's long north-east stretch, north-east of the City of Iniquity (map only: no card or sidebar entry).
- A small island (about 8.6 sq rooms) just north of the Village of Edo marker.
- The sea continues south down the Ashen Forest's east coast (about 9 rooms out from the shore, 599 sq rooms), fading out round the south-east corner; it replaces the old pale shallows there, so the sea is one body and looks the same everywhere. The beach is unchanged.
- The Azure Sea Coastal Path is now a dark navy line, darker than the sea (it was a bright blue that stood out too much).
- The stream at the south end of the Azure Sea Coastal Path (by Ocean Keep) is now the same dark navy as the rest of the path.
- The "Azure Sea Coastal Path" name is a little bigger (size 1.25, was 1.0).
- The Z'hyal marker and its sidebar entry are removed.
- Legend: "Entrance to a place" is now "Area", the off-ramp entry is now "Trade Route Entrance/Exit", and "Guild", "Landmark" and "Town gate" are removed.
- Fixed: zoomed in, the map could show old pictures from before the latest change (the new coast vanished on zooming in); each build's pictures now have their own address.

## Version 11 · The Northern Plains and the areas that open off it · October 12, 2026
- New layout editor for the Northern Plains (`tools/northern_plains_editor`, October 10): 474 Plains rooms and 134 spacer rooms, movable in 13 pieces (595, 2, 1, 1 and 9 rooms with no exits), starting where TinTin's exits put them, north of and over the top of the Barren Peaks; the 75 rooms of the Northern Trade Route past the long bridge are movable too and start where they are on the map; everything else on the map, including the Barren Peaks as arranged, is shown as fixed dots. The map itself is unchanged until the layout is merged.
- Spacer rooms 4216, 4219 and 4382 (between road rooms 4213 and 4214) can now be moved in the Northern Plains editor, with the road; 78 movable road rooms.
- In the Northern Plains editor, the Northern Trade Route inside the Barren Peaks (4136–4155) is fixed again; only its 58 rooms in the Plains (from 4156) move, drawn on top of the Plains rooms so they can be grabbed. Spacer rooms 4216, 4219 and 4382 can now actually be picked up one at a time (bigger grab area; 4219 was under a Plains room).
- Plains rooms 4363, 4417 and 4515 and the five spacer rooms joined to them are left out of the Northern Plains editor, so they will not be on the map.
- The Northern Plains are on the map (October 11), from the layout saved in the editor: a wide wheat-coloured field north of the Barren Peaks with paler and grassier stretches, grass tufts and low brush, and no paths across the open field. Paths are drawn only where you asked: the Northern Trade Route (as before, now where you placed it in the Plains), every link between the Plains and the Barren Peaks, and the seven linear paths you listed (the western one up to its two exits back into the field). The Peaks' brown ground stops where the wheat begins.
- The ground between the Plains' open field and the Barren Peaks is now an overgrown, impassable thicket of trees, rocks, brush and tall grass, so it is clear the only ways through are the southern paths; about one room of clear ground is left beside every path, the road and every room.
- Off-ramp pads on the Northern Trade Route wherever it has an exit into the Plains (11). The thicket is now dark brown and beige with bare trees, like the Barren Peaks' ground. The north-west corner between the Dark Cliffs / Grey Dunes path and the field is impassable: rocky crags by the Dark Cliffs, grey dunes by the Grey Dunes and Beach. A drawing of The Barrow Mound, and groves of trees where the rooms are named The Fringe of Trees and Tall Trees. The tangle of links along the Barren Peaks is now one wide dirt road, with a single short spur to each Peaks room it joins.
- Some Barren Peaks rooms near the Plains (7188–7220) and the canyon road (4152–4155) can be moved in the Northern Plains editor; the map rebuilt from the new Northern Plains layout (October 11).
- October 12: the thicket now reaches north to about one room from the field's rooms, and the place where each southern path leaves the field is kept clear, so the westernmost path is plainly reachable from the field. The wide dirt road along the Barren Peaks now stands for all the little Peaks trails beside it (no spurs, no trails running alongside it, no one-room stubs); trails that lead deeper into the Peaks start from the road. Beyond the north-west path (the Grey Beach, Grey Dunes and Dark Cliffs) the land is now sea out to the edge of the map, with a strip of beach. Markers for the 12 areas that open off the Plains (Azure Sea, Crystalmir Lake, From the Stars, Opallinoc, Temple of the Moon, The Blood Sea, The City of Iniquity, The Dunhill Demesnes, The Island of Irrybis, Town of Solace, Unholy Grounds, Valley of the Elves), with your directions on their cards where your list has them. The name "Northern Plains" in the open field. The dark mountain moved next to the Mountain of Lost Souls marker.
- Later on October 12: the "Northern Plains" name centred between the Northern Trade Route and the west coast; The Blood Sea marker removed; all of the impassable ground in the north-west is now grey dunes; Crystalmir Lake's name to the right of its marker and The Dunhill Demesnes' name centred below its marker; a city drawing just north of the Town of Solace marker, with the land extended round it.
- Later still on October 12: dunes fill the gap west of Opallinoc, so there is clearly no way west from it to the coastal path; a watery path runs a short way north out to sea from the north-west corner of the Plains (room 4405; 4407 is hidden in your layout), named "Otherland"; the little bay east of From the Stars is gone and the sea narrows smoothly to a point there; a few small gravestones just south of Unholy Grounds, with the land extended round them.
- The north coast now runs close along the top of the Town of Solace drawing, so there is no ground to walk round the town to the north.
- The stray patch of thicket north of the eastern path (above the row of rooms where it meets the field) removed. Your directions added to the list for The City of Iniquity and The Island of Irrybis; their cards now trace the route. Unholy Grounds' directions (through the painting) were already in the list.
- The painting in Alms for the Poor is a portal straight to the Northern Plains, so the cards for the areas off the Plains no longer warn that the route passes through undrawn areas. Unholy Grounds (where the painting sets you down) now shows your directions and traces the route.

## Version 10 · The Barren Peaks of Tahjliera and the areas that open off it · October 10, 2026
- The Barren Peaks are on the map (October 10), from the layout saved in the editor: new land to the north of the Forgotten Woods covered in mountains, the Peaks' own paths as dirt trails, and the Northern Trade Route carried on past the long bridge as the same formal road. Rooms hidden in the editor, up/down exits and spacer rooms that lead nowhere are left off. The bridge sits where it was placed in the editor. Published in the working map and the tiled preview.
- Later on October 10: two maze outlines (Valley of Mists Maze; Where Power & Sorcery Collide Maze); the climb between Ancient Ladders and The Treacherous Climb drawn as a trail; the Peaks repainted as brown dirt with clusters of boulders instead of mountain icons; markers for the 14 areas that open off the Peaks; and the sea brought right up to the coastal paths on the west (from 7061 north to 7078) and east (from 6925 north to 7286), with a strip of beach.
- Later still on October 10: the coasts turned the right way round (sea only along the two coastal paths; elsewhere the land carries on off the map); Asgard Nexus renamed Z'hyal; both mazes drawn as dark grey mist; Drow City, Reign of Madness, The Slime Pit and The Crimson Caverns markers moved (Crimson Caverns now has directions); World Housing removed; a Tower of Enlightenment marker in the Forgotten Woods; the trail from 7125 to the spacer room by the Slime Pit; and two map-only names, The Lost City of Tahjliera and The Keep of the Huitz.
- Then: the coastline changes undone (the Barren Peaks keep their own natural edge again, with no sea cut into them and no land beyond them), and the two mazes redrawn as maze blobs like the Forgotten Woods' ones, but dark and ominous.
- The two dark mazes now sit over the paths and hide them; their names, and Z'hyal's marker, show on top.
- Small drawings added: a keep beside Barrik's Keep, a palisade village of sharpened poles under the Village of Tar'pa Cithm, stone cities above Drow City and Revelation City (whose name now sits to the left of its marker), and a crumbling stone building below The Slime Pit.
- Ofcol is now called New Ofcol (the Forgotten Woods' New Ofcol marker keeps its name too).
- The Forgotten Woods' New Ofcol marker removed; the Sorcery maze's name moved below it; the Tar'pa Cithm village drawing moved beside the village (clear of its name), Revelation City's drawing moved above its name, the Slime Pit's ruin moved; room 7213 moved north with its path.
- The Slime Pit's ruin moved clear of its marker; Revelation City's drawing brought down closer to its name; Mountain of Lost Souls' name moved to the west of its marker; a big dark mountain drawn beside it; paths joined between 6652 and 18145 and through 5570, 5571 and 5772; and the area name "Barren Peaks of Tahjliera" added, in the same style as the Ashen Forest's.
- New layout editor for the Barren Peaks of Tahjliera (`tools/barren_peaks_editor`): 528 Peaks rooms, the 72 rooms of the Northern Trade Route past the long bridge and 38 spacer rooms, movable in 7 pieces (581, 44, 9 and 4 single rooms), with up/down levels marked; every room already on the map, including the Northern Trade Route up to the bridge, shown as a fixed dot. The map itself is unchanged until the layout is merged.
- The three rooms of the long bridge (4133–4135) can now be moved in the Barren Peaks editor.
- Room 7058 (The Barrier) and its exits are left out of the Barren Peaks, so it will not be on the map.

## v9 · The Northern Trade Route and its sub-areas, the new west coast and Ocean Keep's bay · October 9, 2026
- The Northern Trade Route is on the map from the layout you arranged in the new editor: from the gate beside Darkhaven's north gate, through the Shadow Grove and across the Forgotten Woods to the long bridge at the Woods' north coast (54 road rooms; the road past the bridge, in the Barren Peaks and the Northern Plains, is not mapped). It is drawn as one continuous formal road, in the same style as the Eastern Trade Route, over the top of the Maze of Trees (whose name moves clear of it). Short dead-end spurs (spacer rooms leading to areas that are not mapped) are left off so nothing looks like a loose piece of road.
- Every road is now drawn layer by layer across all its stretches, so there are no seams where stretches meet. The legend reads "Road (Trade Routes)".
- Off-ramps: a small round junction pad is set into the road wherever it joins a path in the Forgotten Woods or the Shadow Grove (10 pads), and wherever a link to a sub-area leaves it (3 more). The legend explains them.
- Sub-areas off the road: the City of Salburg (the same walled-town emblem as Ofcol, in forest east of the Maze of Trees, reached by a curved path from an off-ramp), the Keep of Belial (a medieval keep tower at the end of the spacer-room stub below the road) and the Wolf's Den, each with a marker, a short link, and your directions on its card. Troll Den is not connected to the road (its only exit is to the Ashen Forest).
- The coast: it comes straight down from the Forgotten Woods' north-east coast past Salburg (the old indent in the coast is filled with forest) and curves in to a small rounded bay, with Ocean Keep on the water at its south end; the shallow water follows it. On the west, a new smooth coast runs from the Woods' westernmost edge down to the middle of the Forest of Tears, with forest filling the open water between, so no path runs out over the sea and the Western Trade Route has land on both sides.
- Drawings and labels: a keep tower (Belial), a small inn on the Ashen Forest Inn with its label, a castle (King's Castle), a windmill, and a town (Ocean Keep); "Ashen / Forest" stacked and gently arched in the open ground north of Shai'ghool; the darker ground at Shai'ghool and Shadar Logoth kept close to the markers; Tullfuhrzky Manor and Ofcol moved a little west clear of the road; The Hermit's Hut removed.
- New layout editor (`tools/northern_trade_route_editor`): the 1,089 rooms already on the map in Darkhaven, the Grove and the Woods shown as fixed dots, with the road's rooms as the movable ones. New build modules: `ntr_merge.py`, `ntr_marker_routes.py`, `ntr_markers.py`, `west_coast.py`, `bay.py`; `fot_extract.py` now tracks every Darkhaven, Grove and Woods room to its final position.

## v8 · The Ashen Forest and the Eastern Trade Route, markers and drawings · October 8, 2026
- The Ashen Forest and the Eastern Trade Route are on the map, east of Darkhaven, from the layout you arranged in the layout editor (431 rooms: 317 forest rooms, 81 Trade Route rooms with their spacer rooms, the King's Castle room, 14 rooms from Ocean Keep and the Azure Sea, and 18 fixed rooms in Darkhaven, the Shadow Grove and the Forgotten Woods). The two piles of stacked rooms and the underground burrows are left out. Ground, grey ash tint and trees are painted around every room; the little white trees were removed.
- Trails are drawn between every two rooms that are both shown. The 132 rooms you hid get ground but no trails. Trails start and stop exactly on the fixed rooms so every junction joins.
- The Eastern Trade Route is a formal road: wide, paved, with stone curbs, a worn middle line and a cleared verge, in the legend as "Road (Eastern Trade Route)". Trails where it meets the forest stay dirt.
- Darkhaven's east road runs straight out of the Darkpass gate to the Cross Roads, and a path runs southeast from the Cross Roads to "Paths Diverge at the Edge of the Trees", joining the forest's path there.
- The far east is a beach and the ocean: the forest thins, a sand strip runs along the shore (your north-south paths lie on it), and the land becomes water about midway along each east-west dead-end path. A pale shallows wash follows the coast, round the north-east corner to Ocean Keep, where a small headland carries the village.
- Markers (13 new, each at the room where your directions step out of the forest or road): King's Castle, Mountains of Desolation, Shai'ghool, Shadar Logoth, Troll Den, Ocean Keep, Glimwinkle's Windmill, White Pine Camp, Moria (one entry only; the Miden'nir one was removed), City of Eldestra, Land of the Fire Newts and Machine Dreams (they share one dot at room 1255), Fire Station (inside White Pine Camp), and the Eastern Trade Route entrance. Names beside Troll Den, White Pine Camp, Fire Station, Moria, the Fire Newts, Machine Dreams, King's Castle, Glimwinkle's Windmill, Ocean Keep and the Trade Route entrance are placed by hand.
- Drawings: a castle above the King's Castle name, a windmill above the Glimwinkle's Windmill name, a town above the Ocean Keep marker, and an inn on the Ashen Forest Inn (vnum 2991) with a small label in the same style as "A Mysterious Inn". The ring of road round the inn is drawn half a room wider north and south so the inn fits between the roads.
- The ground around Shai'ghool and Shadar Logoth is a little darker, with a few more dark trees, kept close to the markers. The Hermit's Hut is off the map.
- New layout editor (`tools/ashen_forest_editor`): rooms start in TinTin's own shape; hide rooms from the map (H), lock rooms, select a whole area, send rooms to where TinTin's exits suggest; shows an import check against the map file.
- New build modules: `ashen_forest.py`, `visual_nudges.py`, `af_marker_routes.py`, `af_markers.py`, `dh_paths.py`, `east_shore.py`, `scenery.py`. The map drawing area now reaches east to x = 96 (it stopped at 66), and trails pin to fixed rooms.

## v7 · Lake Tich, the forest moved west, bigger names, search · October 7, 2026
- Lake Tich ("Lake of Tich'Pyga") is now a big lake. The old lake, the pond by Keep of Lomar and the bay between the Forest of Tears and the Forgotten Woods are one body of water. Its north shore sits at the bottom of the Lost in the Swamp maze, its north-east shore runs along the Woods trail and bulges toward Tullfuhrzky Manor, and its south-west shore is a natural, nearly straight line from Ezard's Fields toward a south-east tip. It stays about 3 rooms from the Western Trade Route. The west end of the bay is closed with a strip of woodland. Its name is set large across the middle.
- The Forest of Tears is stretched east-west (about as wide as the Forgotten Woods), and the forest was moved west by half the town's width (6.6 rooms), leaving a buffer next to Darkhaven. These moves came from an arrangement made in the new map arranger (`src/build_arranger.py`, `src/arranger.js`); the saved arrangement is `src/arrangement_1.json`.
- The gaps those moves left are filled: lake water, or the same forest and grassland as the ground around them (tints, trees and grass). The gaps are beside Keep of Lomar and Ofcol, between the lake and Darkhaven, and between Along the Forest Path and the forest.
- Falcon's Nest Tavern: the Falcon's Talon and Jelarid's Track Shoppe are removed, and the trade route sweeps around the tavern in a wide arc instead of turning sharply.
- The Forgotten Woods title moved to the open forest above Dobra, and the Forest of Tears title moved into the middle of the pines and set in the same size.
- Marker names outside the town are 50% larger, and the page places each one so it does not overlap another name, a marker, a title or a trail.
- Sidebar: one alphabetical list of areas, then one of mobs, with a search box (it filters as you type, Enter opens the first match, Escape clears).
- New build modules: `lake_reshape.py`, `partition.py`, `arrange_apply.py`, `gap_fill.py`, `label_tweaks.py`.

## v6 · your directions on every card, trade route tidied · October 7, 2026
- Directions for the places that had none, as you gave them (condensed to numbered quantities): Notre Dame de Sioux, Sonoria, the three guilds, V'laresch, Falcon's Nest Tavern, Darkhaven Marina, Blackcoggle Manor, The Grimdog Port Authority, the Northern Trade Route and Gnarlwood Forest. Old Thalos shows your second route under "Another way". They are stored in `directions.py` (MORE_DIRECTIONS and ALT_DIRECTIONS).
- Every information box now shows only directions that came from you. Castle Darkhawk is the one place still waiting for directions, and its box says so.
- Guilds corrected to your final directions: Spirit `nw;w;n`, Nature `#3 s;e;s`, Origin `#2 ne;e;ne;nw`.
- The extra "Thalos" marker removed; only Old Thalos is on the map.
- Western Trade Route: drawn in full to its end (a fade-out that had moved out of place after the scaling is gone), the sharp corner just north of the Falcon's Nest Tavern rounded off (the tavern building nudged one room south to make room), and the road cut where it passes the V'laresch marker.
- New build helper `apply_directions.py`, which attaches your directions to the town markers by where they lead.

## v5 · + Shadow Grove, Forgotten Woods and the Lake · October 7, 2026
- The Shadow Grove, north of Darkhaven: dusky fields and low hills wrapped around the town, with The Hermit's Hut and the trail north out of Darktrail. Area markers for Wendle Mansion, Ofcol, Keep of Lomar, Tullfuhrzky Manor, Green Forest, the Northern Trade Route (at the north gate), The Ashen Forest and the link to the Forgotten Woods.
- The Lake of Tich'Pyga drawn larger, with a single marker and its name running along the water.
- The Forgotten Woods, laid out by hand in the layout editor (593 rooms) and placed north of the Shadow Grove where the trail from Darktrail enters them. Terrain painted from each room's terrain type. Every real exit between walkable rooms drawn as a soft dirt trail. The Maze of Trees, Lost in the Swamp and The Hidden Grove drawn as maze areas.
- Forgotten Woods markers: Pixie Forest, Nevermore, Corruption of Anciastra, Vale of Nidaros, Valley of Mysts, The Tower of Zenothir, Wyvern's Tower, La Chute D'eau De L'ancients, Raven Tor, New Ofcol, Gnarlwood Forest, Keep of Mahn-Tor (Ogre Village) and Reomyr Village; mobs Dobra and Catobeplas.
- Information boxes now show only directions that came from you (your original lists and the ones you typed in chat). Traced route lines follow those directions step by step, with breaks where they pass through areas that aren't drawn yet. 14 places with no directions from you say so: Castle Darkhawk, Notre Dame de Sioux, Sonoria, Guilds of Origin, Spirit and Nature, V'laresch, Falcon's Nest Tavern, Darkhaven Marina, Blackcoggle Manor, Thalos, The Grimdog Port Authority, the Northern Trade Route and Gnarlwood Forest.
- The Forgotten Woods scaled down 20% and the Forest of Tears scaled up 20%, each as a whole, so they are closer in size. Everything inside each area keeps its exact arrangement.
- Ofcol marked as a town, with a walled-town emblem about 2.5 rooms wide, and a "Town or city" entry in the legend. Gallow Hill removed.
- The map's land extends further north and east to hold the Woods.
- Included in this bundle (tools folder): the Forgotten Woods layout editor and the layout you saved from it.

## v4 · + Miden'nir and the south · October 6, 2026
- Miden'nir, across the rusted bridge below Darkwall: the Black Forest (darkest at its heart), the Mysterious Inn, the bramble thicket to the east and Mount Doom with its cave mouth to the south.
- Areas off Miden'nir: Intrigues of the Miden'nir, Shattered Refuge, Southern Plains (say "story" at Jed's Desk), Moria (through the brambles) and the Southern Mountain Range (up from Gazing Upon Mount Doom).
- The gap southwest of Darkhaven filled: Along the Forest Path as an approximate patch of woodland with its massive tree, between the Forest of Tears and the Shattered Refuge; the Refuge's labs and homes with their tracks, running east into the Black Forest. The forest, the town and Miden'nir are now one landmass.
- South of the walls: the old path from the Precarious Bridge past the Elm Tree and over the Crumbling Bridge into Miden'nir, drawn as a faint track; the river's western stretch moved slightly south to match its rooms.
- The Darkhaven Marina: a boathouse and pier on the river, with a town landmark.
- Clean-ups: no boats or stray graphics on the river; Shattered Refuge's label sits over its village; the Refuge's south road ends among its homes.

## v3 · + Western Trade Route · October 6, 2026
- The Western Trade Route drawn as a rough, rutted track winding through the Forest of Tears: from Darkguard's southwest exit past the village near Bartok Grove and Major Oak, north over the bridges, out across the northern country past the tavern, then back south through the groves, fading out toward Thalos. Its northern loop is set just north of the Lost Between Woods path.
- A small village of three log buildings on the route: the Falcon's Nest Tavern (with a map landmark, from your `fal` landmark), The Falcon's Talon and Jelarid's Track Shoppe.
- Places opening off the route: Blackcoggle Manor, Ezard's Fields, The Grimdog Port Authority, Haven of Everlasting Light, Old Thalos and Thalos.
- Major Oak and Bartok Grove now pinned where they open off the trade route, which is how your directions reach them.
- The Lost Between Woods path corrected: its eastern stretch rejoins the forest a few rooms east of V'laresch; a separate western stretch rejoins at Path to the Cliffs.
- The road from Darkguard now stops where the forest begins.
- Bare ground in the forest (stretches made only of spacer rooms) filled with light woodland.
- Markers near Florebit, Haven of Everlasting Light, Old Thalos and V'laresch nudged apart so no labels overlap; Guild of Origin label lifted clear of Notre Dame de Sioux.
- Water only where the rooms are water: the stray pools from "Deep Waters" and "West of Silver Lake" removed.

## v2 · New Darkhaven + Forest of Tears · October 6, 2026
- The whole map is now drawn in a hand-painted style, generated from each area's terrain and room names.
- New Darkhaven redrawn to match: rough stone walls and towers, gatehouses, cobbled streets, groves and a paved square; Castle Darkhawk shown as a single small keep; Notre Dame de Sioux as a cathedral. All streets, structures, routes and markers from v1 kept.
- The trail circling Darkhaven outside the walls, joined to each gate.
- The road west from Darkguard into the Forest of Tears, fading into the trees.
- The Forest of Tears: deep woods, lighter woods, bogs, Silver Lake and pools, the Fog Cliffs (with mist only over the Fog Cliffs rooms).
- Town and forest joined as one landmass, with open meadow around the walls.
- The Lost Between Woods path along the north edge, set apart by a line of dark trees and fog: the eastern stretch from Silver Lake rejoins the forest a few rooms east of V'laresch; a separate western stretch rejoins at Path to the Cliffs.
- Forest of Tears sub-areas: Along the Forest Path, Bartok Grove, D'Morian's Lands, Florebit in Immortalis Iuvenis, The Graveyard, Kontaur, Lake of Tich'Pyga, Major Oak, The Sentinel, The Shire, Silvermoon Outpost, Tree of Life, Treetops and Canopy.
- Forest of Tears landmark: V'laresch (room 2090, in the Asgard Nexus).

## v1 · New Darkhaven · October 6, 2026
First snapshot of the map built from the TinTin++ map file.

- The walled town of New Darkhaven: walls, corner towers, the four gates (Darktrail, Darkpass, Darkwall, Darkguard), all streets including Thieves Alley and Park Avenue, and Darkhaven Square.
- Areas in the New Darkhaven geo: Darkhaven Art Gallery, Dragon Cult, Warehouse, Halls of Knowledge, and (inside the Halls) Isle of the Monkeys and A Moment in Nature.
- Landmarks: Castle Darkhawk (room 12550) and Notre Dame de Sioux (room 780).
- Guilds: Origin, Spirit and Nature.
- Mob: Sonoria (room 1310, the Altar to Thoric).
- Footpaths to Spirit, Origin, Castle Darkhawk, Notre Dame and Sonoria.
- Click any place for full directions from Darkhaven Square, traced room by room through the TinTin map.
