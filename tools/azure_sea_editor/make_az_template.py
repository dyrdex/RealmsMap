# Makes az_editor_template.html (the Azure Sea layout editor) from the Northern Plains editor's template (already dark only).
#   python3 make_az_template.py ../northern_plains_editor/np_editor_template.html az_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

AZC, PKC, CWC, NPC, EDC = '#4FB3D9', '#E08A4A', '#E3D27A', '#8DBA4E', '#D98AD0'   # outlines: linked to the Plains / the Peaks cliffs / the shore walk
rep('<title>Layout editor · Northern Plains</title>', '<title>Layout editor · Azure Sea</title>')
rep('color:var(--soft)">Northern Plains</span></h1>', 'color:var(--soft)">The Azure Sea (rooms that join the map)</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">Only the <b>Azure Sea</b> rooms that link to rooms already on the map, and the rooms that join those to each other, are here. Each room that links to the map starts one room from the room it links to; the rooms between them are spread evenly along the shore between. <b style="color:{PKC}">Orange outline</b>: the cliff-foot rooms under the Barren Peaks (6 have an up exit to a Peaks room, 7 lie between them). <b style="color:{CWC}">Yellow outline</b>: the shore walk, the \'Forgotten Woods Coastline\' rooms, which join the Peaks cliffs to the Azure beach room already on the map by the Ashen Forest (14254 \'The Crest of the Hill\'); none of them has an exit into a Forgotten Woods room. <b style="color:{NPC}">Green outline</b>: the coast north from the cliffs (14284, 14285, 14287 \'Azure and Green\' to 14313 and a spacer room) up to 4317 \'Rocky Coastline\', which joins the north of the Plains (4316) through two spacer rooms (14314, 22557: already on the map, movable here, starting where they are). <b style="color:{EDC}">Pink outline</b>: the path from 4317 north to the Village of Edo (7746 \'Adrift off the Coast\' leads nw into Edo); it starts north of 4317 as TinTin\'s exits lay it out. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; the three Select buttons grab each group; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms to where TinTin\'s exits alone would put them.</p>', regex=True)
rep("the Plains are all on one level.", "these rooms are all on one level (their links to the Peaks are up exits).")
rep('<button id="selNtr">Select the Northern Plains</button><button id="selRoad">Select the road</button>',
    '<button id="selNtr">Select the cliffs</button><button id="selRoad">Select the shore walk</button><button id="selNp">Select the north coast</button><button id="selEd">Select the path to Edo</button>')
rep(f'border:2px solid {NPC}"></i><span>Northern Plains room (movable)</span>\n    <i style="background:var(--t-Mountains);border:2px solid #B3541E"></i><span>Barren Peaks room you unlocked (movable)</span>\n    <i style="background:var(--t-Mountains);border:2px solid #D4B44A"></i><span>Northern Trade Route past the bridge (movable)</span>',
    f'border:2px solid {PKC}"></i><span>Azure Sea room under the Peaks cliffs (movable)</span>\n    <i style="background:var(--t-Forest);border:2px solid {CWC}"></i><span>Azure Sea shore walk (movable)</span>\n    <i style="background:var(--t-Forest);border:2px solid {NPC}"></i><span>Azure Sea coast north to the Plains (movable)</span>\n    <i style="background:var(--t-Forest);border:2px solid {EDC}"></i><span>Azure Sea path to the Village of Edo (movable)</span>')
rep('<span>Fixed room in the Barren Peaks</span>', '<span>Fixed room in the Barren Peaks</span>\n    <i style="background:var(--cx-NP);border-radius:50%"></i><span>Fixed room in the Northern Plains</span>\n    <i style="background:var(--cx-AF);border-radius:50%"></i><span>Fixed room in the Ashen Forest, the Eastern Trade Route and its beach</span>')
rep('brown for the Northern Trade Route up to the bridge, rust for the Barren Peaks)', 'brown for the Northern Trade Route, rust for the Barren Peaks, wheat for the Northern Plains, grey for the Ashen Forest and its beach)')
rep('<span>Fixed room on the Northern Trade Route (up to and including the bridge)</span>', '<span>Fixed room on the Northern Trade Route</span>')
rep('--cx-BP:#A86E52;', '--cx-BP:#A86E52;--cx-NP:#B5A16A;--cx-AF:#8E8E8E;')
rep('.nd.np rect,.nd.np circle.shape{stroke:' + NPC + '}\n.nd.pk rect,.nd.pk circle.shape{stroke:#B3541E}',
    '.nd.np rect,.nd.np circle.shape{stroke:' + NPC + '}\n.nd.pk rect,.nd.pk circle.shape{stroke:' + PKC + '}\n.nd.cw rect,.nd.cw circle.shape{stroke:' + CWC + '}\n.nd.ed rect,.nd.ed circle.shape{stroke:' + EDC + '}')
rep("(r.area==='NP'?' ntr np':r.area==='RD'?' ntr rd':r.area==='PK'?' ntr pk':'')", "(r.area==='AZ'?' ntr '+r.grp:'')")
rep("r.area==='NP'?' · Northern Plains':r.area==='PK'?' · Barren Peaks (movable)':r.area==='RD'?' · Northern Trade Route past the bridge'",
    "r.area==='AZ'?' · Azure Sea'+({pk:' (under the Peaks cliffs)',cw:' (shore walk)',np:' (coast north to the Plains)',ed:' (path to the Village of Edo)'})[r.grp]")
rep("NTR:'Northern Trade Route',BP:'Barren Peaks'})[r.src]", "NTR:'Northern Trade Route',BP:'Barren Peaks',NP:'Northern Plains',AF:'Ashen Forest'})[r.src]")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Azure Sea rooms under the Peaks cliffs: ${a.peaks}<br>Shore walk: ${a.coast} (${a.spacers} of them spacer rooms)<br>Coast north from the cliffs to the Plains: ${a.plains} (with the ${a.unlocked} spacer rooms to Plains room 4316)<br>Path from 4317 to the Village of Edo: ${a.edo}<br>Pieces: ${a.pieces}<br>Exits between these rooms: ${a.exits}<br>Links to rooms on the map: ${a.links} (${a.linked})<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw} · Northern Trade Route ${a.ntr} · Barren Peaks ${a.bp} · Northern Plains ${a.np} · Ashen Forest, Eastern Trade Route and beach ${a.af}<br><br>Not included: the rest of the Azure Sea (open water and its other shores)`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='NP')sel.add(r.id)});refreshSel()};\n$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='RD')sel.add(r.id)});refreshSel()};",
    "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='pk')sel.add(r.id)});refreshSel()};\n$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='cw')sel.add(r.id)});refreshSel()};\n$('selNp').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='np')sel.add(r.id)});refreshSel()};\n$('selEd').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='ed')sel.add(r.id)});refreshSel()};")
rep("'nplayout:v1'", "'azlayout:v1'", 2)
rep("'nplayout/current'", "'azlayout/current'", 2)
rep("'nplayout/b'", "'azlayout/b'")
rep("const FORMAT='np-layout-1';", "const FORMAT='az-layout-1';")
rep("filename:'northern_plains_layout.json'", "filename:'azure_sea_layout.json'")
rep("return {format:FORMAT,v:4,savedAt:", "return {format:FORMAT,v:1,savedAt:")
rep("(o.locked||[]).forEach(id=>{if(pos.has(id)&&((o.v||0)>=4||!(D.unlocked||[]).includes(id)))locked.add(id)});", "(o.locked||[]).forEach(id=>{if(pos.has(id))locked.add(id)});")
assert 'nplayout' not in t and "area==='NP'" not in t
open(out, 'w', encoding='utf-8').write(t)
print('ok')
