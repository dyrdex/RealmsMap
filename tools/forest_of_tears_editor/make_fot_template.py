# Makes fot_editor_template.html (the Forest of Tears + Lake of Tich'Pyga layout editor) from the Azure Sea editor's template (dark only).
#   python3 make_fot_template.py ../azure_sea_editor/az_editor_template.html fot_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

FTC, LKC, WTC, FWC = '#8DBA4E', '#4FB3D9', '#E0B04A', '#D98AD0'      # outlines: Forest of Tears / Lake of Tich'Pyga / Western Trade Route
rep('<title>Layout editor · Azure Sea</title>', "<title>Layout editor · Forest of Tears</title>")
rep('The Azure Sea (rooms that join the map)', "The Forest of Tears and the Lake of Tich'Pyga")
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">Every room of the <b>Forest of Tears</b> (<b style="color:{FTC}">green outline</b>) and of the <b>Lake of Tich\'Pyga</b> (<b style="color:{LKC}">blue outline</b>), and the <b>Western Trade Route</b>\'s drawn road (<b style="color:{WTC}">gold outline</b>, unlocked: it starts where the map has it), and Forgotten Woods rooms 5634-5638 (<b style="color:{FWC}">pink outline</b>, unlocked: they start where the map has them), is here, plus the spacer rooms that join them to each other or to the map. The forest starts exactly where the finished map has it. The lake has no rooms on the map today (it is one drawn lake), so it starts as TinTin\'s own layout of it, stretched so that the rooms that touch the forest, the Forgotten Woods and Darkhaven land by the rooms they link to; expect it to sit on top of some forest rooms until you move it. A column of rooms with no exit to anything here (lake rooms with no exits, and Forest of Tears room 357, whose only exit is to the Southern Mountain Range) is parked just east of the lake. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; the Select buttons grab each area; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms to where TinTin\'s exits alone would put them.</p>', regex=True)
rep(r'<p><b>The fixed rooms</b>.*?</p>', '<p><b>The fixed rooms</b> (small round dots, grey-blue for Darkhaven, violet for the Shadow Grove, green for the Forgotten Woods) are the rooms already on the finished map, exactly where they are. They can\'t be moved. Hover one to see its name. The faint lines between them are the exits between those rooms. The finished map (land, lake, trails) is faintly behind; the forest and lake are going to be redrawn from your layout.</p>', regex=True)
rep(r'<p style="color:var\(--soft\)">North is up\..*?</p>', '<p style="color:var(--soft)">North is up. Rooms that TinTin puts on a level above or below the entrance (the Treetops, the cliffs, the lake bed) have a dashed outline and start a little to the side of the ground room they sit over. Up and down exits are dashed purple lines.</p>', regex=True)
rep('<button id="selNtr">Select the cliffs</button><button id="selRoad">Select the shore walk</button><button id="selNp">Select the north coast</button><button id="selEd">Select the path to Edo</button>',
    "<button id=\"selNtr\">Select the Forest of Tears</button><button id=\"selRoad\">Select the Lake of Tich'Pyga</button><button id=\"selWt\">Select the Western Trade Route</button><button id=\"selFw\">Select rooms 5634-5638</button>")
rep(r'    <i style="background:var\(--t-Forest\);border:2px solid #E08A4A">.*?path to the Village of Edo \(movable\)</span>\n',
    f'    <i style="background:var(--t-Forest);border:2px solid {FTC}"></i><span>Forest of Tears room (movable)</span>\n    <i style="background:var(--t-Water);border:2px solid {LKC}"></i><span>Lake of Tich\'Pyga room (movable)</span>\n    <i style="background:var(--t-Forest);border:2px solid {WTC}"></i><span>Western Trade Route room (movable)</span>\n    <i style="background:var(--t-Forest);border:2px solid {FWC}"></i><span>Forgotten Woods rooms 5634-5638 (unlocked, movable)</span>\n', regex=True)
rep(r'    <i style="background:var\(--cx-NTR\).*?Ashen Forest, the Eastern Trade Route and its beach</span>\n',
    '', regex=True)
rep('--cx-BP:#A86E52;--cx-NP:#B5A16A;--cx-AF:#8E8E8E;', '')
rep('--cx-NTR:#A8875C;', '')
rep(':root{--t-City:#8E78A8}', ':root{--t-City:#8E78A8;--t-Underwater:#3E6F8F;--t-Seafloor:#46607A}')
rep("'Inside','Underground','Water','Swimming','City']", "'Inside','Underground','Water','Swimming','City','Underwater','Seafloor']")
rep(r'\.nd\.np rect,\.nd\.np circle\.shape\{stroke:#8DBA4E\}\n\.nd\.pk.*?\.nd\.ed rect,\.nd\.ed circle\.shape\{stroke:#D98AD0\}',
    f'.nd.ft rect,.nd.ft circle.shape{{stroke:{FTC}}}\n.nd.lk rect,.nd.lk circle.shape{{stroke:{LKC}}}\n.nd.wt rect,.nd.wt circle.shape{{stroke:{WTC}}}\n.nd.fw rect,.nd.fw circle.shape{{stroke:{FWC}}}', regex=True)
rep("(r.area==='AZ'?' ntr '+r.grp:'')", "(r.area==='FT'?' ntr '+r.grp:'')")
rep(r"\$\{r\.area==='AZ'\?' · Azure Sea'.*?\[r\.grp\]:\(r\.src\?' · '\+\(\{.*?\}\)\[r\.src\]\+' \(fixed\)':''\)\}",
    "${r.area==='FT'?' · '+({ft:'Forest of Tears',lk:\"Lake of Tich'Pyga\",wt:'Western Trade Route',fw:'Forgotten Woods (unlocked)'})[r.grp]+(r.void?' (spacer room)':''):(r.src?' · '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods'})[r.src]+' (fixed)':'')}", regex=True)
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Forest of Tears rooms: ${a.fot} (${a.fot_untracked} the finished map doesn't hold: parked)<br>Lake of Tich'Pyga rooms: ${a.lake} (${a.lake_in_map} on the finished map)<br>Spacer rooms joining them: ${a.spacers} (${a.fot_sp} by the forest, ${a.lake_sp} by the lake); ${a.stubs} dead-end spacer stubs left off<br>Parked, no exit to anything here: ${a.parked}<br>Levels (TinTin, rooms): ${a.levels}<br>Pieces: ${a.pieces}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw}<br>Western Trade Route rooms (movable): ${a.wtr}<br>Forgotten Woods rooms unlocked: ${a.fwu}<br><br>Not included: the Forest of Tears' sub-areas (Bartok Grove, Major Oak ...), the Mire, the Southern Mountain Range and the rest of what its exits lead to`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='pk')sel.add(r.id)});refreshSel()};", "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='ft')sel.add(r.id)});refreshSel()};")
rep("$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='cw')sel.add(r.id)});refreshSel()};", "$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='lk')sel.add(r.id)});refreshSel()};")
rep("$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='lk')sel.add(r.id)});refreshSel()};", "$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='lk')sel.add(r.id)});refreshSel()};\n$('selWt').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='wt')sel.add(r.id)});refreshSel()};\n$('selFw').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='fw')sel.add(r.id)});refreshSel()};")
rep(r"\$\('selNp'\)\.onclick=.*?\n", '', regex=True)
rep(r"\$\('selEd'\)\.onclick=.*?\n", '', regex=True)
rep("'azlayout:v1'", "'ftlayout:v1'", 2)
rep("'azlayout/current'", "'ftlayout/current'", 2)
rep("'azlayout/b'", "'ftlayout/b'")
rep("const FORMAT='az-layout-1';", "const FORMAT='ft-layout-1';")
rep("filename:'azure_sea_layout.json'", "filename:'forest_of_tears_layout.json'")
bad = [w for w in ('azlayout', 'Azure', 'Edo', 'Peaks', 'Plains', "area==='AZ'", 'Ashen') if w in t]
rep("return {format:FORMAT,v:2,savedAt:", "return {format:FORMAT,v:3,savedAt:")
rep("((o.v||0)>=2||!(D.unlocked||[]).includes(id))", "((o.v||0)>=3||!(D.unlocked||[]).includes(id))")
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
