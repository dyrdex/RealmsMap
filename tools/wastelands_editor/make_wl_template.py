# Makes wl_editor_template.html (the layout editor for the Wastelands) from the Angel's Landing / Edo / Grimdog editor's template (dark only).
#   python3 make_wl_template.py ../new_areas_editor/na_editor_template.html wl_editor_template.html
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def rep(a, b, count=1, regex=False):
    global t
    if regex: t, n = re.subn(a, lambda m: b, t, flags=re.S)
    else: n = t.count(a); t = t.replace(a, b)
    assert n == count, (a[:60], n)

WLC = '#E8C27A'                                                                  # outline: Wastelands
rep("<title>Layout editor · Angel's Landing, Edo, Grimdog</title>", '<title>Layout editor · Wastelands</title>')
rep(">Angel's Landing · Edo · Grimdog</span></h1>", '>Wastelands</span></h1>')
rep(r'<p id="ntrNote".*?</p>', f'<p id="ntrNote" style="margin:4px 0 8px"><b style="color:{WLC}">The Wastelands</b>: all its 351 rooms (the 13 underwater rooms and the 6 tunnel rooms included) and the spacer rooms that join them. Its exits into the Blood Sea and the Sea of Sorrows are left off, and so are the other areas it leads to. The rooms start where TinTin\'s exits put them, one room apart, from the Southern Mountain Range rooms 34-36 and the Southern Mountain Trade Route rooms 9339 and 9346; rooms on another level are offset diagonally (up = north-east). Rooms with no exit to the rest are parked just east of the area. The map grows south to fit them. Hide any room you don\'t want on the map. <b>Select the whole piece</b> grabs every room in the same piece as the rooms you have selected; <b>Selected → where TinTin\'s exits suggest</b> moves the selected rooms back to their starting spots.</p>', regex=True)
rep("<button id=\"selAl\">Angel's Landing</button><button id=\"selEdo\">Village of Edo</button><button id=\"selGp\">Grimdog Port Authority</button>",
    '<button id="selWl">Select the Wastelands rooms</button>')
rep(r'    <i style="background:var\(--t-Field\);border:2px solid #9FB4FF"></i>.*?Western Trade Route room 21076 \(movable\)</span>\n',
    f'    <i style="background:var(--t-Desert);border:2px solid {WLC}"></i><span>Wastelands room (movable)</span>\n', regex=True)
rep('.nd.al rect,.nd.al circle.shape{stroke:#9FB4FF}\n.nd.edo rect,.nd.edo circle.shape{stroke:#F2A65A}\n.nd.gp rect,.nd.gp circle.shape{stroke:#5FD3B5}',
    f'.nd.wl rect,.nd.wl circle.shape{{stroke:{WLC}}}')
rep("(r.area==='NA'?' ntr '+r.grp:'')", "(r.area==='WL'?' ntr '+r.grp:'')")
rep("${r.area==='NA'?' · '+({al:\"Angel's Landing\",edo:'Village of Edo',gp:'Grimdog Port Authority'})[r.grp]", "${r.area==='WL'?' · '+({wl:'Wastelands'})[r.grp]")
rep("CD:'Coral Depths'})[r.src]", "CD:'Coral Depths',NA:\"Angel's Landing, Village of Edo\"})[r.src]")
rep(r"\$\('audit'\)\.innerHTML=`.*?`\}\)\(\);",
    "$('audit').innerHTML=`<b>Import check against your TinTin map:</b><br>Wastelands rooms: ${a.wl} · spacers ${a.wls}<br>Exits between these rooms: ${a.exits}<br>Exits to rooms on the map: ${a.links}<br>Exits left off: Blood Sea ${a.bs}, Sea of Sorrows ${a.ss}, other areas ${a.oth}<br><br>Fixed rooms already on the finished map (near the Wastelands): ${a.fixed}`})();", regex=True)
rep("$('selAl').onclick=()=>selGrp('al');$('selEdo').onclick=()=>selGrp('edo');$('selGp').onclick=()=>selGrp('gp');", "$('selWl').onclick=()=>selGrp('wl');")
rep("'nalayout:v1'", "'wllayout:v1'", 2)
rep("'nalayout/current'", "'wllayout/current'", 2)
rep("'nalayout/b'", "'wllayout/b'")
rep("const FORMAT='na-layout-1';", "const FORMAT='wl-layout-1';")
rep("filename:'new_areas_layout.json'", "filename:'wastelands_layout.json'")
bad = [w for w in ('nalayout', "area==='NA'", '#9FB4FF', "grp==='al'", 'selAl') if w in t]
assert not bad, bad
open(out, 'w', encoding='utf-8').write(t)
print('ok')
