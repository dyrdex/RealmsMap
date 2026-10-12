import re
t = open('ashen_editor2.html', encoding='utf-8').read()
L = t.split('\n')
def line_idx(prefix, start=0):
    for i in range(start, len(L)):
        if L[i].startswith(prefix): return i
    raise SystemExit('not found: ' + prefix)
def sub_line(prefix, new):
    L[line_idx(prefix)] = new
def rep(a, b, cnt=1):
    global t
    assert t.count(a) == cnt, (t.count(a), a[:80]); t = t.replace(a, b)
# ---- text and style (line based, since some of the original lines carry non-ASCII characters) ----
for i, l in enumerate(L):
    if l.startswith('<title>'): L[i] = '<title>Layout editor \u00b7 Northern Trade Route</title>'
    elif l.startswith('  <h1>Layout editor'): L[i] = '  <h1>Layout editor<br><span style="font-size:.62em;font-weight:500;color:var(--soft)">Northern Trade Route</span></h1>'
    elif l.startswith('.nd.etr rect'): L[i] = '.nd.ntr rect,.nd.ntr circle.shape{stroke:#B3541E;stroke-width:.17}'
    elif l.startswith('.nd.kc rect') or l.startswith('.nd.ex rect'): L[i] = ''
    elif l.startswith('.nd.fx{cursor:not-allowed}'): L[i] = '.nd.fx{cursor:not-allowed}.nd.fx .lbl{display:none}\nsvg line.cxe{pointer-events:none}'
    elif l.startswith('  <p id="etrNote"'):
        L[i] = ('  <p id="ntrNote" style="margin:4px 0 8px"><b>The Northern Trade Route</b> (rooms with an <b style="color:#B3541E">orange outline</b>) runs from the gate north of Darkhaven, through the Shadow Grove, and winds through the Forgotten Woods. '
                'It starts off to the east of everything, with trails to the rooms it connects to, so you can drag it into place. <b>Select the Northern Trade Route</b> below grabs all of it at once, and '
                '<b>Selected \u2192 where TinTin\'s exits suggest</b> sends the selected rooms to where your map\'s own exits put them (on top of the Grove and the Woods).</p>')
    elif l.startswith('  <p><b>The fixed rooms</b>'):
        L[i] = ('  <p><b>The fixed rooms</b> (small round dots, grey-blue for Darkhaven, violet for the Shadow Grove, green for the Forgotten Woods) are the rooms already on the finished map, exactly where they are. '
                'They can\'t be moved. Hover one to see its name. The faint lines between them are the exits between those rooms. The finished map (land, lake, the Woods\' trails) is faintly behind.</p>')
    elif l.startswith('  <p style="color:var(--soft)">Rooms start exactly'):
        L[i] = ('  <p style="color:var(--soft)">The road\'s rooms start in the shape TinTin\'s own exits give them (north is up). Rooms on a level above or below ground have a dashed outline. '
                'Up and down exits are dashed purple lines.</p>')
    elif l.startswith('    <button id="selEtr">'): L[i] = '    <button id="selNtr">Select the Northern Trade Route</button>'
t = '\n'.join(L)
# ---- the legend ----
a = t.index('<div class="legend">'); b = t.index('</div>', a) + 6
t = t[:a] + '''<div class="legend">
    <i style="background:var(--t-Forest);border:2px solid #B3541E"></i><span>Northern Trade Route room (movable)</span>
    <i style="background:var(--t-other);border-radius:50%;width:8px;height:8px;border:1px solid #B3541E"></i><span>Spacer room of the road (invisible in the game, free to move)</span>
    <i style="background:var(--cx-DH);border-radius:50%"></i><span>Fixed room in Darkhaven</span>
    <i style="background:var(--cx-Grove);border-radius:50%"></i><span>Fixed room in the Shadow Grove</span>
    <i style="background:var(--cx-FW);border-radius:50%"></i><span>Fixed room in the Forgotten Woods</span>
    <i style="border:2px dashed var(--ud);background:none"></i><span>On a level above or below ground</span>
    <i style="background:var(--ctx-land)"></i><span>Land on the finished map</span><i style="background:var(--ctx-water)"></i><span>The lake</span>
  </div>''' + t[b:]
# ---- colours for the fixed rooms (light and dark) ----
rep('</style>', ''':root{--cx-DH:#7F96B0;--cx-Grove:#A08FBD;--cx-FW:#7FA67C;--cx-edge:#8C998C}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--cx-DH:#6F86A2;--cx-Grove:#9080AE;--cx-FW:#6E9A6C;--cx-edge:#7E8B7E}}
:root[data-theme="dark"]{--cx-DH:#6F86A2;--cx-Grove:#9080AE;--cx-FW:#6E9A6C;--cx-edge:#7E8B7E}
</style>''')
# ---- edges: the exits between two fixed rooms are drawn faint and thin ----
rep("  if(kind==='two'){o.els.push(mk(gWide,'w'+(inside?' mz':''),{stroke:'var(--dirt)','stroke-width':.34,opacity:.8}));",
    "  const cxEdge=byId.get(a).fixed&&byId.get(b).fixed;\n  if(cxEdge){o.els.push(mk(gThin,'cxe'+(kind==='ud'?' ud':''),{stroke:kind==='ud'?'var(--ud)':'var(--cx-edge)','stroke-width':.05,opacity:.55}))}\n  else if(kind==='two'){o.els.push(mk(gWide,'w'+(inside?' mz':''),{stroke:'var(--dirt)','stroke-width':.34,opacity:.8}));")
# ---- rooms: fixed rooms are small dots; the road's rooms have an orange outline ----
rep("(r.area==='ETR'?' etr':'')+(r.area==='KC'?' kc':'')+(r.area==='EX'?' ex':'')", "(r.area==='NTR'?' ntr':'')")
rep("  if(r.fixed)el('rect',{x:-.46,y:-.46,width:.92,height:.92,rx:.1,transform:'rotate(45)',fill:'var(--paper)',stroke:'var(--pick)','stroke-width':.16},g);",
    "  if(r.fixed){el('circle',{class:'shape cxs',r:r.void?.12:.27,fill:'var(--cx-'+r.src+')',stroke:'var(--paper)','stroke-width':.05,opacity:.95},g);el('circle',{r:.42,fill:'transparent'},g)}")
# ---- overlaps: two fixed rooms are never flagged (the finished map decides those) ----
rep("if(o<=id||byId.get(o).void)continue;", "if(o<=id||byId.get(o).void||(byId.get(id).fixed&&byId.get(o).fixed))continue;")
# ---- the import check ----
a = t.index("(function(){const a=D.audit;if(!a)return;"); b = t.index("})();", a) + 5
t = t[:a] + ("(function(){const a=D.audit;if(!a)return;$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Northern Trade Route rooms: ${a.ntr} (the road from its entrance to the long bridge)<br>Spacer rooms on it: ${a.spacers}<br>Exits between road rooms: ${a.exits} of ${a.exits_total} drawn<br>Links to rooms already on the map: ${a.links}<br><br><b>Fixed rooms already on the finished map:</b><br>Darkhaven ${a.dh} \u00b7 Shadow Grove ${a.grove} \u00b7 Forgotten Woods ${a.fw}<br><br>Not included: ${a.beyond} more road rooms past the bridge, in the Barren Peaks and the Northern Plains, which are not mapped yet`})();") + t[b:]
# ---- tooltips and the area buttons ----
a = t.index("${r.area==='ETR'?"); b = t.index("${r.lvl?`", a)
t = t[:a] + "${r.area==='NTR'?' \u00b7 Northern Trade Route':(r.src?' \u00b7 '+({DH:'Darkhaven',Grove:'Shadow Grove',FW:'Forgotten Woods'})[r.src]+' (fixed)':'')}" + t[b:]
a = t.index("$('selEtr').onclick="); b = t.index("$('selAf').onclick=", a); b2 = t.index('\n', b) + 1
t = t[:a] + "$('selNtr').onclick=()=>{sel.clear();rooms.forEach(r=>{if(r.area==='NTR')sel.add(r.id)});refreshSel()};\n" + t[b2:]
# ---- storage: its own format and its own places, so nothing is shared with the other editors ----
rep("const FORMAT='ash-layout-2';", "const FORMAT='ntr-layout-1';")
t = t.replace("ashlayout:v2", "ntrlayout:v1").replace("ashlayout2/", "ntrlayout/")
t = t.replace("ashen_forest_layout_2.json", "northern_trade_route_layout.json")
t = t.replace('r.ex.map', '(r.ex||[]).map').replace('r.ex.length', '(r.ex||[]).length')
open('ntr_editor.html', 'w', encoding='utf-8').write(t)
print('template written', len(t) // 1024, 'KB; left-over Ashen/ETR mentions:', [k for k in ('Ashen','ETR','KC','selAf','selEtr','selAdded','ashlayout') if k in t])
