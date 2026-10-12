"""Attach the directions you gave to the town cards by where they lead, so each card shows your text and sits on the
right marker. Returns the names that were renamed."""
import re
def _exp(route):
    out=[]
    for tok in (route or '').split(';'):
        tok=tok.strip()
        if not tok: continue
        m=re.match(r'^#\s*(\d+)\s*(.+)$',tok)
        out+=([m.group(2).strip()]*int(m.group(1))) if m else [tok]
    return out
def parse(block):
    d={}
    for l in (block or '').strip().splitlines():
        if '|' in l: n,r=l.split('|',1); d[n.strip()]=r.strip()
    return d
def apply_town(places, more):
    """A town marker takes the name and directions of whichever of your directions end at the same place as its own."""
    by_route={';'.join(_exp(r)):n for n,r in more.items()}
    changed=[]
    for p in places:
        key=';'.join(_exp(p.get('route') or ''))
        if key in by_route:
            n=by_route[key]
            if p['name']!=n: changed.append((p['name'],n))
            p['name']=n; p['route']=more[n]; p.pop('noroute',None)
    return changed
