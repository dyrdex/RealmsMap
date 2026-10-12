"""Small visual-only adjustments to where certain rooms are DRAWN on the map. The layout you arrange in the editor is not changed by these."""

# The Ashen Forest Inn sits inside a ring of road. The ring is widened a little (the north row up, the south row down by half a room each)
# so the inn drawing fits between the roads without touching them.
INN_RING = {
    2980: (0, -0.5), 19840: (0, -0.5), 19841: (0, -0.5), 19836: (0, -0.5), 19834: (0, -0.5), 2990: (0, -0.5), 2988: (0, -0.5),      # north row
    2987: (0, 0.5), 19838: (0, 0.5), 19833: (0, 0.5), 2986: (0, 0.5), 19839: (0, 0.5), 19835: (0, 0.5), 2985: (0, 0.5),            # south row
}
NUDGES = dict(INN_RING)
