# Makes bp_editor_template.html (the Barren Peaks layout editor) from the Northern Trade Route editor's template.
#   python3 make_bp_template.py ../northern_trade_route_editor/ntr_editor_template.html bp_editor_template.html
# Dark mode only (project convention): the light palette and the prefers-color-scheme rules are dropped.
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()

# ---- dark only ----
dark = {}
for blk in re.findall(r':root\[data-theme="dark"\]\{([^}]*)\}', t):
    for k, v in re.findall(r'(--[\w-]+):([^;}]+)', blk): dark[k] = v.strip()
t, n1 = re.subn(r'@media \(prefers-color-scheme: dark\)\{:root:not\(\[data-theme="light"\]\)\{[^}]*\}\}\n?', '', t)
t, n2 = re.subn(r':root\[data-theme="dark"\]\{[^}]*\}\n?', '', t)
def darken(m):
    body = re.sub(r'(--[\w-]+):([^;}]+)', lambda d: d.group(1) + ':' + dark.get(d.group(1), d.group(2)), m.group(1))
    return ':root{' + body + '}'
t = re.sub(r':root\{([^}]*)\}', darken, t)
t = t.replace(':root{\n', ':root{color-scheme:dark;\n', 1)
assert 'data-theme' not in t and 'prefers-color-scheme' not in t, 'theme rules left'

def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

rep('<title>Layout editor · Northern Trade Route</title>', '<title>Layout editor · Barren Peaks</title>')
rep('color:var(--soft)">Northern Trade Route</span></h1>', 'color:var(--soft)">Barren Peaks of Tahjliera</span></h1>')
rep(r'<p id="ntrNote".*?</p>', '<p id="ntrNote" style="margin:4px 0 8px"><b>The Barren Peaks</b> (rooms with an <b style="color:#B3541E">orange outline</b>) and <b>the Northern Trade Route past the long bridge</b> (rooms with a <b style="color:#D4B44A">gold outline</b>, the road the Peaks are entered from) start off to the north of everything, in the shapes TinTin\'s exits give them, with trails to the Forgotten Woods rooms they connect to, so you can drag them into place. They come in a few separate <b>pieces</b> (one large, the rest small). <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Select the Barren Peaks</b> grabs everything movable; <b>Selected → where TinTin\'s exits suggest</b> sends the selected rooms to where your map\'s own exits put them (against the north edge of the Woods).</p>', regex=True)
rep('green for the Forgotten Woods) are the rooms', 'green for the Forgotten Woods, brown for the Northern Trade Route up to the bridge) are the rooms')
rep(r"<p style=\"color:var\(--soft\)\">The road's rooms start.*?</p>", '<p style="color:var(--soft)">North is up. Rooms that TinTin puts on a level above or below the entrance have a dashed outline. Up and down exits are dashed purple lines; most of the Peaks\' up/down rooms are also joined sideways through spacer rooms, so they start beside the ground level rather than on top of it.</p>', regex=True)
rep('<button id="selNtr">Select the Northern Trade Route</button>', '<button id="selPiece">Select the whole piece</button><button id="selNtr">Select the Barren Peaks</button>')
rep('<span>Northern Trade Route room (movable)</span>', '<span>Barren Peaks room (movable)</span>\n    <i style="background:var(--t-Mountains);border:2px solid #D4B44A"></i><span>Northern Trade Route past the bridge (movable)</span>')
rep('<span>Spacer room of the road (invisible in the game, free to move)</span>', '<span>Spacer room (invisible in the game, free to move)</span>')
rep('<span>Fixed room in the Forgotten Woods</span>', '<span>Fixed room in the Forgotten Woods</span>\n    <i style="background:var(--cx-NTR);border-radius:50%"></i><span>Fixed room on the Northern Trade Route (up to the bridge)</span>')
rep('--cx-FW:', '--cx-NTR:#A8875C;--cx-FW:')
rep('.nd.ntr rect,.nd.ntr circle.shape{stroke:#B3541E;stroke-width:.17}', '.nd.ntr rect,.nd.ntr circle.shape{stroke:#B3541E;stroke-width:.17}\n.nd.rd rect,.nd.rd circle.shape{stroke:#D4B44A}')
rep("(r.area==='NTR'?' ntr':'')", "(r.area==='BP'?' ntr':r.area==='RD'?' ntr rd':'')")
rep("${r.area==='NTR'?' · Northern Trade Route':(r.src?' · '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods'})[r.src]+' (fixed)':'')}",
    "${r.area==='BP'?' · Barren Peaks':r.area==='RD'?' · Northern Trade Route past the bridge':(r.src?' · '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods',NTR:'Northern Trade Route'})[r.src]+' (fixed)':'')}${r.piece!=null?' · piece '+(r.piece+1):''}")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Barren Peaks rooms: ${a.bp}${a.removed?` (left out at your request: room ${a.removed})`:''}<br>Northern Trade Route rooms past the bridge: ${a.road}<br>Spacer rooms joined to them: ${a.spacers}<br>Pieces: ${a.pieces} (${a.sizes})<br>Exits between these rooms: ${a.exits}<br>Links to rooms already on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw} · Northern Trade Route ${a.ntr}${a.unlocked?` (plus ${a.unlocked} bridge rooms you can move)`:''}<br><br>Not included: the Northern Plains, the Blood Sea and the other areas the Peaks lead to, which are not mapped yet`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='NTR')sel.add(r.id)});refreshSel()};",
    "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='BP'||r.area==='RD')sel.add(r.id)});refreshSel()};\n$('selPiece').onclick=()=>{const ps=new Set([...sel].map(id=>byId.get(id).piece).filter(p=>p!=null));if(!ps.size){toast('Select a room of the piece first');return}rooms.forEach(r=>{if(ps.has(r.piece))sel.add(r.id)});refreshSel()};")
rep("'ntrlayout:v1'", "'bplayout:v1'", 2)
rep("'ntrlayout/current'", "'bplayout/current'", 2)
rep("'ntrlayout/b'", "'bplayout/b'")
rep("const FORMAT='ntr-layout-1';", "const FORMAT='bp-layout-1';")
rep("filename:'northern_trade_route_layout.json'", "filename:'barren_peaks_layout.json'")
# rooms unlocked after a layout was saved: an older save (no "v") must not lock them again
rep("return {format:FORMAT,savedAt:", "return {format:FORMAT,v:2,savedAt:")
rep("(o.locked||[]).forEach(id=>{if(pos.has(id))locked.add(id)});", "(o.locked||[]).forEach(id=>{if(pos.has(id)&&(o.v||!(D.unlocked||[]).includes(id)))locked.add(id)});")
assert 'ntrlayout' not in t and "area==='NTR'" not in t
open(out, 'w', encoding='utf-8').write(t)
print('ok', n1, 'media blocks and', n2, 'dark blocks folded;', len(dark), 'dark values')
