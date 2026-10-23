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
- `src/changes/README.md`: how to write a change. `src/maplib.py`: `world()`, `tracer(pos, wild)`, `condense(route)`.
- `src/template.html`: draws the map (layers, sprites, labels). `src/site_template.html`: the live page. `src/data.py`: owner's
  areas + directions. `src/VERSION`: footer label.
- `docs/REGION_NOTES.md`: data layout of the base, editor links, standing owner rules per region (read the part you need).
  `docs/archive/`: full history (grep it, don't read it whole). `CHANGELOG.md`: owner-facing history (append to the top section).

## State (Oct 22, 2026)
- Last version 2.7 (Oct 22, "Otherland's Peaks"; tag `v2.7` to be added by the owner on GitHub). Base = a legacy redraw + `applied/v22/`, `v23/`, `v24/`,
  `v2.2/` ... `v2.7/` (2.4: Otherland from the owner's save, `legacy/ol_layout_final.json`, now the save of Oct 23 00:19Z; 2.5: Otherland's wilds;
  2.6: the Azure Sea east coast (coast, sea, routes, cliff + climbs, iceberg 15154) and the Fissure as clefts down to the gorge floor;
  2.7: Otherland's mountains (Morte's Peak, Zenith of the Gods; terraces from above), even plants/drifts, east routes redrawn, north sea edge). Saves since
  Oct 22 18:39Z have the west/south 3 east: applied v2.4/001 `WS`. Details and standing rules: REGION_NOTES (Otherland).
  After a legacy redraw or a new Otherland save: `BASE_DUMP=<f> NO_TILES=1 python3 legacy/build_legacy.py`, then `python3 legacy/rebase.py <f> base/map.json`.
- All 15 layout editors live in the owner's current organization (links in REGION_NOTES). Read saves with ArtifactData get `<key>/current`.
  Hidden/route-only rooms added via `tools/forest_of_tears_editor/add_*.py`; Azure Sea rooms via `tools/otherland_editor/add_azure_east.py`.
- In progress (2.8): `changes/001_winterlight_island.py` (Winterlight Island re-fitted, Oct 22), `002_otherland_places.py` (4 sub-area markers, South/North routes), `003_otherland_keep_sprites.py` (Otherland save of Oct 23 00:19Z drawn; sprites kept), `004_otherland_mobs.py` (5 mobs, South/North), `005_sea_of_sorrows_keep_water.py` (Wastelands save of Oct 23 01:00Z drawn; sea edge kept). (2.7's files: `applied/v2.7/` 001 bases, 002 Morte's Peak + shared `build()`, 003 Gods, 004 even cover, 005 east routes, 006 north sea.)

## Snapshots
- Version numbers (owner, Oct 21): restarted at the map's revamp (the old count, v20-v24, is kept in the CHANGELOG); this release is 2.7, the next is 2.8
  (footer `Version 2.8 · <title> · <date>`, tag `v2.8`, folder `applied/v2.8/`; add the folder to `legacy/rebase.py`; change files that read
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
