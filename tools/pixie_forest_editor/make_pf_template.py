# Makes pf_editor_template.html (the Pixie Forest layout editor) from the Miden'nir editor's template (dark only).
#   python3 make_pf_template.py ../midennir_editor/md_editor_template.html pf_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

PFC, ANC, FWC = '#C77DD9', '#5BB8E0', '#8DBA4E'                                      # outlines: Pixie Forest, Asgard Nexus, unlocked Forgotten Woods rooms
rep("<title>Layout editor · Miden'nir</title>", '<title>Layout editor · Pixie Forest</title>')
rep(">Miden'nir</span></h1>", '>The Pixie Forest</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px">The rooms you listed: 10 rooms of the <b>Pixie Forest</b> (<b style="color:{PFC}">violet outline</b>) and 4 of the <b>Asgard Nexus</b> (<b style="color:{ANC}">blue outline</b>), the rooms the paths to A\'enari and Reomyr Village run through, and the Forgotten Woods rooms <b>4017, 4018, 4019</b> (<b style="color:{FWC}">green outline</b>, unlocked: they start where the map has them). The Pixie Forest rooms start where TinTin\'s exits put them, from room 4019 (and they also link to room 4015 in the Forgotten Woods). The Asgard Nexus is entered with <b>enter</b> (no compass direction), so 5019 starts one step north-east of 5018. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep(r'<p style="color:var\(--soft\)">North is up\..*?</p>', '<p style="color:var(--soft)">North is up. Up and down exits are dashed purple lines.</p>', regex=True)
rep('<button id="selNtr">Select Miden\'nir</button>', '<button id="selNtr">Select the Pixie Forest rooms</button><button id="selAn">Select the Asgard Nexus rooms</button><button id="selFw">Select rooms 4017-4019</button>')
rep("<span>Miden'nir room (movable)</span>", '<span>Pixie Forest room (movable)</span>')
rep(f'border:2px solid #D97A8A">', f'border:2px solid {PFC}">')
rep("    <i style=\"background:var(--t-Forest);border:2px solid #C77DD9\"></i><span>Pixie Forest room (movable)</span>\n",
    f"    <i style=\"background:var(--t-Forest);border:2px solid {PFC}\"></i><span>Pixie Forest room (movable)</span>\n    <i style=\"background:var(--t-Forest);border:2px solid {ANC}\"></i><span>Asgard Nexus room (movable)</span>\n    <i style=\"background:var(--t-Forest);border:2px solid {FWC}\"></i><span>Forgotten Woods room 4017, 4018 or 4019 (unlocked, movable)</span>\n")
rep('.nd.md rect,.nd.md circle.shape{stroke:#D97A8A}', f'.nd.pf rect,.nd.pf circle.shape{{stroke:{PFC}}}\n.nd.an rect,.nd.an circle.shape{{stroke:{ANC}}}\n.nd.fw rect,.nd.fw circle.shape{{stroke:{FWC}}}')
rep("(r.area==='MD'?' ntr '+r.grp:'')", "(r.area==='PF'?' ntr '+r.grp:'')")
rep("${r.area==='MD'?\" · Miden'nir\"+(r.void?' (spacer room)':''):", "${r.area==='PF'?' · '+({pf:'Pixie Forest',an:'Asgard Nexus',fw:'Forgotten Woods (unlocked)'})[r.grp]+(r.void?' (spacer room)':''):")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Pixie Forest rooms: ${a.pf}<br>Asgard Nexus rooms: ${a.an}<br>Forgotten Woods rooms unlocked: ${a.fw}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fwfix}<br>Forest of Tears ${a.ft} · Lake of Tich'Pyga ${a.lake} · Western Trade Route ${a.wtr}<br>Ashen Forest ${a.af} · Southern Mountain Range and its trade route ${a.sm}<br><br>Only the rooms you listed; the rest of the Pixie Forest and the Asgard Nexus stay off.`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='MD'&&!r.void)sel.add(r.id)});refreshSel()};",
    "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='pf')sel.add(r.id)});refreshSel()};\n$('selAn').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='an')sel.add(r.id)});refreshSel()};\n$('selFw').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.grp==='fw')sel.add(r.id)});refreshSel()};")
rep("'mdlayout:v1'", "'pflayout:v1'", 2)
rep("'mdlayout/current'", "'pflayout/current'", 2)
rep("'mdlayout/b'", "'pflayout/b'")
rep("const FORMAT='md-layout-1';", "const FORMAT='pf-layout-1';")
rep("filename:'midennir_layout.json'", "filename:'pixie_forest_layout.json'")
bad = [w for w in ('mdlayout', "area==='MD'", "Miden'nir room", '#D97A8A') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
