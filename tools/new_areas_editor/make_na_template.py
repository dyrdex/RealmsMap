# Makes na_editor_template.html (the layout editor for Angel's Landing, the Village of Edo and The Grimdog Port Authority) from the Coral Depths
# editor's template (dark only).
#   python3 make_na_template.py ../coral_depths_editor/cd_editor_template.html na_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

ALC, EDC, GPC = '#9FB4FF', '#F2A65A', '#5FD3B5'                                  # outlines: Angel's Landing, Village of Edo, Grimdog Port Authority
rep('<title>Layout editor · Coral Depths</title>', "<title>Layout editor · Angel's Landing, Edo, Grimdog</title>")
rep('>Coral Depths</span></h1>', ">Angel's Landing · Edo · Grimdog</span></h1>")
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">Three areas, each with its own outline: <b style="color:{ALC}">Angel\'s Landing</b> (its 22 rooms, plus Blood Sea room <b>16226</b>, shown only with its links ne to 5667 on the Forgotten Beach and nw to 21135), <b style="color:{EDC}">the Village of Edo</b> (77 rooms, off 7746 on the Azure Sea Coast) and <b style="color:{GPC}">The Grimdog Port Authority</b> (29 rooms, plus Western Trade Route room <b>21076</b>, the way in from the road), and the spacer rooms that join them. They start where TinTin\'s exits put them, one room apart, from the rooms they join on the map; rooms on another level are offset diagonally. The map grows west and north to fit them. The three buttons below select an area and zoom to it. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selNtr">Select the Coral Depths rooms</button><button id="selSm">Select the unlocked map rooms</button>',
    "<button id=\"selAl\">Angel's Landing</button><button id=\"selEdo\">Village of Edo</button><button id=\"selGp\">Grimdog Port Authority</button>")
rep(f"    <i style=\"background:var(--t-Swimming);border:2px solid #E58A6B\"></i><span>Coral Depths room (movable)</span>\n    <i style=\"background:var(--t-Hills);border:2px solid #E0C04A\"></i><span>Unlocked map room: 7-10, 569-572, 6365, 19863 (Southern Mountain Range) or 14360 (Ashen Forest) (movable)</span>\n",
    f"    <i style=\"background:var(--t-Field);border:2px solid {ALC}\"></i><span>Angel's Landing room, or Blood Sea room 16226 (movable)</span>\n    <i style=\"background:var(--t-City);border:2px solid {EDC}\"></i><span>Village of Edo room (movable)</span>\n    <i style=\"background:var(--t-City);border:2px solid {GPC}\"></i><span>Grimdog Port Authority room, or Western Trade Route room 21076 (movable)</span>\n")
rep('.nd.cd rect,.nd.cd circle.shape{stroke:#E58A6B}\n.nd.un rect,.nd.un circle.shape{stroke:#E0C04A}',
    f'.nd.al rect,.nd.al circle.shape{{stroke:{ALC}}}\n.nd.edo rect,.nd.edo circle.shape{{stroke:{EDC}}}\n.nd.gp rect,.nd.gp circle.shape{{stroke:{GPC}}}')
rep("(r.area==='CD'?' ntr '+r.grp:'')", "(r.area==='NA'?' ntr '+r.grp:'')")
rep("${r.area==='CD'?' · '+({cd:'Coral Depths',un:'unlocked map room'})[r.grp]", "${r.area==='NA'?' · '+({al:\"Angel's Landing\",edo:'Village of Edo',gp:'Grimdog Port Authority'})[r.grp]")
rep("SM:'Southern Mountain Range'})[r.src]", "SM:'Southern Mountain Range',AZ:'Azure Sea Coast',N:'Northern Plains, Barren Peaks and the Northern Trade Route',MD:\"Miden'nir\",PF:'Pixie Forest',CD:'Coral Depths'})[r.src]")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Angel's Landing rooms: ${a.al} + Blood Sea room 16226 · spacers ${a.als}<br>Village of Edo rooms: ${a.edo} · spacers ${a.edos}<br>Grimdog Port Authority rooms: ${a.gp} + Western Trade Route room 21076 · spacers ${a.gps}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br><br>Fixed rooms already on the finished map (near these areas): ${a.fixed}`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='cd')sel.add(r.id)});refreshSel()};\n$('selSm').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='un')sel.add(r.id)});refreshSel()};",
    "const selGrp=g=>{sel.clear();rooms.forEach(r=>{if(r.grp===g)sel.add(r.id)});refreshSel();const P=[...sel].map(id=>pos.get(id));if(!P.length)return;"
    "const x0=Math.min(...P.map(p=>p[0]))-6,x1=Math.max(...P.map(p=>p[0]))+6,y0=Math.min(...P.map(p=>p[1]))-6,y1=Math.max(...P.map(p=>p[1]))+6;"
    "cam={x:(x0+x1)/2,y:(y0+y1)/2,k:Math.max(3,Math.min(140,Math.min(VW/(x1-x0),VH/(y1-y0))))};applyCam()};\n"
    "$('selAl').onclick=()=>selGrp('al');$('selEdo').onclick=()=>selGrp('edo');$('selGp').onclick=()=>selGrp('gp');")
rep("(o.locked||[]).forEach(id=>{if(pos.has(id)&&!((D.newly||[]).includes(id)&&(o.savedAt||'')<(D.newlyAt||'')))locked.add(id)})",
    "(o.locked||[]).forEach(id=>{if(pos.has(id))locked.add(id)})")
rep("'cdlayout:v1'", "'nalayout:v1'", 2)
rep("'cdlayout/current'", "'nalayout/current'", 2)
rep("'cdlayout/b'", "'nalayout/b'")
rep("const FORMAT='cd-layout-1';", "const FORMAT='na-layout-1';")
rep("filename:'coral_depths_layout.json'", "filename:'new_areas_layout.json'")
bad = [w for w in ('cdlayout', "area==='CD'", 'Coral Depths room', '#E58A6B', "grp==='cd'") if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
