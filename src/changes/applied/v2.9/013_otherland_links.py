"""Owner, Oct 23: Otherland's links to the Northern Plains side, drawn with the sprites already used for them:
  - at the far south of the water path south out of Otherland (Off the Northern Coast 15606, the southernmost room), the 'Otherland'
    watery trail of the Northern Plains' north-west (gfx 'waterway', len 3.4) mirrored to aim south, with a small label "Northern Plains"
    beside its tip as the 'Otherland' one has (tags, size 0.55; the same gap from the trail);
  - in 5967 and 5970 (Adrift off the Coast, their down exits lead to Otherland) the watery hole of 2528 (gfx 'seahole', 1.1), each with a
    small label "Otherland" just east of it (the side clear of paths)."""

WIDTH = {'Otherland': 2.172, 'Northern Plains': 3.388}            # text widths at size 0.55 (fonts/alegreya-latin-600-italic, measured)


def apply(town, wild, pos):
    width = WIDTH.get
    G = wild['gfx']; T = wild['tags']
    ww = next(g for g in G if g['k'] == 'waterway'); wt = next(t for t in T if t[2] == 'Otherland' and abs(t[0] - ww['x']) < 4 and abs(t[1] - ww['y']) < 5)
    gap = (wt[0] - ww['x']) - width('Otherland') / 2                   # its label's left edge this far east of the trail
    x, y = pos['15606']
    G.append(dict(ww, x=x, y=y, h=-ww['h']))                           # (h < 0: the sprite mirrored north to south)
    T.append([round(x + gap + width('Northern Plains') / 2, 2), round(y - (wt[1] - ww['y']), 2), 'Northern Plains', wt[3]])
    sh = next(g for g in G if g['k'] == 'seahole')
    for r in ('5967', '5970'):
        hx, hy = pos[r]
        G.append(dict(sh, x=hx, y=hy))
        T.append([round(hx + sh['w'] / 2 + 0.25 + width('Otherland') / 2, 2), round(hy, 2), 'Otherland', 0.55])
    return {'trail aiming south at 15606, its label': ((x, y), T[-3][:2]), 'holes at 5967, 5970, their labels': [t[:2] for t in T[-2:]]}
