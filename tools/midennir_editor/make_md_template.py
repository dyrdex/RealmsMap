# Makes md_editor_template.html (the Miden'nir layout editor) from the Southern Mountain Range editor's template (dark only).
#   python3 make_md_template.py ../southern_mountain_range_editor/smr_editor_template.html md_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

MDC = '#D97A8A'                                                                                          # outline: Miden'nir
rep('<title>Layout editor · Southern Mountain Range</title>', "<title>Layout editor · Miden'nir</title>")
rep('>The Southern Mountain Range</span></h1>', ">Miden'nir</span></h1>")
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">The rooms of <b>Miden\'nir</b> above ground (<b style="color:{MDC}">rose outline</b>): the Black Forest, its trails and brambles, the rusted bridge and the Mysterious Inn (its rooms upstairs and its cellar brewery too), plus the spacer rooms that join them to each other or to the map. The tunnels under Mount Doom are left out. Each room starts where the painted Miden\'nir on the map has it today (worked out from TinTin\'s exits). Hide any room you don\'t want displayed on the map: the painting stays, and the rooms you keep are drawn on it. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to where TinTin\'s exits alone would put them.</p>', regex=True)
rep(r'<p><b>The fixed rooms</b>.*?</p>', '<p><b>The fixed rooms</b> (small round dots: grey-blue for Darkhaven, violet for the Shadow Grove, green for the Forgotten Woods, olive for the Forest of Tears, blue for the Lake of Tich\'Pyga, gold for the Western Trade Route, brown for the Ashen Forest, copper for the Southern Mountain Range and its trade route) are the rooms already on the finished map, exactly where they are. They can\'t be moved. Hover one to see its name. The faint lines between them are the exits between those rooms. The finished map (land, lake, trails) is faintly behind.</p>', regex=True)
rep(r'<p style="color:var\(--soft\)">North is up\..*?</p>', '<p style="color:var(--soft)">North is up. The Mysterious Inn\'s rooms upstairs and its cellar (a level above or below ground in TinTin) have a dashed outline and start a little to the side of the room they sit over or under. Up and down exits are dashed purple lines.</p>', regex=True)
rep('<button id="selNtr">Select the Southern Mountain Range</button><button id="selRoad">Select the underground rooms</button><button id="selFt">Select the Sparse Woodlands trail</button><button id="selTr">Select the Southern Mountain Trade Route</button><button id="selAf">Select room 670 and its spacer</button>',
    '<button id="selNtr">Select Miden\'nir</button>')
rep(r'    <i style="background:var\(--t-Mountains\);border:2px solid #C98A5B">.*?\(movable\)</span>\n(    <i style="background:var\(--t-[A-Za-z]+\);border:2px solid #[0-9A-F]+">.*?</span>\n){3}',
    f'    <i style="background:var(--t-Forest);border:2px solid {MDC}"></i><span>Miden\'nir room (movable)</span>\n', regex=True)
rep('    <i style="background:var(--cx-WT);border-radius:50%"></i><span>Fixed room on the Western Trade Route</span>\n',
    '    <i style="background:var(--cx-WT);border-radius:50%"></i><span>Fixed room on the Western Trade Route</span>\n    <i style="background:var(--cx-SM);border-radius:50%"></i><span>Fixed room in the Southern Mountain Range or on its trade route</span>\n')
rep('--cx-WT:#E0B04A;', '--cx-WT:#E0B04A;--cx-SM:#C98A5B;')
rep(r'\.nd\.sm rect,\.nd\.sm circle\.shape\{stroke:#C98A5B\}\n.*?\.nd\.af rect,\.nd\.af circle\.shape\{stroke:#E08A4A\}',
    f'.nd.md rect,.nd.md circle.shape{{stroke:{MDC}}}', regex=True)
rep("(r.area==='SM'?' ntr '+r.grp:'')", "(r.area==='MD'?' ntr '+r.grp:'')")
rep(r"\$\{r\.area==='SM'\?' · '\+.*?\(fixed\)':''\)\}",
    "${r.area==='MD'?\" · Miden'nir\"+(r.void?' (spacer room)':''):(r.src?' · '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods',AF:'Ashen Forest',FT:'Forest of Tears',LK:\"Lake of Tich'Pyga\",WT:'Western Trade Route',SM:'Southern Mountain Range'})[r.src]+' (fixed)':'')}", regex=True)
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Miden'nir rooms: ${a.md} (of ${a.all}; the ${a.tunnels} tunnel rooms under Mount Doom left out)<br>Spacer rooms joining them: ${a.spacers}; ${a.stubs} dead-end spacer stubs left off<br>Levels (TinTin, rooms): ${a.levels}<br>Pieces: ${a.pieces}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw}<br>Forest of Tears ${a.ft} · Lake of Tich'Pyga ${a.lake} · Western Trade Route ${a.wtr}<br>Ashen Forest ${a.af} · Southern Mountain Range and its trade route ${a.sm}<br><br>Not included: the tunnels under Mount Doom, and the other areas Miden'nir's exits lead to (Shattered Refuge, Intrigues of the Miden'nir, Moria, World Housing ...)`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='SM'&&!r.void)sel.add(r.id)});refreshSel()};", "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='MD'&&!r.void)sel.add(r.id)});refreshSel()};")
rep(r"\n\$\('selRoad'\)\.onclick=.*?\n\$\('selAf'\)\.onclick=[^\n]*", '', regex=True)
rep("'smrlayout:v1'", "'mdlayout:v1'", 2)
rep("'smrlayout/current'", "'mdlayout/current'", 2)
rep("'smrlayout/b'", "'mdlayout/b'")
rep("const FORMAT='smr-layout-1';", "const FORMAT='md-layout-1';")
rep("filename:'southern_mountain_range_layout.json'", "filename:'midennir_layout.json'")
bad = [w for w in ('smrlayout', "area==='SM'", 'Sparse Woodlands', 'selAf', 'selTr', 'selFt', 'selRoad') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
