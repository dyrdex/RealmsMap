# Realm map: working notes (loaded every session; keep this file short)

Interactive dark-mode map of the MUD "Disgruntled Realms", built from the owner's TinTin++ map (`src/world`).
Pipeline (Python) paints terrain from room layouts -> `realm_map.html` (render source) -> `site_build.py`
bakes terrain into WebP tiles -> `site/` (Leaflet CRS.Simple page with live markers, names, search, cards, routes).

## Build, review, deploy
- `cd src && python3 build.py` (~1 min pipeline + ~50 s tiles). `NO_TILES=1` skips tiles. Packages: `requirements.txt` (pinned; playwright 1.56.0 = Chromium 1194, which cloud sessions have pre-installed).
- The pipeline is deterministic: `realm_map.html` is committed as the reference; a rebuild must not change it unless intended. `git diff --stat realm_map.html` after each build.
- Build outputs are NOT committed (`site/`, `realm_map_preview.html`, `src/nd2.json`, `src/fot.json`).
- GitHub Actions (`.github/workflows/pages.yml`) rebuilds and deploys `site/` to GitHub Pages on every push to `main` or `claude/**`. The owner reviews there.
- Old artifact links (working map, preview, snapshots, editors) are listed in `docs/REGION_NOTES.md`.

## Where things are
- `src/build.py`: stage order. `src/template.html`: draws the terrain for the bake. `src/site_template.html`: the live page (sidebar, cards, legend). `src/data.py`: owner's areas + directions. `src/VERSION`: footer label.
- Per-region merge modules and their editor saves: Ashen (`ashen_*`), NTR (`ntr_*`), Barren Peaks (`bp_*`), Northern Plains (`np_*`), Azure Sea (`az_*`, editor only so far). Editors in `tools/`. `*_marker_routes.py` are one-time scripts that write `*_marker_routes.json`.
- `docs/REGION_NOTES.md`: detailed per-region history and decisions. Read only the section for the region being changed.
- `CHANGELOG.md`: owner-facing history. `README.md`: file-by-file description.

## State (Oct 12, 2026)
- Mapped through the Northern Plains, incl. its sub-area markers, area name and the NW sea (Oct 12 batch). Last snapshot: v11 (git tag `v11`, Oct 12).
- Open question to owner: which regions to freeze. (Asgard Nexus and World Housing stay off the map: owner, Oct 12.)
- Azure Sea (limited, owner Oct 12): editor published (47 rooms; see REGION_NOTES), waiting for the owner's save in `azlayout/current`; then write the merge.
- Not done (not asked): routes through the Plains on Peaks cards.
- Agreed plan (Oct 12): repo cleanup + Pages done. Next, when the owner picks the regions: freeze finished regions into baked data with final positions (markers, drawings, names incl. the solver's) so no correction tables remain, and re-render only changed tiles. Verify with a pixel-identical rebuild. (The separate tweaks file was dropped.)

## Snapshots
- An official version = edit `src/VERSION`, retitle the CHANGELOG's in-progress section, rebuild twice (realm_map.html must match), commit, then an annotated git tag `vN` pushed to GitHub (replaces the old zip + artifact snapshots).

## Conventions (owner preferences)
- Dark mode only: no light palette, no `prefers-color-scheme`, no theme toggle.
- Never add graphics, labels or markers the owner didn't ask for. Do exactly what's asked and report numbers.
- Big area names: italic, size 2.4, letter-spacing .55, pale halo, gentle arc. Small labels: italic .38, soft grey, pale halo.
- Trade routes are one continuous formal road with off-ramp pads where paths/sub-area links join; dirt trails elsewhere. Spacer rooms drawn only between two real rooms; dead-end spacer stubs left off.
- Don't re-add coasts to the Barren Peaks unless the owner asks with a clear picture.

## Gotchas
1. Never fill open water without a bounding box. After any coast/land change, diff land against the last snapshot and list new pieces.
2. Any land-mask change must also clip ground tints and clear trees/tufts in the cut area.
3. A route's marker goes where the route leaves the area, not at the end of the drawn rooms.
4. Roads are drawn layer by layer across ALL segments (no per-segment layers) or joints show seams.
5. Lists like `w['gfx']` are appended to, never replaced.
6. Check placements numerically (distance to road/water, overlaps with names) before any screenshot. The site's label positions can differ from `realm_map.html`'s; check overlaps against `site/data/places.json`.
7. Label solver flags 11 hand-placed names as "touching": expected baseline.
8. `bp_merge` and `np_merge` use their own taller grids; `np_merge` must stay the LAST land change. Don't extend `gap_fill`'s grid (float rounding moves things elsewhere).
9. Fonts are embedded from `src/fonts/` for the bake; screenshots without them show different label placement.
10. Leaflet snaps to whole zoom levels (zoomSnap 1) to avoid tile seams.
11. Preview artifact limit is 16 MB (preview is ~14 MB): another reason the site now lives on Pages.

## Working rules (save credits)
- Read this file; open `docs/REGION_NOTES.md`, README or CHANGELOG sections only when needed. Don't search old chats.
- Batch the owner's requests into one build; verify with numbers; at most one screenshot per set of changes.
- Ask before work outside the agreed plan.
- After each batch: one line per change in CHANGELOG (owner-facing), short decisions in REGION_NOTES under the region, update "State" above.
