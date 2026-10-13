# Makes smr_editor_template.html (the Southern Mountain Range layout editor) from the Forest of Tears editor's template (dark only).
#   python3 make_smr_template.py ../forest_of_tears_editor/fot_editor_template.html smr_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

SMC = '#C98A5B'                                                           # outline: Southern Mountain Range
rep('<title>Layout editor · Forest of Tears</title>', '<title>Layout editor · Southern Mountain Range</title>')
rep("The Forest of Tears and the Lake of Tich'Pyga", 'The Southern Mountain Range')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">Every room of the <b>Southern Mountain Range</b> (<b style="color:{SMC}">copper outline</b>), plus the spacer rooms that join them to each other or to the map. Nothing is placed by hand yet: each piece of the range starts where TinTin\'s own exits put it, anchored (shifted, and stretched a little per axis when it touches the map in several places) to the Forest of Tears rooms it links to. Expect it to overlap itself and the forest until you move it. Rooms with no exit to anything here are parked in a column east of the range. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms to where TinTin\'s exits alone would put them.</p>', regex=True)
rep(r'<p><b>The fixed rooms</b>.*?</p>', '<p><b>The fixed rooms</b> (small round dots: grey-blue for Darkhaven, violet for the Shadow Grove, green for the Forgotten Woods, olive for the Forest of Tears, blue for the Lake of Tich\'Pyga, gold for the Western Trade Route) are the rooms already on the finished map, exactly where they are. They can\'t be moved. Hover one to see its name. The faint lines between them are the exits between those rooms. The finished map (land, lake, trails) is faintly behind.</p>', regex=True)
rep(r'<p style="color:var\(--soft\)">North is up\..*?</p>', '<p style="color:var(--soft)">North is up. Rooms that TinTin puts on a level above or below ground (the tunnels, caverns and underground rivers) have a dashed outline and start a little to the side of the ground room they sit under or over. Up and down exits are dashed purple lines.</p>', regex=True)
rep('<button id="selNtr">Select the Forest of Tears</button><button id="selRoad">Select the Lake of Tich\'Pyga</button><button id="selWt">Select the Western Trade Route</button><button id="selFw">Select rooms 5634-5638</button>',
    '<button id="selNtr">Select the Southern Mountain Range</button><button id="selRoad">Select the underground rooms</button>')
rep(r'    <i style="background:var\(--t-Forest\);border:2px solid #8DBA4E">.*?\(unlocked, movable\)</span>\n',
    f'    <i style="background:var(--t-Mountains);border:2px solid {SMC}"></i><span>Southern Mountain Range room (movable)</span>\n', regex=True)
rep('    <i style="background:var(--cx-FW);border-radius:50%"></i><span>Fixed room in the Forgotten Woods</span>\n',
    '    <i style="background:var(--cx-FW);border-radius:50%"></i><span>Fixed room in the Forgotten Woods</span>\n    <i style="background:var(--cx-FT);border-radius:50%"></i><span>Fixed room in the Forest of Tears</span>\n    <i style="background:var(--cx-LK);border-radius:50%"></i><span>Fixed room in the Lake of Tich\'Pyga</span>\n    <i style="background:var(--cx-WT);border-radius:50%"></i><span>Fixed room on the Western Trade Route</span>\n')
rep('--cx-FW:#6E9A6C;', '--cx-FW:#6E9A6C;--cx-FT:#8DBA4E;--cx-LK:#4FB3D9;--cx-WT:#E0B04A;')
rep(r'\.nd\.ft rect,\.nd\.ft circle\.shape\{stroke:#8DBA4E\}\n.*?\.nd\.fw rect,\.nd\.fw circle\.shape\{stroke:#D98AD0\}',
    f'.nd.sm rect,.nd.sm circle.shape{{stroke:{SMC}}}\n.nd.ug rect,.nd.ug circle.shape{{stroke:{SMC}}}', regex=True)
rep("(r.area==='FT'?' ntr '+r.grp:'')", "(r.area==='SM'?' ntr '+r.grp:'')")
rep(r"\$\{r\.area==='FT'\?' · '\+.*?\(fixed\)':''\)\}",
    "${r.area==='SM'?' · Southern Mountain Range'+(r.void?' (spacer room)':''):(r.src?' · '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods',FT:'Forest of Tears',LK:\"Lake of Tich'Pyga\",WT:'Western Trade Route'})[r.src]+' (fixed)':'')}", regex=True)
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Southern Mountain Range rooms: ${a.smr}<br>Spacer rooms joining them: ${a.spacers}; ${a.stubs} dead-end spacer stubs left off<br>Parked, no exit to anything here: ${a.parked}<br>Levels (TinTin, rooms): ${a.levels}<br>Pieces: ${a.pieces}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br>Placed by anchors: ${a.anchored} rooms in ${a.anchored_pieces} pieces<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw}<br>Forest of Tears ${a.ft} · Lake of Tich'Pyga ${a.lake} · Western Trade Route ${a.wtr}<br><br>Not included: the Southern Mountain Range's sub-areas and the other areas its exits lead to (Wastelands, Elemental Canyon, World Housing ...)`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='ft')sel.add(r.id)});refreshSel()};", "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='SM'&&!r.void)sel.add(r.id)});refreshSel()};")
rep("$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='lk')sel.add(r.id)});refreshSel()};", "$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='ug')sel.add(r.id)});refreshSel()};")
rep(r"\n\$\('selWt'\)\.onclick=.*?\n", '\n', regex=True)
rep(r"\$\('selFw'\)\.onclick=.*?\n", '', regex=True)
rep("'ftlayout:v1'", "'smrlayout:v1'", 2)
rep("'ftlayout/current'", "'smrlayout/current'", 2)
rep("'ftlayout/b'", "'smrlayout/b'")
rep("const FORMAT='ft-layout-1';", "const FORMAT='smr-layout-1';")
rep("filename:'forest_of_tears_layout.json'", "filename:'southern_mountain_range_layout.json'")
rep("return {format:FORMAT,v:3,savedAt:", "return {format:FORMAT,v:1,savedAt:")
rep("((o.v||0)>=3||!(D.unlocked||[]).includes(id))", "true")
bad = [w for w in ('ftlayout', "area==='FT'", 'Azure', '5634') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
