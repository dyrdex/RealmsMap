# Makes np_editor_template.html (the Northern Plains layout editor) from the Barren Peaks editor's template (already dark only).
#   python3 make_np_template.py ../barren_peaks_editor/bp_editor_template.html np_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

NPC = '#8DBA4E'                                                  # outline of the Plains rooms
rep('<title>Layout editor · Barren Peaks</title>', '<title>Layout editor · Northern Plains</title>')
rep('color:var(--soft)">Barren Peaks of Tahjliera</span></h1>', 'color:var(--soft)">Northern Plains</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b>The Northern Plains</b> (rooms with a <b style="color:{NPC}">green outline</b>) start where TinTin\'s exits put them, joined by trails to the Barren Peaks and the road. That is on top of <b>the Northern Trade Route past the long bridge</b> (rooms with a <b style="color:#D4B44A">gold outline</b>): its stretch in the Plains (from 4156 on) is movable here, starts where it is on the map now and is drawn on top of the Plains rooms; its stretch inside the Barren Peaks is fixed. The old road line past the bridge is left out of the background so you only see where the rooms are. A few Plains rooms have no link to anything and wait in a column to the east. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Select the Northern Plains</b> and <b>Select the road</b> grab those rooms; <b>Selected → where TinTin\'s exits suggest</b> sends the selected rooms back to their starting spot.</p>', regex=True)
rep("most of the Peaks' up/down rooms are also joined sideways through spacer rooms, so they start beside the ground level rather than on top of it.", "the Plains are all on one level.")
rep('<button id="selNtr">Select the Barren Peaks</button>', '<button id="selNtr">Select the Northern Plains</button><button id="selRoad">Select the road</button>')
rep('border:2px solid #B3541E"></i><span>Barren Peaks room (movable)</span>', f'border:2px solid {NPC}"></i><span>Northern Plains room (movable)</span>\n    <i style="background:var(--t-Mountains);border:2px solid #B3541E"></i><span>Barren Peaks room you unlocked (movable)</span>')
rep('<span>Fixed room on the Northern Trade Route (up to the bridge)</span>', '<span>Fixed room on the Northern Trade Route (up to and including the bridge)</span>\n    <i style="background:var(--cx-BP);border-radius:50%"></i><span>Fixed room in the Barren Peaks</span>')
rep('brown for the Northern Trade Route up to the bridge)', 'brown for the Northern Trade Route up to the bridge, rust for the Barren Peaks)')
rep('--cx-NTR:#A8875C;', '--cx-NTR:#A8875C;--cx-BP:#A86E52;')
rep('.nd.rd rect,.nd.rd circle.shape{stroke:#D4B44A}', '.nd.rd rect,.nd.rd circle.shape{stroke:#D4B44A}\n.nd.np rect,.nd.np circle.shape{stroke:' + NPC + '}\n.nd.pk rect,.nd.pk circle.shape{stroke:#B3541E}')
rep("(r.area==='BP'?' ntr':r.area==='RD'?' ntr rd':'')", "(r.area==='NP'?' ntr np':r.area==='RD'?' ntr rd':r.area==='PK'?' ntr pk':'')")
rep("r.area==='BP'?' · Barren Peaks':r.area==='RD'", "r.area==='NP'?' · Northern Plains':r.area==='PK'?' · Barren Peaks (movable)':r.area==='RD'")
rep("NTR:'Northern Trade Route'})[r.src]", "NTR:'Northern Trade Route',BP:'Barren Peaks'})[r.src]")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Northern Plains rooms: ${a.np}${a.removed?` (left out at your request, with their spacer rooms: ${a.removed})`:''}<br>Spacer rooms joined to them: ${a.spacers}<br>Pieces: ${a.pieces} (${a.sizes})<br>Exits between these rooms: ${a.exits}<br>Links to other rooms: ${a.links} (${a.linksrd} of them to the road)<br>Northern Trade Route rooms past the bridge (movable): ${a.road}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} · Shadow Grove ${a.grove} · Forgotten Woods ${a.fw} · Northern Trade Route ${a.ntr} up to the bridge, ${a.ntrpk} past it inside the Barren Peaks · Barren Peaks ${a.bp} (plus ${a.pk} you can move)<br><br>Not included: the Blood Sea, the Valley of the Elves and the other areas the Plains lead to, which are not mapped yet`})();", regex=True)
rep("$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='BP'||r.area==='RD')sel.add(r.id)});refreshSel()};",
    "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='NP')sel.add(r.id)});refreshSel()};\n$('selRoad').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='RD')sel.add(r.id)});refreshSel()};")
rep("'bplayout:v1'", "'nplayout:v1'", 2)
rep("'bplayout/current'", "'nplayout/current'", 2)
rep("'bplayout/b'", "'nplayout/b'")
rep("const FORMAT='bp-layout-1';", "const FORMAT='np-layout-1';")
rep("filename:'barren_peaks_layout.json'", "filename:'northern_plains_layout.json'")
# Oct 10 (owner): movable spacer rooms get a bigger invisible grab area; saves before v3 must not re-lock the rooms in D.unlocked;
# a save never moves a room that is fixed in this build (rooms locked later, e.g. the road inside the Barren Peaks)
rep("else if(r.void)el('circle',{class:'shape',r:.17,fill:'var(--t-other)',opacity:.85},g);", "else if(r.void){el('circle',{class:'shape',r:.17,fill:'var(--t-other)',opacity:.85},g);el('circle',{r:.36,fill:'transparent'},g)}")
rep("return {format:FORMAT,v:2,savedAt:", "return {format:FORMAT,v:4,savedAt:")
rep("(o.locked||[]).forEach(id=>{if(pos.has(id)&&(o.v||!(D.unlocked||[]).includes(id)))locked.add(id)});", "(o.locked||[]).forEach(id=>{if(pos.has(id)&&((o.v||0)>=4||!(D.unlocked||[]).includes(id)))locked.add(id)});")
rep("const id=o.ids[i];if(pos.has(id))list.push(", "const id=o.ids[i];if(pos.has(id)&&!byId.get(id).fixed)list.push(")
assert 'bplayout' not in t and "area==='BP'" not in t
open(out, 'w', encoding='utf-8').write(t)
print('ok')
