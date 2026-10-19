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

## State (Oct 19, 2026)
- Last version v21 (Oct 19, "A New Starting Point": Miden'nir routes in full, Fog Cliffs mountains thinner, the map frozen into
  `src/base/map.json`; tag `v21` to be added by the owner on GitHub). Oct 19: base rebuilt by legacy with the owner's Plains
  save (14:29Z, then 14:50Z: road rooms 4165-4167 moved; `legacy/np_layout_final.json`). Changes since: 001 city graphics (New Ofcol, Salburg ->
  `stonecity`), 002 Wastelands shore path ends snapped to the water route, 003 Inahir Camp (old-map ink: palisade, 5 tents, long house,
  corral, fire pit, no animals; `wild.camps`, template CAMPS), legend icon = stone city, 004 Tall Trees grove (82 tall trees
  round 4575; `wild.talltrees`, template TALL; old `grove` gfx removed), 005 sea gaps east of the Plains filled
  (`geo.seafill` + `seashore`, drawn over the sea; rerun it, or a copy with its own box, after any coast change).
- Oct 19: all 13 layout editors republished in the owner's current organization (links in REGION_NOTES; loaded with the latest
  saves). Read saves with ArtifactData get `<key>/current` on the new links; nothing from the old organization is used.
- Next (owner's list): clearings assessment
  (candidate room clusters per area for the owner to approve, then one general clearing change); Sesuad'ra Rift rooms (2112, 21974, 21973, 13608, 21972, 21971,
  21970, 13607, 2088, 2090) ADDED to the Forest of Tears editor Oct 19 (`tools/forest_of_tears_editor/add_sesuadra_rooms.py`; way in 1659 n 2086
  cauldron 2112; 2086 not added): waiting for the owner's save; render with a change file, never via legacy ft_merge (directions `#9 w;nw;#2 w;nw;w;#2 n;#3 nw;w;#4 sw;w;#2 nw;w;sw;#13 w;n;cauldron;sw;enter`).

## Snapshots
- New version: `python3 build.py --freeze`, delete the change files, edit `src/VERSION`, retitle the CHANGELOG's in-progress
  section, rebuild twice (realm_map.html must match), commit.
- Merge into `main` ONLY when the owner says to save a new version (Oct 16). Day to day: push to the session branch only. Then
  open a PR to `main`, merge it, and remind the owner: GitHub -> Releases -> Draft a new release -> tag `vN` -> Target `main` ->
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
- Never send images or files into the chat (Oct 18): screenshots are for checking only.
- Ask before work outside the agreed plan.
- After each batch: one line per change in CHANGELOG (owner-facing), a short rule in REGION_NOTES if it should hold later,
  update "State" above.
