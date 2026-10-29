"""Owner, Oct 28: a typo in the directions to Revelation City (8pm - 4am): 'enter, #3 n' -> 'enter;#3 n'."""


def apply(town, wild, pos):
    n = 0
    for p in wild['places']:
        for o in p.get('opts') or []:
            if o.get('route') and 'enter, #3 n' in o['route']:
                o['route'] = o['route'].replace('enter, #3 n', 'enter;#3 n'); n += 1
    assert n == 1, n
    return {'Revelation City typo': n}
