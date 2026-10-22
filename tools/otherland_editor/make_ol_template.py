# Makes ol_editor_template.html (the layout editor for Otherland) from the Desert of Despair editor's template (dark only).
#   python3 make_ol_template.py ../desert_of_despair_editor/dd_editor_template.html ol_editor_template.html
# Changes: names, save keys, legend (Otherland rooms; fixed map rooms), the up/down note.
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

OLC, OLX, AZX, NX, ANC, UNC = '#9FD3F0', '#CFE9F7', '#4FA3C9', '#8C8C8C', '#B58CE6', '#6FC3E8'                                # outlines: Otherland rooms; fixed: Otherland, Azure Sea Coast, other map rooms
rep('<title>Layout editor · Desert of Despair</title>', '<title>Layout editor · Otherland</title>')
rep('>Desert of Despair</span></h1>', '>Otherland</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b style="color:{OLC}">Otherland</b>: all its rooms, the unnamed rooms that lead only back into it, and the spacer rooms that join them. It joins the map only at the Iceberg rooms 22534 and 22535 (east to 13379 and 13380 on the Sea of Sorrows coast); its other exits (Blood Sea, Azure Sea, Sea of Sorrows, Wild Tundra, Cursed Lands, Asgard Nexus) are left off. Where a room has an up/down exit to the same room as one of its flat exits (n, e, s, w, ne, se, nw, sw), the flat exit is used and the up/down one ignored; the up/down exits left (dashed) start offset diagonally (up = north-east). The area is split into <b>sections</b> (parts with only a few exits between them). Each section starts where TinTin\'s exits put its rooms, two rooms apart; the sections are spread out with wide gaps between them over the sea west and south of the link rooms (past the map\'s south edge, which grows to fit), so some exits between sections (and to the map) are stretched. Hide any room you don\'t want on the map. <b>Select a section</b> grabs a whole section to move it; <b>Select the whole piece</b> grabs the sections of the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selDd">Select the desert rooms</button><button id="selWl">Select the Wastelands rooms</button><button id="selCd">Select the Coral Depths rooms</button><button id="selGe">Select the added rooms</button>', '<button id="selOl">Select the Otherland rooms</button><button id="selAn">Select the added rooms</button><button id="selUn">Select the unlocked map rooms</button>')
rep(r'    <i style="background:var\(--t-Desert\);border:2px solid #E6C36A"></i>.*?\(movable, start next to the rooms they join in your saved layout\)</span>\n',
    f'    <i style="background:var(--t-Mountains);border:2px solid {OLC}"></i><span>Otherland room (movable)</span>\n'
    f'    <i style="background:var(--t-other);border:2px solid {ANC}"></i><span>Added Oct 21: Frost Mansion 22248-22250 (Asgard Nexus), off 22247 and 21819 (movable, start next to the rooms they join)</span>\n'
    f'    <i style="background:var(--t-Water);border:2px solid {UNC}"></i><span>Unlocked map room (Oct 21): the Ahtborne Straights 18052-18075 (Blood Sea, spacers included), 6174, 18047, 13379 and 13380, Among the Icebergs 6166 and 6180, Afloat on the Azure Sea 6650 and 15410-15418 (movable, start at their spots on the map)</span>\n', regex=True)
rep('    <i style="background:var(--cx-MI);border-radius:50%"></i><span>Fixed room in the Mire</span>\n',
    '    <i style="background:var(--cx-MI);border-radius:50%"></i><span>Fixed room in the Mire</span>\n    <i style="background:var(--cx-AZ);border-radius:50%"></i><span>Fixed room on the Azure Sea Coast</span>\n')
rep('--cx-DD:#F2E2A0;--cx-MI:#7FCB8E;--cx-N:#8C8C8C', f'--cx-DD:#F2E2A0;--cx-MI:#7FCB8E;--cx-AZ:{AZX};--cx-OL:{OLX};--cx-N:{NX}')
rep('.nd.dd rect,.nd.dd circle.shape{stroke:#E6C36A}\n.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}\n.nd.wl rect,.nd.wl circle.shape{stroke:#D98A5B}\n.nd.cd rect,.nd.cd circle.shape{stroke:#E07A9A}\n.nd.ge rect,.nd.ge circle.shape{stroke:#B58CE6}',
    f'.nd.ol rect,.nd.ol circle.shape{{stroke:{OLC}}}\n.nd.an rect,.nd.an circle.shape{{stroke:{ANC}}}\n.nd.un rect,.nd.un circle.shape{{stroke:{UNC}}}')
rep("(r.area==='DD'?' ntr '+r.grp:'')", "(r.area==='OL'?' ntr '+r.grp:'')")
rep("${r.area==='DD'?' · Desert of Despair'", "${r.area==='OL'?' · Otherland'")
rep("DD:'Desert of Despair',MI:'The Mire'})[r.src]", "DD:'Desert of Despair',MI:'The Mire',OL:'Otherland'})[r.src]")
rep("Desert rooms: ${a.dd} · spacers ${a.dds}", "Otherland rooms: ${a.ol} · added Frost Mansion rooms ${a.an} · unlocked map rooms ${a.un} · unnamed rooms ${a.oln} · spacers ${a.ols}<br>Up/down exits ignored (a flat exit joins the same rooms): ${a.flat} · up/down exits kept: ${a.ud}")
rep("(near the desert)", "(near Otherland)")
rep("$('selDd').onclick=()=>selGrp('dd');$('selWl').onclick=()=>selGrp('wl');$('selCd').onclick=()=>selGrp('cd');$('selGe').onclick=()=>selGrp('ge');", "$('selOl').onclick=()=>selGrp('ol');$('selAn').onclick=()=>selGrp('an');$('selUn').onclick=()=>selGrp('un');")
rep("'ddlayout:v1'", "'ollayout:v1'", 2)
rep("'ddlayout/current'", "'ollayout/current'", 2)
rep("'ddlayout/b'", "'ollayout/b'")
rep("const FORMAT='dd-layout-1';", "const FORMAT='ol-layout-1';")
rep("filename:'desert_of_despair_layout.json'", "filename:'otherland_layout.json'")
bad = [w for w in ('ddlayout', "area==='DD'", "'dd'", 'selDd', 'Desert of Despair</span></h1>') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
