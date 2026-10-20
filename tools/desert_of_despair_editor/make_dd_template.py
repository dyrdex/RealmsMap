# Makes dd_editor_template.html (the layout editor for the Desert of Despair) from the Mire editor's template (dark only).
#   python3 make_dd_template.py ../mire_editor/mi_editor_template.html dd_editor_template.html
# Changes: names, save keys, legend (desert rooms; fixed Wastelands, Southern Mountain Range, the entrance 6365 and other map rooms).
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

DDC, DDX, MIX, NX, WLC, CDC = '#E6C36A', '#F2E2A0', '#7FCB8E', '#8C8C8C', '#D98A5B', '#E07A9A'                     # outlines: desert rooms; fixed: entrance 6365, Mire, other map rooms
rep('<title>Layout editor · The Mire</title>', '<title>Layout editor · Desert of Despair</title>')
rep('>The Mire</span></h1>', '>Desert of Despair</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b style="color:{DDC}">Desert of Despair</b>: all its rooms and the spacer rooms that join them. Its exits into the Azure Sea, Great Eastern Desert, Emerald Hills, The Dungeon, Thul Ab\'hara, Daichaal and The Barren Wastes are left off. It joins the map at its entrance 6365 (off the Southern Mountain Range, where the route ends) and at the Wastelands\' desert fringe (west). The Wastelands rooms round the desert (rust outline) and the Coral Depths editor\'s rooms north of it (pink outline) are unlocked too, starting where they are on the map. The area is split into <b>sections</b> (parts with only a few exits between them). Each section starts where TinTin\'s exits put its rooms, two rooms apart; the sections are spread out over the empty ground east of the Wastelands with gaps between them, so some exits between sections (and to the map) are stretched. Rooms on another level are offset diagonally (up = north-east). Hide any room you don\'t want on the map. <b>Select a section</b> grabs a whole section to move it; <b>Select the whole piece</b> grabs the sections of the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selMi">Select the Mire rooms</button>', '<button id="selDd">Select the desert rooms</button><button id="selWl">Select the Wastelands rooms</button><button id="selCd">Select the Coral Depths rooms</button>')
rep(r'    <i style="background:var\(--t-Swamp\);border:2px solid #7FCB8E"></i>.*?\(movable, start next to the rooms they join\)</span>\n',
    f'    <i style="background:var(--t-Desert);border:2px solid {DDC}"></i><span>Desert of Despair room (movable)</span>\n'
    '    <i style="background:var(--t-Hills);border:2px solid #6FC3E8"></i><span>Unlocked map room: the entrance 6365 (movable, starts at its spot on the map)</span>\n'
    f'    <i style="background:var(--t-Desert);border:2px solid {WLC}"></i><span>Unlocked Wastelands room: those round the desert, spacer rooms included (movable, start at their spots on the map)</span>\n'
    f'    <i style="background:var(--t-Water);border:2px solid {CDC}"></i><span>Unlocked room from the Coral Depths editor: Coral Depths 2518-2531, the Azure Sea rooms north of the desert and their spacers (movable, start at their spots on the map)</span>\n', regex=True)
rep('<span>Fixed room in the Wastelands</span>\n',
    '<span>Fixed room in the Wastelands</span>\n'
    '    <i style="background:var(--cx-MI);border-radius:50%"></i><span>Fixed room in the Mire</span>\n    <i style="background:var(--cx-N);border-radius:50%"></i><span>Other fixed room on the map</span>\n')
rep('--cx-WL:#D9B26F', f'--cx-WL:#D9B26F;--cx-DD:{DDX};--cx-MI:{MIX};--cx-N:{NX}')
rep('.nd.mi rect,.nd.mi circle.shape{stroke:#7FCB8E}\n.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}\n.nd.om rect,.nd.om circle.shape{stroke:#E0A458}', f'.nd.dd rect,.nd.dd circle.shape{{stroke:{DDC}}}\n.nd.un rect,.nd.un circle.shape{{stroke:#6FC3E8}}\n.nd.wl rect,.nd.wl circle.shape{{stroke:{WLC}}}\n.nd.cd rect,.nd.cd circle.shape{{stroke:{CDC}}}')
rep("(r.area==='MI'?' ntr '+r.grp:'')", "(r.area==='DD'?' ntr '+r.grp:'')")
rep("${r.area==='MI'?' · The Mire'", "${r.area==='DD'?' · Desert of Despair'")
rep("WL:'Wastelands'})[r.src]", "WL:'Wastelands',DD:'Desert of Despair',MI:'The Mire'})[r.src]")
rep("Mire rooms: ${a.mi} · spacers ${a.mis}", "Desert rooms: ${a.dd} · spacers ${a.dds}")
rep("(near the Mire)", "(near the desert)")
rep("$('selMi').onclick=()=>selGrp('mi');", "$('selDd').onclick=()=>selGrp('dd');$('selWl').onclick=()=>selGrp('wl');$('selCd').onclick=()=>selGrp('cd');")
rep("'milayout:v1'", "'ddlayout:v1'", 2)
rep("'milayout/current'", "'ddlayout/current'", 2)
rep("'milayout/b'", "'ddlayout/b'")
rep("const FORMAT='mi-layout-1';", "const FORMAT='dd-layout-1';")
rep("filename:'mire_layout.json'", "filename:'desert_of_despair_layout.json'")
bad = [w for w in ('milayout', "area==='MI'", "'mi'", 'selMi', 'The Mire</span></h1>') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
