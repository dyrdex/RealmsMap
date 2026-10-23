# Realm map: working notes (loaded every session; keep this file short)

Interactive dark-mode map of the MUD "Disgruntled Realms", from the owner's TinTin++ map (`src/world`). Leaflet site on GitHub Pages.

## Build, review, deploy
- `cd src && python3 build.py`: frozen map `src/base/map.json` + change files `src/changes/NNN_*.py` (applied in order) ->
  `realm_map.html` (~0.2 s) -> WebP tiles + `site/` (~50 s; `NO_TILES=1` skips). `FINAL_DUMP=<file>` writes the map data (editors).
- `realm_map.html` is committed as the reference: `git diff --stat realm_map.html` after each build; it changes only when meant.
- Build outputs not committed: `site/`, `realm_map_preview.html`, `.tile_cache/`, `src/legacy/nd2.json`, `src/legacy/fot.json`.
- Actions (`.github/workflows/pages.yml`) builds and deploys on every push to `main` or `claude/**`. The owner reviews on Pages.
- `src/legacy/`: the old region-by-region pipeline (`python3 legacy/build_legacy.py`, ~2 min, reproduces the base exactly). Use it
  only to redraw a whole region from its old code; otherwise never touch it.

## Where things are
- `src/changes/README.md`: how to write a change. `src/maplib.py`: `world()`, `tracer(pos, wild)`, `condense(route)`, `warpline(line)` (every new non-C water path).
- `src/template.html`: draws the map (layers, sprites, labels). `src/site_template.html`: the live page. `src/data.py`: owner's
  areas + directions. `src/VERSION`: footer label.
- `docs/REGION_NOTES.md`: data layout of the base, editor links, standing owner rules per region (read the part you need).
  `docs/archive/`: full history (grep it, don't read it whole). `CHANGELOG.md`: owner-facing history (append to the top section).

## State (Oct 23, 2026)
- Last version 2.10 (Oct 23, "The Ashen Shore"; tag `v2.10` to be added by the owner on GitHub; 2.9 "Open Seas"). Base = a legacy redraw + `applied/v22/`, `v23/`, `v24/`,
  `v2.2/` ... `v2.10/` (2.4: Otherland from the owner's save, `legacy/ol_layout_final.json`, now the save of Oct 23 00:19Z; 2.5: Otherland's wilds;
  2.6: the Azure Sea east coast (coast, sea, routes, cliff + climbs, iceberg 15154) and the Fissure as clefts down to the gorge floor;
  2.7: Otherland's mountains (Morte's Peak, Zenith of the Gods; terraces from above), even plants/drifts, east routes redrawn, north sea edge;
  2.8: Winterlight Island re-fitted, Otherland's sub-areas + mobs (South/North routes), the Ziggurat rooms, the Ahtborne gap rooms; Wastelands save Oct 23 01:00Z).
  Saves since Oct 22 18:39Z have the west/south 3 east: applied v2.4/001 `WS`. Details and standing rules: REGION_NOTES (Otherland).
  After a legacy redraw or a new Otherland save: `BASE_DUMP=<f> NO_TILES=1 python3 legacy/build_legacy.py`, then `python3 legacy/rebase.py <f> base/map.json`;
  then keep the sprites outside the changed area (as applied/v2.8/003) and check sea lost (as v2.8/005).
- All 15 layout editors live in the owner's current organization (links in REGION_NOTES). Read saves with ArtifactData get `<key>/current`.
  Hidden/route-only rooms added via `tools/forest_of_tears_editor/add_*.py`; Azure Sea rooms via `tools/otherland_editor/add_azure_east.py`;
  Oct 23 rooms via `tools/otherland_editor/add_sub_areas.py`, `tools/wastelands_editor/add_ahtborne_gap.py`, `tools/ashen_forest_editor/add_azure_beach.py` (65 Azure Sea beach rooms, area 'AZ'; drawn from the save of Oct 23 14:30Z by `applied/v2.10/001`) (new editor rooms also go into `legacy/*_editor_edges.json` when saved).
- In progress (2.11): `changes/001` the Azure Sea Coast path redrawn from the owner's save of Oct 23 16:48Z (26 rooms added via `tools/azure_sea_editor/add_coast_rooms.py`); only path lines/dashes/label + the Ocean Keep stream changed (owner: never the mainland). 2.10 (`applied/v2.10/001`): the Ashen far east beach from the owner's Ashen save of Oct 23 14:30Z (only moved/new rooms; sea pushed east, smooth coast, south corner cut; clearing 3201/3202/3205/3206; template ASHBEACH).
- 2.9 (`applied/v2.9/`, files 001-020): `changes/001` all type A water routes (seaways) drawn as B (seawaysfaint); `002` DD east coast primary path 12984-12993 + 15098, 15108, 15097, 6300 as B, Otherland trail warp; `003` its other 27 routes as C (olharborways); `004` Coral Depths' 5 land links as C; template SEACUR thinner, opacity .4; `005` the Ocean Keep stream as B; `006` the standard water path bend (`maplib.warpline`) on all B routes + currents; `007` Tunnel in the Snow Maze label, Over the Cliff Maze's west bulge; `008` frame widened, `009` sea fills all open background (geo.water rewritten), `010` sea names + Otherland name; `011` places Otherland (Northern)/(Southern) (places live in the map data, added by change files; data.py is only the old list); `012` Over the Cliff label bigger/centred, Edo's new route; 009 also cuts shore lines out at sea; `013` Otherland link sprites (waterway at 15606 aiming south, gfx h<0 = mirrored; seaholes 5967/5970). Text widths: measure once (fontTools needs brotli, not in CI), hard-code. `014` Azure Sea place removed; `015` 22557/14314 straightened (NP editor save v5 + legacy np save updated); `016` NP 'Otherland' waterway + label removed; `017` route jumps (dashed arc; owner's list only); `018` Tower of Enlightenment's new route (Ofcol joined).; `019` Dobra retraced (spacers followed by their other exit), Catobeplas joined at Ofcol; `020` Over the Cliff Maze shrunk (paths cut); (a map frame was tried and removed at the owner's request, Oct 23: none).

## Snapshots
- Version numbers (owner, Oct 21): restarted at the map's revamp (the old count, v20-v24, is kept in the CHANGELOG); this release is 2.10, the next is 2.11
  (footer `Version 2.11 · <title> · <date>`, tag `v2.11`, folder `applied/v2.11/`; add the folder to `legacy/rebase.py`; change files that read
  `legacy/` need their path one level deeper once moved).
- New version: `python3 build.py --freeze`, move the change files to `src/changes/applied/v2.N/`, edit `src/VERSION`, retitle the CHANGELOG's in-progress
  section, rebuild twice (realm_map.html must match), commit.
- Merge into `main` ONLY when the owner says to save a new version (Oct 16). Day to day: push to the session branch only. Then
  open a PR to `main`, merge it, and remind the owner: GitHub -> Releases -> Draft a new release -> tag `v2.N` -> Target `main` ->
  title + notes from the CHANGELOG -> Publish. (Cloud sessions can't push tags.)

## Conventions (owner preferences)
- Dark mode only: no light palette, no `prefers-color-scheme`, no theme toggle.
- Never add graphics, labels or markers the owner didn't ask for. Do exactly what's asked and report numbers.
- Big area names: italic, size 2.4, letter-spacing .55, pale halo, gentle arc. Small labels: italic .38, soft grey, pale halo.
- Directions always in numbered form ('#6 s'); convert every set the owner gives (`maplib.condense`; build.py condenses all).
- Rooms the owner asks to add go into a layout editor ONLY; drawn after the owner places them and saves (Oct 18).
- A change touches only what was asked: draw new random sprites with their own `random.Random`, so nothing else moves.

## Gotchas
1. Never fill open water without a bounding box. After any coast/land change, diff land against the base and list new pieces.
2. A land change must also clip ground tints and clear trees/tufts in the cut area.
3. A route's marker goes where the route leaves the area, not at the end of the drawn rooms.
4. Roads are drawn layer by layer across ALL segments, or joints show seams. Lists like `wild['gfx']` are appended to.
5. Check placements numerically (distance to road/water, overlaps with names) before any screenshot; the site's label spots can
   differ from `realm_map.html`'s: check against `site/data/<stamp>/places.json`. Fonts come from `src/fonts/`.
6. The label solver flags 11 hand-placed names as "touching": expected baseline.
7. Leaflet snaps to whole zoom levels (zoomSnap 1). Tiles/data live under `site/tiles/<stamp>/`, `site/data/<stamp>/`.

## Working rules (save credits)
- Read this file; open other docs only for the part needed. Don't search old chats.
- Batch the owner's requests into one build; verify with numbers; at most one screenshot per set of changes.
- Never send images or files into the chat (Oct 18; repeated Oct 22): opening an image with Read shows it in the chat too, so verify with
  numbers and avoid screenshots; take one only when numbers can't settle it.
- Ask before work outside the agreed plan.
- After each batch: one line per change in CHANGELOG (owner-facing), a short rule in REGION_NOTES if it should hold later,
  update "State" above.
