# Makes mi_editor_template.html (the layout editor for The Mire) from the Wastelands editor's template (dark only).
#   python3 make_mi_template.py ../wastelands_editor/wl_editor_template.html mi_editor_template.html
# Additions: 'Select a section' list (the starting layout's sections = r.piece, names in D.secs); section name in the room tooltip; Wastelands fixed rooms.
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

MIC, WLX = '#7FCB8E', '#D9B26F'                                                     # outlines: Mire rooms; fixed Wastelands rooms
rep('<title>Layout editor · Wastelands</title>', '<title>Layout editor · The Mire</title>')
rep('>Wastelands</span></h1>', '>The Mire</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b style="color:{MIC}">The Mire</b>: all its 488 rooms and the spacer rooms that join them. Its exits into the Blood Sea, Dragon Tower, Old Marsh and the other areas it leads to are left off. It joins the map at the Forest of Tears (north-west), the Southern Mountain Range and the Wastelands (east). The area is split into <b>sections</b> (parts with only a few exits between them). Each section starts where TinTin\'s exits put its rooms, two rooms apart; the sections are spread out over the empty ground south-west of the map with wide gaps between them, so the exits between sections (and to the map) are stretched. Rooms on another level are offset diagonally (up = north-east). Rooms with no exit to the rest are parked near the area. Hide any room you don\'t want on the map. <b>Select a section</b> grabs a whole section to move it; <b>Select the whole piece</b> grabs the sections of the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep('<button id="selWl">Select the Wastelands rooms</button><button id="selUn">Select the unlocked map rooms</button>',
    '<button id="selMi">Select the Mire rooms</button></div>\n  <div class="row"><select id="selSec" aria-label="Select a section"><option value="">Select a section…</option></select>')
rep(r'    <i style="background:var\(--t-Desert\);border:2px solid #E8C27A"></i>.*?\(movable, starts at its spot on the map\)</span>\n',
    f'    <i style="background:var(--t-Swamp);border:2px solid {MIC}"></i><span>Mire room (movable)</span>\n    <i style="background:var(--t-Hills);border:2px solid #6FC3E8"></i><span>Unlocked map room: Southern Mountain Range 110-116; Wastelands 8606, 8608, 8610, 8611, 8614 and spacers 10045, 10049 (movable, start at their spots on the map)</span>\n    <i style="background:var(--t-Swamp);border:2px solid #E0A458"></i><span>Added Oct 18: the Old Marsh rooms, Dragon Tower rooms 7940, 8155 the Dragon\'s Pass shortcut 655, 8209, 8212, 8214, 8221 and the way down to Shadowport 10050-10099 (movable, start next to the rooms they join)</span>\n', regex=True)
rep('<span>Fixed room in the Southern Mountain Range or on its trade route</span>\n',
    f'<span>Fixed room in the Southern Mountain Range or on its trade route</span>\n    <i style="background:var(--cx-WL);border-radius:50%"></i><span>Fixed room in the Wastelands</span>\n')
rep('copper for the Southern Mountain Range and its trade route)', 'copper for the Southern Mountain Range and its trade route, tan for the Wastelands)')
rep('--cx-SM:#C98A5B', f'--cx-SM:#C98A5B;--cx-WL:{WLX}')
rep('.nd.wl rect,.nd.wl circle.shape{stroke:#E8C27A}\n.nd.un rect,.nd.un circle.shape{stroke:#6FC3E8}', f'.nd.mi rect,.nd.mi circle.shape{{stroke:{MIC}}}\n.nd.un rect,.nd.un circle.shape{{stroke:#6FC3E8}}\n.nd.om rect,.nd.om circle.shape{{stroke:#E0A458}}')
rep("(r.area==='WL'?' ntr '+r.grp:'')", "(r.area==='MI'?' ntr '+r.grp:'')")
rep("${r.area==='WL'?' · '+({wl:'Wastelands',un:'unlocked map room'})[r.grp]", "${r.area==='MI'?' · The Mire'")
rep("NA:\"Angel's Landing, Village of Edo\"})[r.src]", "NA:\"Angel's Landing, Village of Edo\",WL:'Wastelands'})[r.src]")
rep("${r.piece!=null?' · piece '+(r.piece+1):''}", "${r.piece!=null&&D.secs?'<br>Section '+(r.piece+1)+': '+esc(D.secs[r.piece].name):''}")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Mire rooms: ${a.mi} · spacers ${a.mis}<br>Sections: ${a.secs}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br>Exits left off: ${a.off}<br><br>Fixed rooms already on the finished map (near the Mire): ${a.fixed}`})();", regex=True)
rep("$('selWl').onclick=()=>selGrp('wl');$('selUn').onclick=()=>selGrp('un');",
    "$('selMi').onclick=()=>selGrp('mi');\n(D.secs||[]).forEach(s=>{const o=document.createElement('option');o.value=s.i;o.textContent=`${s.i+1}. ${s.name} (${s.n})`;$('selSec').appendChild(o)});\n"
    "$('selSec').onchange=e=>{const v=e.target.value;if(v==='')return;const i=+v;sel.clear();rooms.forEach(r=>{if(!r.fixed&&r.piece===i)sel.add(r.id)});refreshSel();e.target.value=''};")
rep("'wllayout:v1'", "'milayout:v1'", 2)
rep("'wllayout/current'", "'milayout/current'", 2)
rep("'wllayout/b'", "'milayout/b'")
rep("const FORMAT='wl-layout-1';", "const FORMAT='mi-layout-1';")
rep("filename:'wastelands_layout.json'", "filename:'mire_layout.json'")
bad = [w for w in ('wllayout', "area==='WL'", '#E8C27A', "grp==='wl'", 'selWl', 'selUn') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
