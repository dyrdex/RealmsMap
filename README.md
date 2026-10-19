# Realm Map

An interactive dark-mode map of the MUD *Disgruntled Realms*, built from the owner's TinTin++ map file. Every push to `main` or
`claude/**` rebuilds the site and publishes it to GitHub Pages (`.github/workflows/pages.yml`).

## Building
`cd src && python3 build.py` (packages: `requirements.txt`). It takes about a minute, almost all of it the tile bake; `NO_TILES=1`
skips the tiles.

1. `base/map.json` is the frozen map: every marker, route, name, drawing and room position as of Oct 19, 2026 (after v20).
2. The files in `changes/` are applied on top of it, in file-name order (one small file per change; see `changes/README.md`).
3. `template.html` turns the data into `../realm_map.html`, the full map as one page (committed as the reference: a rebuild
   must not change it unless a change was meant).
4. `site_build.py` bakes the terrain into WebP tiles and writes `../site/` (Leaflet page from `site_template.html`, with live
   markers, names, search, cards and routes). Unchanged tiles are reused from `../.tile_cache/`.

When a version is saved, `python3 build.py --freeze` folds the changes into a new `base/map.json` and the change files are deleted.

## Files in `src`
- `base/map.json`: the frozen map. `changes/`: changes since the last freeze.
- `build.py`: the build above. `maplib.py`: helpers for changes (world file, route tracer, numbered directions).
- `world`: the owner's TinTin++ map file; `parse_world.py` reads it.
- `data.py`: the owner's areas and directions (`MORE_DIRECTIONS`, `ROUTE_OPTIONS`).
- `template.html`: draws the map. `site_template.html`: the live page. `site_build.py`: the tiles and the site.
- `editor_spread.py`: starting spots for new layout editors. `fonts/`, `vendor/`: embedded fonts and Leaflet.
- `VERSION`: the footer label.
- `legacy/`: the old pipeline that drew the map from the world file and the owner's editor saves, region by region (v1 to v20),
  with those saves (`*_layout_final.json`, `*_editor_edges.json`). `python3 legacy/build_legacy.py` still reproduces the frozen
  map exactly (`BASE_DUMP=<file>` writes it); it is only needed to redraw a whole region from its old code.

## Other folders
- `tools/`: the layout editors (one folder each, with their builders); links in `docs/REGION_NOTES.md`.
- `docs/REGION_NOTES.md`: the current rules per region. `docs/archive/`: the full region history and the changelog of v1 to v12.
- `CHANGELOG.md`: the owner-facing history. `CLAUDE.md`: working notes for Claude Code.
