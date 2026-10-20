# Makes wl3_editor_template.html (the Wastelands layout editor, v3, Oct 20: the new Sea of Sorrows / Blood Sea rooms) from the Desert of
# Despair editor's template (dark only).
#   python3 make_wl3_template.py ../desert_of_despair_editor/dd_editor_template.html wl3_editor_template.html
# Changes: names, save keys (new format, so the Oct 17 save isn't laid over today's map), legend (new sea rooms; unlocked beach rooms), no sections.
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

SSC, WLC = '#6FB7F0', '#E8C27A'                                                     # outlines: new sea rooms; unlocked beach rooms
rep('<title>Layout editor · Desert of Despair</title>', '<title>Layout editor · Wastelands</title>')
rep('>Desert of Despair</span></h1>', '>Wastelands · Sea of Sorrows and Blood Sea rooms</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b style="color:{SSC}">New sea rooms</b>: the rooms you listed from the Sea of Sorrows and the Blood Sea (with Winterlight Island 9841, 9842) and the spacer rooms that join them to each other and to the beaches. They start where TinTin\'s exits put them, two rooms apart, south of the beaches; rooms on another level are offset diagonally (up = north-east). Their exits to other sea rooms are left off. <b style="color:{WLC}">Beaches of Sorrow</b> and <b style="color:{WLC}">The Wasted Shores of Ahtborne</b> and the spacer rooms joined to them are unlocked, starting where they are on the map. Everything else is fixed where it is on today\'s map. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selDd">Select the desert rooms</button><button id="selWl">Select the Wastelands rooms</button><button id="selCd">Select the Coral Depths rooms</button><button id="selGe">Select the added rooms</button>',
    '<button id="selSs">Select the new sea rooms</button><button id="selWl">Select the beach rooms</button>')
rep('  <div class="row"><select id="selSec" aria-label="Select a section"><option value="">Select a section…</option></select>\n  </div>\n', '')
rep(r'    <i style="background:var\(--t-Desert\);border:2px solid #E6C36A"></i>.*?\(movable, start next to the rooms they join in your saved layout\)</span>\n',
    f'    <i style="background:var(--t-Water);border:2px solid {SSC}"></i><span>New sea room (movable)</span>\n'
    f'    <i style="background:var(--t-Desert);border:2px solid {WLC}"></i><span>Unlocked Wastelands room: Beaches of Sorrow, The Wasted Shores of Ahtborne and the spacer rooms joined to them (movable, start at their spots on the map)</span>\n', regex=True)
rep('.nd.dd rect,.nd.dd circle.shape{stroke:#E6C36A}\n.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}\n.nd.wl rect,.nd.wl circle.shape{stroke:#D98A5B}\n.nd.cd rect,.nd.cd circle.shape{stroke:#E07A9A}\n.nd.ge rect,.nd.ge circle.shape{stroke:#B58CE6}',
    f'.nd.ss rect,.nd.ss circle.shape{{stroke:{SSC}}}\n.nd.wl rect,.nd.wl circle.shape{{stroke:{WLC}}}')
rep("(r.area==='DD'?' ntr '+r.grp:'')", "(r.area==='WL'?' ntr '+r.grp:'')")
rep("${r.area==='DD'?' · Desert of Despair'", "${r.area==='WL'?' · '+({ss:'new sea room',wl:'unlocked beach room'})[r.grp]")
rep("N:'Northern Plains, Barren Peaks and the Northern Trade Route'", "N:'other area'")
rep("Desert rooms: ${a.dd} · spacers ${a.dds}<br>Sections: ${a.secs}", "New sea rooms: ${a.ss} · spacers ${a.sss}<br>Beach rooms unlocked: ${a.wl} · spacers ${a.wls}")
rep("(near the desert)", "(near these rooms)")
rep("$('selDd').onclick=()=>selGrp('dd');$('selWl').onclick=()=>selGrp('wl');$('selCd').onclick=()=>selGrp('cd');$('selGe').onclick=()=>selGrp('ge');", "$('selSs').onclick=()=>selGrp('ss');$('selWl').onclick=()=>selGrp('wl');")
rep("(D.secs||[]).forEach(s=>{const o=document.createElement('option');o.value=s.i;o.textContent=`${s.i+1}. ${s.name} (${s.n})`;$('selSec').appendChild(o)});\n", '')
rep("$('selSec').onchange=e=>{const v=e.target.value;if(v==='')return;const i=+v;sel.clear();rooms.forEach(r=>{if(!r.fixed&&r.piece===i)sel.add(r.id)});refreshSel();e.target.value=''};\n", '')
rep("'ddlayout:v1'", "'wllayout:v3'", 2)
rep("'ddlayout/current'", "'wllayout/current'", 2)
rep("'ddlayout/b'", "'wllayout/b'")
rep("const FORMAT='dd-layout-1';", "const FORMAT='wl-layout-3';")
rep("filename:'desert_of_despair_layout.json'", "filename:'wastelands_layout.json'")
bad = [w for w in ('ddlayout', "area==='DD'", "'dd'", 'selDd', 'selSec', 'selGe', 'Desert of Despair</span></h1>') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
