"""A wide old-map frame round the sea (owner, Oct 23): the map's canvas grows by FW rooms on every side and the template draws the frame there
(template FRAME). It follows the sea's oval (owner: the sea's outer ring is the box `frame.box`, which ring() draws as four curves through its
sides' midpoints) and is drawn in pen and ink as the owner's two examples (Oct 23): two gnarled tree trunks for the sides, branches and vines
weaving round them and braiding at the top and bottom, twigs with small leaves, roots. Nothing inside the old frame moves."""

FW = 14


def apply(town, wild, pos):
    x0, y0, x1, y1 = wild['bounds']
    big = max(wild['geo']['water'], key=lambda r: (max(q[0] for q in r) - min(q[0] for q in r)) * (max(q[1] for q in r) - min(q[1] for q in r)))
    assert len(big) == 4, len(big)                                    # (the sea's outer ring: the box changes/009 fills, a little past the frame)
    xs = [q[0] for q in big]; ys = [q[1] for q in big]
    wild['frame'] = {'inner': [x0, y0, x1, y1], 'w': FW, 'box': [min(xs), min(ys), max(xs), max(ys)]}
    wild['bounds'] = [x0 - FW, y0 - FW, x1 + FW, y1 + FW]
    return {'canvas was -> now (the sea inside, the frame round it)': ([x0, y0, x1, y1], wild['bounds'])}
