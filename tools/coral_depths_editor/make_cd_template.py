# Makes cd_editor_template.html (the Coral Depths layout editor) from the Pixie Forest editor's template (dark only).
#   python3 make_cd_template.py ../pixie_forest_editor/pf_editor_template.html cd_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

CDC, SMC = '#E58A6B', '#E0C04A'                                                     # outlines: Coral Depths, unlocked Southern Mountain Range rooms
rep('<title>Layout editor · Pixie Forest</title>', '<title>Layout editor · Coral Depths</title>')
rep('>The Pixie Forest</span></h1>', '>Coral Depths</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">The rooms you listed as <b>Coral Depths</b> (<b style="color:{CDC}">coral outline</b>): 47 rooms of the Azure Sea and Coral Depths areas that tie the Ashen Forest and the Southern Mountains together, plus the spacer rooms that join two of them (or one of them to a room on the map). Unlocked from the Southern Mountain Range: rooms <b>7, 8, 9, 10, 572, 6365</b> (<b style="color:{SMC}">gold outline</b>; they start where the map has them). The Coral Depths rooms start where TinTin\'s exits put them, one room apart, from rooms 10 and 572; rooms on another level are offset diagonally. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selNtr">Select the Pixie Forest rooms</button><button id="selAn">Select the Asgard Nexus rooms</button><button id="selFw">Select rooms 4017-4019</button>',
    '<button id="selNtr">Select the Coral Depths rooms</button><button id="selSm">Select rooms 7-10, 572, 6365</button>')
rep(f"    <i style=\"background:var(--t-Forest);border:2px solid #C77DD9\"></i><span>Pixie Forest room (movable)</span>\n    <i style=\"background:var(--t-Forest);border:2px solid #5BB8E0\"></i><span>Asgard Nexus room (movable)</span>\n    <i style=\"background:var(--t-Forest);border:2px solid #8DBA4E\"></i><span>Forgotten Woods room 4017, 4018 or 4019 (unlocked, movable)</span>\n",
    f"    <i style=\"background:var(--t-Swimming);border:2px solid {CDC}\"></i><span>Coral Depths room (movable)</span>\n    <i style=\"background:var(--t-Hills);border:2px solid {SMC}\"></i><span>Southern Mountain Range room 7, 8, 9, 10, 572 or 6365 (unlocked, movable)</span>\n")
rep('.nd.pf rect,.nd.pf circle.shape{stroke:#C77DD9}\n.nd.an rect,.nd.an circle.shape{stroke:#5BB8E0}\n.nd.fw rect,.nd.fw circle.shape{stroke:#8DBA4E}',
    f'.nd.cd rect,.nd.cd circle.shape{{stroke:{CDC}}}\n.nd.sm rect,.nd.sm circle.shape{{stroke:{SMC}}}')
rep("(r.area==='PF'?' ntr '+r.grp:'')", "(r.area==='CD'?' ntr '+r.grp:'')")
rep("${r.area==='PF'?' · '+({pf:'Pixie Forest',an:'Asgard Nexus',fw:'Forgotten Woods (unlocked)'})[r.grp]", "${r.area==='CD'?' · '+({cd:'Coral Depths',sm:'Southern Mountain Range (unlocked)'})[r.grp]+(r.ga?' (game area: '+esc(r.ga)+')':'')")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Coral Depths rooms you listed: ${a.cd} (Azure Sea ${a.az}, Coral Depths ${a.cdp}, Asgard Nexus ${a.an})<br>Spacer rooms joining them: ${a.spc}<br>Southern Mountain Range rooms unlocked: ${a.sm}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fwfix}<br>Forest of Tears ${a.ft} · Lake of Tich'Pyga ${a.lake} · Western Trade Route ${a.wtr}<br>Ashen Forest ${a.af} · Southern Mountain Range and its trade route ${a.smfix}<br><br>Only the rooms you listed; the rest of the Azure Sea and the Coral Depths stay off.`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='pf')sel.add(r.id)});refreshSel()};\n$('selAn').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='an')sel.add(r.id)});refreshSel()};\n$('selFw').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='fw')sel.add(r.id)});refreshSel()};",
    "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='cd')sel.add(r.id)});refreshSel()};\n$('selSm').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='sm')sel.add(r.id)});refreshSel()};")
rep("'pflayout:v1'", "'cdlayout:v1'", 2)
rep("'pflayout/current'", "'cdlayout/current'", 2)
rep("'pflayout/b'", "'cdlayout/b'")
rep("const FORMAT='pf-layout-1';", "const FORMAT='cd-layout-1';")
rep("filename:'pixie_forest_layout.json'", "filename:'coral_depths_layout.json'")
bad = [w for w in ('pflayout', "area==='PF'", 'Pixie', '#C77DD9', 'Asgard Nexus room') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
