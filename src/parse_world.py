import re
from collections import Counter, defaultdict
def fields(line):
    # split top-level {...} groups
    out=[];depth=0;cur=''
    for ch in line:
        if ch=='{':
            if depth==0: cur=''
            else: cur+=ch
            depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: out.append(cur)
            else: cur+=ch
        elif depth>0: cur+=ch
    return out
rooms={}; exits=defaultdict(list); landmarks=[]
cur=None
import os as _osw
for line in open('world' if _osw.path.exists('world') else '../world',encoding='utf-8'):
    line=line.rstrip('\n')
    if line.startswith('R '):
        f=fields(line[2:]); v=int(f[0]); cur=v
        rooms[v]=dict(vnum=v,flags=int(f[1]),color=f[2],name=f[3],symbol=f[4],desc=f[5],area=f[6],note=f[7],terrain=f[8],data=f[9],weight=f[10],id=f[11] if len(f)>11 else '',nf=len(f))
    elif line.startswith('E ') and cur is not None:
        f=fields(line[2:])
        exits[cur].append(dict(to=int(f[0]),name=f[1],cmd=f[2],dir=int(f[3]),flags=int(f[4]),data=f[5],weight=f[6],color=f[7],delay=f[8] if len(f)>8 else ''))
    elif line.startswith('LM '):
        f=fields(line[3:]); landmarks.append(f)
