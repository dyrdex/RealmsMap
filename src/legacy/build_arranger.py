# Builds the map arranger page from the finished map page: python3 build_arranger.py <finished map html> <output html>
import sys, json, re, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import partition as P, lake_reshape as L
src=open(sys.argv[1]).read(); out=sys.argv[2]
i=src.index('const DATA=')+len('const DATA='); d=0
for j in range(i,len(src)):
    c=src[j]
    if c=='{': d+=1
    elif c=='}':
        d-=1
        if d==0: break
DATA=json.loads(src[i:j+1]); w=DATA['wild']
DATA['pieces']=P.pieces_json(w,w.get('strip') or L.STRIP)
DATA['round']=int(sys.argv[3]) if len(sys.argv)>3 else 2
head=src[:src.index('</style>')]
draw=src[src.index('const T=DATA.town'):src.index('/* ---------- camera ---------- */')]
css='''
#side{width:330px;flex:0 0 330px;overflow:auto}
#side header{padding:16px 18px 6px}
#side p.t{font-size:.88rem;line-height:1.42;margin:0 18px 6px;color:var(--ink)}
#side ul.how{margin:4px 18px 6px;padding-left:18px;font-size:.86rem;line-height:1.42}
#plist{list-style:none;margin:0;padding:0 10px 8px}
.pi{display:flex;align-items:center;gap:9px;padding:7px 8px;border-radius:8px;cursor:pointer;border:1px solid transparent}
.pi:hover{background:var(--paper)}.pi.on{background:var(--glow);border-color:var(--pick)}
.pi .sw{width:14px;height:14px;border-radius:4px;flex:0 0 14px}.pi .nm{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2}
.pi .nm b{font-family:var(--serif);font-size:1.02rem}.pi .nm i{font-size:.76rem;color:var(--soft);font-style:normal}
.pi .ic{all:unset;cursor:pointer;width:28px;height:28px;text-align:center;line-height:28px;border-radius:6px;font-size:1rem}.pi .ic:hover{background:var(--panel)}
.row{display:flex;gap:6px;flex-wrap:wrap;margin:5px 18px}
.btn,#side button.b{font:inherit;font-size:.86rem;padding:6px 10px;border-radius:7px;border:1px solid var(--edge);background:var(--paper);color:var(--ink);cursor:pointer}
#side button.b:hover{border-color:var(--pick)}#side button.b:disabled{opacity:.45;cursor:default}
#side button.primary{background:var(--pick);border-color:var(--pick);color:#fff;font-weight:700;padding:8px 14px}
#side button.warn{border-color:#C23B22;color:#C23B22}
label.l{display:flex;gap:7px;align-items:center;font-size:.86rem;margin:3px 18px;cursor:pointer}
.stat{font-size:.82rem;color:var(--soft);margin:4px 18px}.ok{color:#2F7A4F;font-weight:700}
#toast{position:absolute;top:12px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--panel);padding:7px 14px;border-radius:8px;font-size:.86rem;display:none;z-index:6}
#modal{position:absolute;inset:0;background:rgba(0,0,0,.45);display:none;align-items:center;justify-content:center;z-index:8}
#modal .box{background:var(--panel);border:1px solid var(--edge);border-radius:12px;padding:16px;width:min(640px,92%);max-height:88%;display:flex;flex-direction:column;gap:8px}
#modal textarea{width:100%;height:200px;font:12px ui-monospace,Menlo,Consolas,monospace;background:var(--paper);color:var(--ink);border:1px solid var(--edge);border-radius:7px;padding:8px;resize:vertical}
svg#map{cursor:default}
'''
body='''</style>
</head>
<body>
<div id="app">
  <aside id="side" aria-label="Pieces">
    <header><h1>Map arranger</h1><p class="sub">Move and resize the pieces of the map to try out a different arrangement.</p></header>
    <ul class="how">
      <li><b>Click a piece</b> to select it, <b>drag</b> it to move it.</li>
      <li><b>Drag a corner handle</b> to resize it (it keeps its proportions).</li>
      <li><b>Arrow keys</b> nudge it (Shift = bigger, Alt = finer). <b>[</b> and <b>]</b> shrink and grow it. <b>Ctrl+Z</b> undoes.</li>
      <li><b>Drag empty space</b> to pan, <b>scroll</b> to zoom.</li>
    </ul>
    <div class="gh">Pieces <span style="font-weight:400;text-transform:none;letter-spacing:0">(the top of the list is drawn on top)</span></div>
    <ul id="plist"></ul>
    <div class="row"><button class="b" id="undo">↶ Undo</button><button class="b" id="redo">↷ Redo</button><button class="b warn" id="resetAll">Put everything back…</button></div>
    <label class="l"><input type="checkbox" id="snap"> Snap moves to half a room</label>
    <div class="gh">Show</div>
    <label class="l"><input type="checkbox" id="vOut" checked> Outline every piece</label>
    <label class="l"><input type="checkbox" id="vNames" checked> Piece names</label>
    <div class="gh">Send your arrangement to Claude</div>
    <div class="row"><button class="b primary" id="saveDb">Save for Claude</button></div>
    <p class="stat" id="dbStat">Not saved yet.</p>
    <p class="t" style="color:var(--soft);font-size:.82rem">After you press it, tell me <b>"saved"</b> in the chat and I'll read your arrangement directly. If that button isn't available, use one of these:</p>
    <div class="row"><button class="b" id="dl">Download file</button><button class="b" id="txt">Copy / paste text…</button></div>
    <p class="stat" id="localStat"></p>
    <footer>This is a preview: each piece is the finished map, clipped to its area. Where pieces meet you will see their straight edges, and the trees, markers and text scale with the piece. Once you have an arrangement you like, I rebuild the real map from it with everything at its proper size and no seams.</footer>
  </aside>
  <main id="stage">
    <svg id="map" aria-label="Map arranger"><g id="world"></g></svg>
    <div id="toast"></div>
    <div id="tools"><button id="zin" aria-label="Zoom in">+</button><button id="zout" aria-label="Zoom out">−</button><button id="zfit" aria-label="Show everything">⤢</button></div>
    <div id="modal"><div class="box"><b style="font-family:var(--serif);font-size:1.1rem">Arrangement text</b>
      <p style="margin:0;font-size:.88rem">This is your current arrangement. To send it to me, copy it and paste it into the chat. To load one, paste it here and press <b>Load text</b>.</p>
      <textarea id="lt" spellcheck="false"></textarea>
      <div class="row" style="margin:0"><button class="b primary" id="mCopy">Copy</button><button class="b" id="mSel">Select all</button><button class="b" id="mLoad">Load text</button><button class="b" id="mClose">Close</button></div></div></div>
  </main>
</div>
<script>
const DATA=''' 
page=head+css+body+json.dumps(DATA,separators=(',',':'))+';\n(function(){\n'+draw+open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'arranger.js')).read()+'\n})();\n</script>\n</body>\n</html>\n'
page=page.replace('<title>The Realms</title>','<title>Map arranger</title>')
open(out,'w').write(page)
print('wrote',out,len(page)//1024,'KB; pieces',[p['name'] for p in DATA['pieces']])
