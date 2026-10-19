/* ---------- arranger: the map as pieces you can move and resize ---------- */
const NS2='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id);
function el(tag,attrs,parent){const e=document.createElementNS(NS2,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e}

// the finished map is drawn once, then shown as one clipped copy per piece
const content=el('g',{id:'content'});
while(world.firstChild)content.appendChild(world.firstChild);
const defs=el('defs',{},world);defs.appendChild(content);
const pieceLayer=el('g',{id:'pieces'},world),ovLayer=el('g',{id:'ov'},world);
const PC=DATA.pieces,st=new Map(),base=new Map();
const ctx=document.createElement('canvas').getContext('2d');
PC.forEach(p=>{
  p.ax=(p.box[0]+p.box[2])/2;p.ay=(p.box[1]+p.box[3])/2;p.path=new Path2D(p.d);
  st.set(p.id,{tx:0,ty:0,s:1,locked:!!p.locked});base.set(p.id,{tx:0,ty:0,s:1});
  const cp=el('clipPath',{id:'cp_'+p.id},defs);el('path',{d:p.d,'clip-rule':'evenodd'},cp);
  p.g=el('g',{id:'pc_'+p.id,class:'pc'},pieceLayer);el('use',{href:'#content','clip-path':`url(#cp_${p.id})`},p.g);
});
const byId=Object.fromEntries(PC.map(p=>[p.id,p]));
const tf=(p,s)=>`translate(${(p.ax+s.tx).toFixed(3)} ${(p.ay+s.ty).toFixed(3)}) scale(${s.s.toFixed(4)}) translate(${-p.ax} ${-p.ay})`;
const applyPiece=p=>p.g.setAttribute('transform',tf(p,st.get(p.id)));

/* ---------- camera ---------- */
let cam={x:0,y:0,k:5},VW=0,VH=0;
function apply(){world.setAttribute('transform',`translate(${VW/2-cam.x*cam.k},${VH/2-cam.y*cam.k}) scale(${cam.k})`);drawOv()}
function fitAll(){const b=DATA.wild.bounds,r=svg.getBoundingClientRect();VW=r.width;VH=r.height;const k=Math.min(VW/(b[2]-b[0]+8),VH/(b[3]-b[1]+8));cam={x:(b[0]+b[2])/2,y:(b[1]+b[3])/2,k};apply()}
const toW=e=>{const r=svg.getBoundingClientRect();return [(e.clientX-r.left-VW/2)/cam.k+cam.x,(e.clientY-r.top-VH/2)/cam.k+cam.y]};
window.addEventListener('resize',()=>{const r=svg.getBoundingClientRect();VW=r.width;VH=r.height;apply()});

/* ---------- selection, overlay, handles ---------- */
let selId=null;
const showOut=()=>$('vOut').checked, showNames=()=>$('vNames').checked;
function corners(p,s){const [x0,y0,x1,y1]=p.box,f=(x,y)=>[p.ax+s.tx+s.s*(x-p.ax),p.ay+s.ty+s.s*(y-p.ay)];return [f(x0,y0),f(x1,y0),f(x1,y1),f(x0,y1)]}
function drawOv(){
  ovLayer.textContent='';const u=1/cam.k;
  for(const p of PC){const s=st.get(p.id),sel=p.id===selId;
    if(showOut()||sel){el('path',{d:p.d,transform:tf(p,s),fill:sel?'rgba(181,101,29,.10)':'none',stroke:sel?'var(--pick)':p.color,'stroke-width':sel?2.2:1.2,'stroke-dasharray':sel?'':'5 4',opacity:sel?1:.7,'vector-effect':'non-scaling-stroke','pointer-events':'none'},ovLayer)}
    if(showNames()){const cx=p.ax+s.tx+s.s*(p.lab[0]-p.ax),cy=p.ay+s.ty+s.s*(p.lab[1]-p.ay);
      const t=el('text',{x:cx,y:cy,'text-anchor':'middle','font-size':15*u,'font-weight':700,fill:'var(--ink)',style:`paint-order:stroke;stroke:var(--halo);stroke-width:${4*u}px;pointer-events:none;font-family:var(--sans)`},ovLayer);t.textContent=p.name+(s.locked?' 🔒':'')}}
  if(selId){const p=byId[selId],s=st.get(selId),c=corners(p,s);
    el('rect',{x:c[0][0],y:c[0][1],width:c[2][0]-c[0][0],height:c[2][1]-c[0][1],fill:'none',stroke:'var(--pick)','stroke-width':1.4,'stroke-dasharray':'2 3','vector-effect':'non-scaling-stroke','pointer-events':'none'},ovLayer);
    if(!s.locked)c.forEach((q,i)=>{const h=11*u;el('rect',{class:'hd','data-c':i,x:q[0]-h/2,y:q[1]-h/2,width:h,height:h,fill:'var(--panel)',stroke:'var(--pick)','stroke-width':2,'vector-effect':'non-scaling-stroke',style:'cursor:'+(i%2?'nesw':'nwse')+'-resize'},ovLayer)})}
}
function select(id){selId=id;drawOv();renderList()}

/* ---------- history ---------- */
let undoS=[],redoS=[];
const snap=id=>{const s=st.get(id);return {tx:s.tx,ty:s.ty,s:s.s}};
function setState(id,v){const s=st.get(id);s.tx=v.tx;s.ty=v.ty;s.s=v.s;applyPiece(byId[id])}
function commit(id,before){const a=snap(id);if(Math.abs(a.tx-before.tx)+Math.abs(a.ty-before.ty)+Math.abs(a.s-before.s)<1e-4)return;undoS.push({id,before,after:a});if(undoS.length>300)undoS.shift();redoS=[];changed()}
function undo(){const a=undoS.pop();if(!a)return;setState(a.id,a.before);redoS.push(a);changed(true)}
function redo(){const a=redoS.pop();if(!a)return;setState(a.id,a.after);undoS.push(a);changed(true)}
function changed(){$('undo').disabled=!undoS.length;$('redo').disabled=!redoS.length;drawOv();renderList();scheduleAutosave()}

/* ---------- mouse ---------- */
const hitCtx=ctx;
function pieceAt(w){for(let i=PC.length-1;i>=0;i--){const p=PC[i],s=st.get(p.id);const ox=p.ax+(w[0]-p.ax-s.tx)/s.s,oy=p.ay+(w[1]-p.ay-s.ty)/s.s;if(hitCtx.isPointInPath(p.path,ox,oy,'evenodd'))return p}return null}
let mode=null;
svg.addEventListener('pointerdown',e=>{
  if(e.button>1)return;svg.setPointerCapture(e.pointerId);const w=toW(e);
  if(e.button===1){mode={t:'pan',sx:e.clientX,sy:e.clientY,cx:cam.x,cy:cam.y,go:true};return}
  const hd=e.target.closest&&e.target.closest('.hd');
  if(hd&&selId&&!st.get(selId).locked){const p=byId[selId],s=st.get(selId),c=corners(p,s),i=+hd.dataset.c,o=(i+2)%4;
    mode={t:'size',id:selId,i,o,before:snap(selId),oPt:c[o],v0:[c[i][0]-c[o][0],c[i][1]-c[o][1]],ox:[p.box[[0,2,2,0][o]],p.box[[1,1,3,3][o]]]};return}
  const p=pieceAt(w);
  if(p){select(p.id);const s=st.get(p.id);mode=s.locked?{t:'none'}:{t:'move',id:p.id,w0:w,before:snap(p.id),go:false,sx:e.clientX,sy:e.clientY};svg.style.cursor=s.locked?'':'grabbing'}
  else{select(null);mode={t:'pan',sx:e.clientX,sy:e.clientY,cx:cam.x,cy:cam.y,go:false}}
});
svg.addEventListener('pointermove',e=>{
  if(!mode){const p=pieceAt(toW(e));svg.style.cursor=p?(st.get(p.id).locked?'not-allowed':'grab'):'default';return}
  const w=toW(e);
  if(mode.t==='pan'){if(!mode.go&&Math.abs(e.clientX-mode.sx)+Math.abs(e.clientY-mode.sy)<4)return;mode.go=true;cam.x=mode.cx-(e.clientX-mode.sx)/cam.k;cam.y=mode.cy-(e.clientY-mode.sy)/cam.k;apply();return}
  if(mode.t==='move'){if(!mode.go&&Math.abs(e.clientX-mode.sx)+Math.abs(e.clientY-mode.sy)<4)return;mode.go=true;
    let dx=w[0]-mode.w0[0],dy=w[1]-mode.w0[1];if($('snap').checked){dx=Math.round(dx*2)/2;dy=Math.round(dy*2)/2}
    const s=st.get(mode.id);s.tx=mode.before.tx+dx;s.ty=mode.before.ty+dy;applyPiece(byId[mode.id]);drawOv();return}
  if(mode.t==='size'){const p=byId[mode.id],s=st.get(mode.id);const v=[w[0]-mode.oPt[0],w[1]-mode.oPt[1]];
    const f=(v[0]*mode.v0[0]+v[1]*mode.v0[1])/(mode.v0[0]**2+mode.v0[1]**2);const s2=Math.max(.15,Math.min(8,mode.before.s*f));
    s.s=s2;s.tx=mode.oPt[0]-p.ax-s2*(mode.ox[0]-p.ax);s.ty=mode.oPt[1]-p.ay-s2*(mode.ox[1]-p.ay);applyPiece(p);drawOv()}
});
const endMode=()=>{if(mode&&(mode.t==='move'||mode.t==='size'))commit(mode.id,mode.before);mode=null;svg.style.cursor=''};
svg.addEventListener('pointerup',endMode);svg.addEventListener('pointercancel',endMode);
svg.addEventListener('wheel',e=>{e.preventDefault();const r=svg.getBoundingClientRect(),X=e.clientX-r.left,Y=e.clientY-r.top;const mx=(X-VW/2)/cam.k+cam.x,my=(Y-VH/2)/cam.k+cam.y;cam.k=Math.max(1.5,Math.min(120,cam.k*Math.exp(-e.deltaY*.0016)));cam.x=mx-(X-VW/2)/cam.k;cam.y=my-(Y-VH/2)/cam.k;apply()},{passive:false});
$('zin').onclick=()=>{cam.k=Math.min(120,cam.k*1.5);apply()};$('zout').onclick=()=>{cam.k=Math.max(1.5,cam.k/1.5);apply()};$('zfit').onclick=fitAll;
window.addEventListener('keydown',e=>{
  if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)&&e.target.type!=='checkbox')return;const k=e.key.toLowerCase();
  if((e.ctrlKey||e.metaKey)&&k==='z'){e.preventDefault();e.shiftKey?redo():undo();return}
  if((e.ctrlKey||e.metaKey)&&k==='y'){e.preventDefault();redo();return}
  if(k==='escape'){select(null);return}
  if(!selId||st.get(selId).locked)return;
  const step=e.shiftKey?2:(e.altKey?.1:.5),mv={arrowleft:[-step,0],arrowright:[step,0],arrowup:[0,-step],arrowdown:[0,step]}[k];
  if(mv){e.preventDefault();const b=snap(selId),s=st.get(selId);s.tx+=mv[0];s.ty+=mv[1];applyPiece(byId[selId]);commit(selId,b)}
  if(k==='['||k==='-'||k===']'||k==='='||k==='+'){e.preventDefault();const b=snap(selId),s=st.get(selId),p=byId[selId],f=(k==='['||k==='-')?.97:1.03;s.s=Math.max(.15,Math.min(8,s.s*f));applyPiece(p);commit(selId,b)}
});

/* ---------- sidebar ---------- */
const fmt=(v,d=1)=>(Math.round(v*10**d)/10**d).toString();
function renderList(){
  $('plist').innerHTML=PC.slice().reverse().map(p=>{const s=st.get(p.id),moved=Math.abs(s.tx)+Math.abs(s.ty)>.01||Math.abs(s.s-1)>.001;
    return `<li class="pi${p.id===selId?' on':''}" data-id="${p.id}"><span class="sw" style="background:${p.color}"></span><span class="nm"><b>${p.name}</b><i>${moved?`moved ${fmt(s.tx)}, ${fmt(s.ty)} · size ${Math.round(s.s*100)}%`:'where it started'}</i></span>
      <button class="ic" data-act="lock" title="${s.locked?'Unlock':'Lock'} this piece">${s.locked?'🔒':'🔓'}</button><button class="ic" data-act="reset" title="Put this piece back where it started">↺</button></li>`}).join('');
}
$('plist').addEventListener('click',e=>{const li=e.target.closest('.pi');if(!li)return;const id=li.dataset.id,act=e.target.closest('[data-act]')?.dataset.act;
  if(act==='lock'){const s=st.get(id);s.locked=!s.locked;changed()}
  else if(act==='reset'){const b=snap(id);setState(id,{tx:0,ty:0,s:1});commit(id,b)}
  else{select(id)}});
$('undo').onclick=undo;$('redo').onclick=redo;
let armed=null;$('resetAll').onclick=function(){if(!armed){this.textContent='Click again to confirm';armed=setTimeout(()=>{armed=null;this.textContent='Put everything back…'},4000);return}
  clearTimeout(armed);armed=null;this.textContent='Put everything back…';PC.forEach(p=>{const b=snap(p.id);if(b.tx||b.ty||b.s!==1){setState(p.id,{tx:0,ty:0,s:1});undoS.push({id:p.id,before:b,after:{tx:0,ty:0,s:1}})}});redoS=[];changed();toast('Everything is back where it started')};
['vOut','vNames'].forEach(id=>$(id).addEventListener('change',drawOv));

/* ---------- saving ---------- */
const ROUND=DATA.round||2, FORMAT='map-arrangement-'+ROUND;
function layoutObject(){return {format:FORMAT,savedAt:new Date().toISOString(),ids:PC.map(p=>p.id),tx:PC.map(p=>+st.get(p.id).tx.toFixed(2)),ty:PC.map(p=>+st.get(p.id).ty.toFixed(2)),s:PC.map(p=>+st.get(p.id).s.toFixed(4)),locked:PC.map(p=>st.get(p.id).locked?1:0)}}
function loadLayout(o,note){
  if(!o||o.format!==FORMAT||!o.ids)throw new Error('That is not an arrangement from this page.');
  o.ids.forEach((id,i)=>{if(!byId[id])return;const b=snap(id);setState(id,{tx:o.tx[i],ty:o.ty[i],s:o.s[i]});st.get(id).locked=!!o.locked[i];undoS.push({id,before:b,after:snap(id)})});
  redoS=[];changed();if(note)toast(note)}
let asT=null;function scheduleAutosave(){clearTimeout(asT);asT=setTimeout(()=>{try{localStorage.setItem('maparr:v'+ROUND,JSON.stringify(layoutObject()));$('localStat').textContent='Autosaved in this browser at '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})+'.'}catch(e){}},500)}
function toast(m){const t=$('toast');t.textContent=m;t.style.display='block';clearTimeout(toast.t);toast.t=setTimeout(()=>t.style.display='none',2600)}
async function dbHandle(){try{return (window.claude&&claude.use)?await claude.use('db'):null}catch(e){return null}}
$('saveDb').onclick=async()=>{
  const db=await dbHandle();
  if(!db){$('dbStat').textContent='Saving for Claude is not available in this view. Please use Download file or Copy / paste text instead.';return}
  const o=layoutObject();$('saveDb').disabled=true;$('dbStat').textContent='Saving…';
  try{const stamp=o.savedAt.replace(/[^0-9]/g,'').slice(0,14);await db.doc('arrangement'+ROUND+'/current').set(o);await db.doc('arrangement'+ROUND+'/b'+stamp).set(o);
    const n=o.s.filter((v,i)=>v!==1||o.tx[i]||o.ty[i]).length;
    $('dbStat').innerHTML=`<span class="ok">Saved ✓</span> at ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})} · ${n} piece${n==1?'':'s'} changed. Now tell me “saved” in the chat.`;
  }catch(err){$('dbStat').textContent='Could not save ('+((err&&err.code)||'error')+'). Please use Download file or Copy / paste text instead.'}
  $('saveDb').disabled=false};
$('dl').onclick=async()=>{let d=null;try{d=(window.claude&&claude.use)?await claude.use('downloads'):null}catch(e){}
  if(!d){openModal();toast('Download is not available here — copy the text instead');return}
  try{await d.save({filename:'map_arrangement_'+ROUND+'.json',data:JSON.stringify(layoutObject())});toast('Saved — now upload that file in the chat')}catch(err){if(!err||err.code!=='declined')toast('Download did not go through — try Copy / paste text')}};
function openModal(){$('lt').value=JSON.stringify(layoutObject());$('modal').style.display='flex';$('lt').focus();$('lt').select()}
$('txt').onclick=openModal;$('mClose').onclick=()=>$('modal').style.display='none';$('mSel').onclick=()=>{$('lt').focus();$('lt').select()};
$('mCopy').onclick=async()=>{$('lt').focus();$('lt').select();let ok=false;try{await navigator.clipboard.writeText($('lt').value);ok=true}catch(e){try{ok=document.execCommand('copy')}catch(e2){}}toast(ok?'Copied — paste it into the chat':'Press Ctrl+C (or Cmd+C) to copy the selected text')};
$('mLoad').onclick=()=>{try{loadLayout(JSON.parse($('lt').value),'Arrangement loaded');$('modal').style.display='none'}catch(e){toast(e.message||'Could not read that text')}};

/* ---------- start ---------- */
PC.forEach(applyPiece);renderList();
const r0=svg.getBoundingClientRect();VW=r0.width;VH=r0.height;fitAll();$('undo').disabled=true;$('redo').disabled=true;
(async function restore(){
  let local=null;try{local=JSON.parse(localStorage.getItem('maparr:v'+ROUND)||'null')}catch(e){}
  let remote=null;try{const db=await dbHandle();if(db){const s=await db.doc('arrangement'+ROUND+'/current').get();if(s&&s.exists)remote=s.data()}}catch(e){}
  const pick=[local,remote].filter(x=>x&&x.format===FORMAT).sort((a,b)=>(b.savedAt||'').localeCompare(a.savedAt||''))[0];
  if(pick){try{loadLayout(pick,'Restored your latest arrangement');undoS=[];redoS=[];changed()}catch(e){}}
})();
