"""A wide old-map frame round the sea (owner, Oct 23): the map's canvas grows by FW rooms on every side and the template draws the frame there
(template FRAME): nautical chart borders woven with forest - outer double rule, a twisted rope, two woven vines with leaves, tendrils and berries,
a second rope, an old chart's alternating bar border, a fine rule on the sea; compass roses wreathed in leaves in the corners, a fouled anchor
in the middle of each side. Nothing inside the old frame moves."""

FW = 14


def apply(town, wild, pos):
    x0, y0, x1, y1 = wild['bounds']
    wild['frame'] = {'inner': [x0, y0, x1, y1], 'w': FW}
    wild['bounds'] = [x0 - FW, y0 - FW, x1 + FW, y1 + FW]
    return {'canvas was -> now (the sea inside, the frame round it)': ([x0, y0, x1, y1], wild['bounds'])}
