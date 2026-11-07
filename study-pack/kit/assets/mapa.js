/* study-pack kit — Mapa page. Generic engine: nodes + edges + groups (+ columns). Vocabulary comes from MAP.kind (i18n), look from theme tokens. */
const MAP=JSON.parse($('#pack-src').textContent);
const M=T.mapa, K=M.kinds[MAP.kind]||M.kinds.causal;
const NODE={},OUT={},INN={},GIDX={};
MAP.groups.forEach((g,i)=>GIDX[g.id]=i);
MAP.nodes.forEach(n=>{NODE[n.id]=n;OUT[n.id]=[];INN[n.id]=[]});
MAP.edges.forEach((e,i)=>{e.i=i;OUT[e.a].push(e);INN[e.b].push(e)});
const GM=['●','■','▲','◆','★'];
const gm=n=>GM[GIDX[n.group]%GM.length], gcls=n=>'g'+(GIDX[n.group]%5);
const rich=s=>esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
const VOICE={pt:'pt-PT',fr:'fr-FR',en:'en-GB'}[PACK.lang]||'pt-PT';

/* ---- layout: every node gets a lane (row band) and a column; several nodes in one cell are stacked ---- */
const timeline=MAP.layout==='timeline';
const COLS=[],COLIDX={};
if(timeline){MAP.cols.forEach((c,i)=>{COLS.push(c);COLIDX[c.id]=i})}
else{ /* layers: column = longest path from a source */
  const dep={};const vis={};
  const depth=id=>{if(dep[id]!==undefined)return dep[id];dep[id]=INN[id].length?1+Math.max(...INN[id].map(e=>depth(e.a))):0;return dep[id]};
  MAP.nodes.forEach(n=>depth(n.id));
  const mx=Math.max(...Object.values(dep));
  for(let i=0;i<=mx;i++){COLS.push({id:'L'+i,label:tf(M.level,{n:i+1})});COLIDX['L'+i]=i}
  MAP.nodes.forEach(n=>n.col='L'+dep[n.id]);
  /* order inside a level by the mean row of its causes, to keep arrows short */
  const row={};
  for(let i=0;i<=mx;i++){
    const lv=MAP.nodes.filter(n=>dep[n.id]===i);
    lv.forEach(n=>{n._b=INN[n.id].length?INN[n.id].reduce((s,e)=>s+(row[e.a]||0),0)/INN[n.id].length:GIDX[n.group]});
    lv.sort((a,b)=>a._b-b._b||GIDX[a.group]-GIDX[b.group]);
    lv.forEach((n,j)=>row[n.id]=j);
  }
  MAP.nodes.sort((a,b)=>dep[a.id]-dep[b.id]||row[a.id]-row[b.id]);
}
const LANES=timeline?MAP.groups.map(g=>({id:g.id,name:g.name,idx:GIDX[g.id]})):[{id:'*',name:'',idx:0}];
const laneOf=n=>timeline?n.group:'*';

/* ---- chains ---- */
function walk(id,map,pick){const seen={},st=[id],r=[];while(st.length){const x=st.pop();map[x].forEach(e=>{const y=pick(e);if(!seen[y]){seen[y]=1;r.push(y);st.push(y)}})}return r}
const upstream=id=>walk(id,INN,e=>e.a), downstream=id=>walk(id,OUT,e=>e.b);
const edgeBetween=(a,b)=>MAP.edges.find(e=>e.a===a&&e.b===b);

/* ---- state ---- */
const CW=198,CH=112,COLW=226,GAPY=12,LEFT=22,TOP=64,LANEHEAD=40,LANEPAD=14,LANEGAP=16;
const vp=$('#mpVp'),world=$('#mpWorld'),panel=$('#mpPanel');
const pos={},cards={},bands={};let edgeEls=[];
const S={mode:'map',sel:null,route:null,step:0,quiz:null,score:{ok:0,n:0},only:false,topic:null,speak:'',W:0,H:0};
let known={},mode='local';
const isKnown=id=>!!known[id];
function saveKnown(){Store.save('mapa',{known})}

function build(){
  const stack={};MAP.nodes.forEach(n=>{const k=laneOf(n)+'|'+n.col;n._s=stack[k]===undefined?0:stack[k]+1;stack[k]=n._s});
  const maxs={};MAP.nodes.forEach(n=>{maxs[laneOf(n)]=Math.max(maxs[laneOf(n)]||0,n._s+1)});
  let y=TOP,html='';const W=LEFT*2+COLS.length*COLW;
  const laneY={};
  LANES.forEach(l=>{
    const h=LANEHEAD+(maxs[l.id]||1)*(CH+GAPY)+LANEPAD;laneY[l.id]=y;
    if(timeline) html+=`<div class="mp-band g${l.idx%5}" data-lane="${esc(l.id)}" style="left:6px;top:${y}px;width:${W-12}px;height:${h}px"><div class="mp-nm"><span class="mp-gm">${GM[l.idx%GM.length]}</span>${esc(l.name)}</div></div>`;
    y+=h+LANEGAP;
  });
  const H=y;
  COLS.forEach((c,i)=>{html+=`<div class="mp-colh" style="left:${LEFT+i*COLW}px;width:${COLW}px">${esc(c.label)}<i></i></div>`});
  MAP.nodes.forEach(n=>{
    const x=LEFT+COLIDX[n.col]*COLW+(COLW-CW)/2, yy=laneY[laneOf(n)]+LANEHEAD+n._s*(CH+GAPY);
    pos[n.id]={x,y:yy};
    const when=timeline?COLS[COLIDX[n.col]].label:(MAP.groups.length>1?MAP.groups[GIDX[n.group]].name:'');
    html+=`<button type="button" class="mp-card ${gcls(n)}" data-act="card" data-id="${esc(n.id)}" style="left:${x}px;top:${yy}px;width:${CW}px;height:${CH}px" aria-label="${esc((when?when+': ':'')+n.label)}"><span class="mp-when">${esc(when)}</span><span class="mp-lbl">${esc(n.label)}</span><span class="mp-gm" aria-hidden="true">${gm(n)}</span><span class="mp-tag"></span><span class="mp-chk" aria-hidden="true">✓</span></button>`;
  });
  let sv=`<svg id="mpEdges" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>`+['n','u','d'].map(k=>`<marker id="m${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path id="mk-${k}" d="M0 0L10 5L0 10z"/></marker>`).join('')+'</defs>';
  MAP.edges.forEach(ed=>{
    const a=pos[ed.a],b=pos[ed.b],na=NODE[ed.a],nb=NODE[ed.b];let d;
    if(COLIDX[na.col]<COLIDX[nb.col]){const x1=a.x+CW,y1=a.y+CH/2,x2=b.x-3,y2=b.y+CH/2,dx=Math.max(40,(x2-x1)*.5);d=`M${x1} ${y1}C${x1+dx} ${y1} ${x2-dx} ${y2} ${x2} ${y2}`}
    else{const down=b.y>a.y,x1=a.x+CW/2,x2=b.x+CW/2,y1=down?a.y+CH:a.y,y2=down?b.y-3:b.y+CH+3,dy=Math.max(20,Math.abs(y2-y1)*.5)*(down?1:-1);d=`M${x1} ${y1}C${x1} ${y1+dy} ${x2} ${y2-dy} ${x2} ${y2}`}
    sv+=`<path class="mp-edge" data-i="${ed.i}" d="${d}" marker-end="url(#mn)"><title>${esc(na.label+' → '+nb.label+': '+ed.why)}</title></path>`;
  });
  sv+='</svg>';
  world.innerHTML=html+sv;world.style.width=W+'px';world.style.height=H+'px';S.W=W;S.H=H;
  $$('.mp-card',world).forEach(c=>cards[c.dataset.id]=c);
  edgeEls=$$('.mp-edge',world);
  $$('.mp-band',world).forEach(b=>bands[b.dataset.lane]=b);
}
function paintKnown(){Object.keys(cards).forEach(id=>cards[id].classList.toggle('known',isKnown(id)))}
function paint(o){
  o=o||{};const any=!!(o.sel||(o.keep&&o.keep.length));
  const U={},D={},Kp={};(o.up||[]).forEach(x=>U[x]=1);(o.down||[]).forEach(x=>D[x]=1);(o.keep||[]).forEach(x=>Kp[x]=1);
  Object.keys(cards).forEach(id=>{const c=cards[id],on=id===o.sel||U[id]||D[id]||Kp[id];
    c.classList.toggle('is-sel',id===o.sel);c.classList.toggle('is-up',!!U[id]&&id!==o.sel);c.classList.toggle('is-down',!!D[id]&&id!==o.sel&&!U[id]);c.classList.toggle('is-route',!!Kp[id]&&id!==o.sel);c.classList.toggle('dim',any&&!on);
    const t=$('.mp-tag',c);t.textContent=id===o.sel?M.chosen:(U[id]?K.upBadge:(D[id]?K.downBadge:(Kp[id]?M.routeBadge:'')))});
  const eU={},eD={};(o.eU||[]).forEach(x=>eU[x]=1);(o.eD||[]).forEach(x=>eD[x]=1);
  edgeEls.forEach(el=>{const i=+el.dataset.i,u=eU[i],d=eD[i];el.classList.toggle('u',!!u);el.classList.toggle('d',!!d&&!u);el.classList.toggle('dim',any&&!u&&!d);
    el.setAttribute('marker-end','url(#m'+(u?'u':(d?'d':'n'))+')')});
  const on={};if(any)Object.keys(cards).forEach(id=>{if(!cards[id].classList.contains('dim'))on[laneOf(NODE[id])]=1});
  Object.keys(bands).forEach(l=>bands[l].classList.toggle('dim',any&&!on[l]));
}
function chainPaint(id){
  const up=upstream(id),dn=downstream(id),U={},Dn={};up.forEach(x=>U[x]=1);dn.forEach(x=>Dn[x]=1);U[id]=1;Dn[id]=1;
  const eU=[],eD=[];MAP.edges.forEach(e=>{if(U[e.a]&&U[e.b])eU.push(e.i);else if(Dn[e.a]&&Dn[e.b])eD.push(e.i)});
  paint({sel:id,up,down:dn,eU,eD});
}

/* ---- camera ---- */
const cam={x:0,y:0,k:.85};let anim=null;
const apply=()=>{world.style.transform=`translate(${cam.x}px,${cam.y}px) scale(${cam.k})`};
function clampCam(){const w=vp.clientWidth,h=vp.clientHeight,k=cam.k;cam.x=Math.max(Math.min(40,w-S.W*k-40),Math.min(40,cam.x));cam.y=Math.max(Math.min(40,h-S.H*k-40),Math.min(40,cam.y))}
function fly(x,y,k,ms){
  const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;cancelAnimationFrame(anim);
  const s={x:cam.x,y:cam.y,k:cam.k},t0=performance.now();ms=ms===undefined?600:ms;
  if(reduce||!ms){cam.x=x;cam.y=y;cam.k=k;clampCam();apply();return}
  (function f(t){const p=Math.min(1,(t-t0)/ms),e=p<.5?2*p*p:1-Math.pow(-2*p+2,2)/2;cam.x=s.x+(x-s.x)*e;cam.y=s.y+(y-s.y)*e;cam.k=s.k+(k-s.k)*e;apply();if(p<1)anim=requestAnimationFrame(f);else{clampCam();apply()}})(t0);
}
function centerOn(id,k){k=k||Math.max(cam.k,.85);const p=pos[id],w=vp.clientWidth,h=vp.clientHeight;fly(w/2-(p.x+CW/2)*k,h/2-(p.y+CH/2)*k,k)}
function fitAll(){const w=vp.clientWidth,h=vp.clientHeight,k=Math.min(w/S.W,h/S.H)*.96;fly((w-S.W*k)/2,(h-S.H*k)/2,k)}
function goCol(i,ms){const k=Math.max(.7,Math.min(cam.k,1));fly(16-(LEFT+i*COLW-10)*k,8,k,ms)}
(function(){
  const ptrs={};let start=null,moved=false,pinch=null;
  vp.addEventListener('pointerdown',e=>{if(e.target.closest('.mp-ctl'))return;ptrs[e.pointerId]={x:e.clientX,y:e.clientY};start={x:e.clientX,y:e.clientY,cx:cam.x,cy:cam.y};moved=false;cancelAnimationFrame(anim);
    if(Object.keys(ptrs).length===2){const p=Object.values(ptrs);pinch={d:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y),k:cam.k}}});
  vp.addEventListener('pointermove',e=>{
    if(!ptrs[e.pointerId])return;ptrs[e.pointerId]={x:e.clientX,y:e.clientY};const ks=Object.keys(ptrs);
    if(ks.length===2&&pinch){const p=Object.values(ptrs),d=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y),nk=Math.max(.2,Math.min(1.6,pinch.k*d/pinch.d)),r=vp.getBoundingClientRect(),mx=(p[0].x+p[1].x)/2-r.left,my=(p[0].y+p[1].y)/2-r.top;
      cam.x=mx-(mx-cam.x)*nk/cam.k;cam.y=my-(my-cam.y)*nk/cam.k;cam.k=nk;moved=true;clampCam();apply();return}
    const dx=e.clientX-start.x,dy=e.clientY-start.y;
    if(!moved&&Math.hypot(dx,dy)>6){moved=true;vp.classList.add('drag');try{vp.setPointerCapture(e.pointerId)}catch(x){}}
    if(moved&&ks.length===1){cam.x=start.cx+dx;cam.y=start.cy+dy;clampCam();apply()}
  });
  const up=e=>{delete ptrs[e.pointerId];pinch=null;if(!Object.keys(ptrs).length){vp.classList.remove('drag');setTimeout(()=>{moved=false},0)}};
  vp.addEventListener('pointerup',up);vp.addEventListener('pointercancel',up);
  vp.addEventListener('click',e=>{if(moved){e.stopPropagation();e.preventDefault()}},true);
  vp.addEventListener('wheel',e=>{e.preventDefault();const r=vp.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
    if(e.ctrlKey||Math.abs(e.deltaY)>Math.abs(e.deltaX)&&!e.shiftKey){const nk=Math.max(.2,Math.min(1.6,cam.k*Math.exp(-e.deltaY*(e.ctrlKey?.01:.0015))));cam.x=mx-(mx-cam.x)*nk/cam.k;cam.y=my-(my-cam.y)*nk/cam.k;cam.k=nk}
    else{cam.x-=e.deltaX;cam.y-=e.deltaY}clampCam();apply()},{passive:false});
  vp.addEventListener('keydown',e=>{if(e.target.closest('.mp-card'))return;const st=60;let h=true;
    if(e.key==='ArrowLeft')cam.x+=st;else if(e.key==='ArrowRight')cam.x-=st;else if(e.key==='ArrowUp')cam.y+=st;else if(e.key==='ArrowDown')cam.y-=st;
    else if(e.key==='+'||e.key==='='){zoomBy(1.25);h=false}else if(e.key==='-'){zoomBy(.8);h=false}else return;e.preventDefault();clampCam();apply()});
})();
function zoomBy(f){const w=vp.clientWidth/2,h=vp.clientHeight/2,nk=Math.max(.2,Math.min(1.6,cam.k*f));fly(w-(w-cam.x)*nk/cam.k,h-(h-cam.y)*nk/cam.k,nk,250)}

/* ---- voice ---- */
const Voice={ok:'speechSynthesis' in window,on:null,
  say(text,btn){
    if(!this.ok)return;const s=speechSynthesis;
    if(this.on&&s.speaking){s.cancel();const same=this.on===btn;this.on=null;if(btn)btn.setAttribute('aria-pressed','false');if(same)return}
    const u=new SpeechSynthesisUtterance(text);u.lang=VOICE;u.rate=.9;
    const v=s.getVoices().filter(x=>x.lang&&x.lang.toLowerCase().startsWith(VOICE.slice(0,2)));const p=v.find(x=>x.lang===VOICE)||v[0];if(p)u.voice=p;
    u.onend=u.onerror=()=>{this.on=null;if(btn)btn.setAttribute('aria-pressed','false')};
    this.on=btn||true;if(btn)btn.setAttribute('aria-pressed','true');s.speak(u)
  },
  stop(){if(this.ok){speechSynthesis.cancel();this.on=null}}};

/* ---- panel pieces ---- */
const groupName=n=>MAP.groups[GIDX[n.group]].name;
const whenOf=n=>timeline?COLS[COLIDX[n.col]].label:'';
function itemBtn(id,why){const n=NODE[id];return `<li><button type="button" class="mp-item ${gcls(n)}" data-act="card" data-id="${esc(id)}" data-fly="1"><span class="mp-num">${esc(timeline?whenOf(n):gm(n))}</span><span><span class="mp-t">${esc(n.label)}</span>${why?`<span class="mp-why">${esc(why)}</span>`:''}</span></button></li>`}
function topicLinks(n){
  if(!n.topic)return '';const U=PACK.urls;let h='';
  if(U.resumo)h+=`<a class="btn" href="${esc(U.resumo)}#r${n.topic}">${esc(M.openResumo)}</a>`;
  if(U.revisao)h+=`<a class="btn" href="${esc(U.revisao)}#ch${n.topic}">${esc(M.openPractice)}</a>`;
  return h?`<div class="mp-row">${h}</div>`:'';
}
function sec(cls,title,body,open){return `<details class="mp-sec ${cls}"${open?' open':''}><summary>${esc(title)}</summary>${body}</details>`}
function detail(n,full){
  let h='';
  if(n.ctx)h+=sec('ctx',M.ctx,`<p>${rich(Array.isArray(n.ctx)?n.ctx.join(' '):n.ctx)}</p>`,true);
  if(n.what&&n.what.length)h+=sec('what',M.what,'<ul>'+n.what.map(w=>`<li>${rich(w)}</li>`).join('')+'</ul>',true);
  if(n.keys&&n.keys.length)h+=sec('keys',M.keys,'<ul>'+n.keys.map(w=>`<li>${rich(w)}</li>`).join('')+'</ul>',true);
  if(n.hook)h+=sec('hook',M.hook,`<p>${rich(n.hook)}</p>`,true);
  if(n.pages)h+=`<p class="mp-note">📖 ${esc(M.pagesLbl)}: ${esc(n.pages)}</p>`;
  if(n.terms&&n.terms.length)h+=sec('terms',M.terms,'<dl class="mp-terms">'+n.terms.map(t=>`<dt>${esc(t.t)}</dt><dd>${esc(t.d)}</dd>`).join('')+'</dl>',!!full);
  if(n.extra&&n.extra.length)h+=sec('extra',M.extra,'<ul class="extra">'+n.extra.map(w=>`<li>${rich(w)}</li>`).join('')+'</ul>',false);
  return h;
}
function speakText(n,edgeWhy){
  const parts=[n.label+'.',n.text];
  if(edgeWhy)parts.unshift(K.because+' '+edgeWhy);
  if(n.ctx)parts.push(n.ctx);
  (n.what||[]).forEach(w=>parts.push(w));
  if(n.keys&&n.keys.length)parts.push(M.keys+': '+n.keys.join('. '));
  return parts.join(' ').replace(/\*\*/g,'').replace(/\$/g,'');
}
function nodeHead(n){return `<div><div class="mp-kind ${gcls(n)}"><span class="mp-gm" aria-hidden="true">${gm(n)}</span>${esc(groupName(n))}</div><h2>${esc(n.label)}</h2>${whenOf(n)?`<div class="mp-when">${esc(whenOf(n))}</div>`:''}</div>`}
function actions(n,extra){
  return `<div class="mp-row">${Voice.ok?`<button type="button" class="btn" data-act="speak" aria-pressed="false">🔊 ${esc(M.listen)}</button>`:''}<button type="button" class="btn${isKnown(n.id)?' solid':''}" data-act="know" data-id="${esc(n.id)}" aria-pressed="${isKnown(n.id)}">${isKnown(n.id)?'✓ '+esc(M.known):esc(M.know)}</button>${extra||''}</div>`;
}
const backBtn=()=>`<button type="button" class="btn mp-back" data-act="tomap">↑ ${esc(M.toMap)}</button>`;

const MATHY=/\$/.test(JSON.stringify(MAP));
function ts(el){if(!MATHY)return;let n=0;(function go(){if(window.renderMathInElement||n++>40)typeset(el);else setTimeout(go,100)})()}
function renderPanel(){Voice.stop();let h;if(S.mode==='map')h=panelMap();else if(S.mode==='routes')h=panelRoutes();else h=panelTrain();panel.innerHTML=h;ts(panel)}
function progressBlock(){
  const k=Object.keys(known).length,N=MAP.nodes.length;
  return `<div><h3>${esc(M.progress)}</h3><div class="mp-bar" aria-hidden="true"><i style="width:${Math.round(k/N*100)}%"></i></div><p class="mp-note">${esc(tf(M.progressN,{k,n:N}))} · ${esc(mode==='account'?M.savedAcct:M.savedLocal)}</p></div>`;
}
function panelMap(){
  let h='';
  if(S.topic&&!S.sel){
    const ns=MAP.nodes.filter(n=>n.topic===S.topic);
    S.speak='';
    h+=`<div><div class="mp-kind">${esc(T.topic)} ${S.topic}</div><h2>${esc(PACK.topics[S.topic]||'')}</h2></div><p class="mp-sum">${esc(M.topicIntro)}</p><ul class="mp-list">${ns.map(n=>itemBtn(n.id,n.text)).join('')}</ul><div class="mp-row"><button type="button" class="btn" data-act="clear">${esc(M.close)}</button></div>`;
    return h;
  }
  if(!S.sel){
    S.speak='';
    h+=`<div><div class="mp-kind" style="color:var(--muted)">${esc(K.title)}</div><h2>${esc(K.h)}</h2></div><p class="mp-sum">${esc(K.intro)}</p>`;
    h+=`<div class="mp-leg"><span class="s"><i class="mp-sw u"></i>${esc(K.upLeg)}</span><span class="s"><i class="mp-sw d"></i>${esc(K.downLeg)}</span></div>`;
    h+=`<p class="mp-note">${esc(timeline?M.howTimeline:M.howLayers)}</p><p class="mp-note">${esc(M.intro)}</p>`;
    h+=`<div class="mp-row"><button type="button" class="btn solid" data-act="mode" data-m="routes">${esc(M.followRoute)}</button><button type="button" class="btn" data-act="mode" data-m="train">${esc(M.trainBtn)}</button></div>`;
    return h+progressBlock();
  }
  const n=NODE[S.sel],up=upstream(S.sel),dn=downstream(S.sel);
  S.speak=speakText(n);
  h+=nodeHead(n)+`<p class="mp-sum">${rich(n.text)}</p>`;
  h+=actions(n,`<button type="button" class="btn" data-act="only" aria-pressed="${S.only}">${esc(M.onlyChain)}</button><button type="button" class="btn" data-act="clear">${esc(M.close)}</button>`);
  h+=topicLinks(n);
  h+=`<p class="mp-note">${esc(tf(M.chain,{u:up.length,d:dn.length,uw:up.length===1?K.upOne:K.upMany,dw:dn.length===1?K.downOne:K.downMany}))}</p>`;
  h+=detail(n,false);
  h+=sec('up',K.upH,INN[n.id].length?`<ul class="mp-list">${INN[n.id].map(e=>itemBtn(e.a,e.why)).join('')}</ul>`:`<p class="mp-note">${esc(K.start)}</p>`,true);
  h+=sec('down',K.downH,OUT[n.id].length?`<ul class="mp-list">${OUT[n.id].map(e=>itemBtn(e.b,e.why)).join('')}</ul>`:`<p class="mp-note">${esc(K.end)}</p>`,true);
  return h+backBtn();
}
function selectNode(id,fl){S.sel=id;S.topic=null;chainPaint(id);renderPanel();if(fl)centerOn(id)}
function clearSel(){S.sel=null;S.topic=null;S.only=false;world.classList.remove('mp-only');paint();renderPanel()}

/* routes */
function panelRoutes(){
  const R=S.route;let h='';
  if(!R){
    S.speak='';
    h+=`<div><div class="mp-kind" style="color:var(--muted)">${esc(M.tabs.routes)}</div><h2>${esc(M.routesH)}</h2></div><p class="mp-sum">${esc(M.routesIntro)}</p><ul class="mp-list">`;
    MAP.routes.forEach((r,i)=>{h+=`<li><button type="button" class="mp-item" data-act="route" data-i="${i}"><span class="mp-num">${r.nodes.length}</span><span class="mp-t">${esc(r.name)}</span></button></li>`});
    return h+'</ul>';
  }
  const st=R.nodes,i=S.step,n=NODE[st[i]],ed=i>0?edgeBetween(st[i-1],st[i]):null;
  S.speak=speakText(n,ed&&ed.why);
  h+=`<div><div class="mp-kind" style="color:var(--muted)">${esc(M.route)}</div><h2>${esc(R.name)}</h2></div>`;
  h+=`<div class="mp-prog" aria-label="${esc(tf(M.stepOf,{i:i+1,n:st.length}))}">${st.map((s,j)=>`<i class="${j<=i?'on':''}${j===i?' now':''}"></i>`).join('')}</div>`;
  h+=`<div class="mp-note">${esc(tf(M.stepOf,{i:i+1,n:st.length}))}${whenOf(n)?' · '+esc(whenOf(n)):''}</div>`;
  if(ed)h+=`<div class="mp-because"><b>${esc(K.because)}</b> ${esc(ed.why)}</div>`;
  h+=nodeHead(n)+`<p class="mp-sum">${rich(n.text)}</p>`;
  h+=actions(n);
  h+=detail(n,false);
  h+=`<div class="mp-row"><button type="button" class="btn" data-act="prev"${i===0?' disabled':''}>${esc(M.before)}</button>${i<st.length-1?`<button type="button" class="btn solid" data-act="next">${esc(M.after)}</button>`:`<button type="button" class="btn solid" data-act="mode" data-m="train">${esc(M.trainBtn)}</button>`}<button type="button" class="btn" data-act="routes">${esc(M.otherRoutes)}</button></div>`;
  h+=topicLinks(n);
  return h+backBtn();
}
function routePaint(){
  const R=S.route;if(!R){paint();return}
  const st=R.nodes,eD=[];for(let j=1;j<=S.step;j++)eD.push(edgeBetween(st[j-1],st[j]).i);
  paint({sel:st[S.step],keep:st,eD});
}
function goStep(i){S.step=i;routePaint();renderPanel();centerOn(S.route.nodes[i],.95)}

/* training: why / next / key points */
const shuffle=a=>{a=a.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a};
const rank=n=>COLIDX[n.col];
function newQ(){
  const kinds=[];
  MAP.nodes.forEach(n=>{if(INN[n.id].length)kinds.push(['up',n.id]);if(OUT[n.id].length)kinds.push(['down',n.id]);if(n.keys&&n.keys.length&&MAP.nodes.length>=4)kinds.push(['key',n.id])});
  let pool=shuffle(kinds);if(S.quiz&&pool.length>1)pool=pool.filter(k=>k[1]!==S.quiz.id||k[0]!==S.quiz.type);
  const [type,id]=pool[0],n=NODE[id];
  if(type==='key'){
    const good=shuffle(n.keys)[0];
    const others=[];MAP.nodes.forEach(x=>{if(x.id!==id)(x.keys||[]).forEach(k=>{if(!n.keys.includes(k))others.push({id:x.id,t:k,same:x.group===n.group})})});
    const d=shuffle(others).sort((a,b)=>(b.same-a.same)).slice(0,3);
    const opts=shuffle([{id:'_ok',t:good}].concat(d));
    S.quiz={type,id,opts,correct:'_ok',goodSet:{_ok:1},done:false,pick:null};
  }else{
    const up=type==='up',good=(up?INN[id].map(e=>e.a):OUT[id].map(e=>e.b));
    const correct=shuffle(good)[0],chain=up?upstream(id):downstream(id),bad={};chain.concat([id]).forEach(x=>bad[x]=1);
    const pl=MAP.nodes.filter(x=>!bad[x.id]),pref=pl.filter(x=>up?rank(x)<=rank(n):rank(x)>=rank(n));
    let d=shuffle(pref).slice(0,3);if(d.length<3)d=d.concat(shuffle(pl.filter(x=>!d.includes(x))).slice(0,3-d.length));
    const gs={};good.forEach(x=>gs[x]=1);
    S.quiz={type,id,opts:shuffle([correct].concat(d.slice(0,3).map(x=>x.id))).map(o=>({id:o,t:NODE[o].label})),correct,goodSet:gs,done:false,pick:null};
  }
  S.speak='';
}
function panelTrain(){
  if(!S.quiz)newQ();
  const Q=S.quiz,n=NODE[Q.id];let h='';
  const title=Q.type==='up'?K.upShort:(Q.type==='down'?K.downShort:M.keyShort);
  const q=Q.type==='up'?tf(K.qUp,{x:n.label}):(Q.type==='down'?tf(K.qDown,{x:n.label}):tf(M.qKey,{x:n.label}));
  h+=`<div><div class="mp-kind" style="color:var(--muted)">${esc(M.tabs.train)} · ${esc(tf(M.score,{ok:S.score.ok,n:S.score.n}))}</div><h2>${esc(title)}</h2></div>`;
  h+=`<p class="mp-q">${esc(q)}</p><p class="mp-note">${esc(whenOf(n)?whenOf(n)+' · ':'')}${esc(n.text)}</p>`;
  S.speak=q;
  h+='<div class="mp-opts">';
  Q.opts.forEach((o,i)=>{let cls='';if(Q.done){if(Q.goodSet[o.id])cls=' right';else if(o.id===Q.pick)cls=' wrong'}
    const nn=NODE[o.id];
    h+=`<button type="button" class="mp-opt${cls}" data-act="answer" data-id="${esc(o.id)}"${Q.done?' disabled':''}><span class="mp-ab">${'ABCD'[i]}</span><span>${esc(o.t)}${Q.done&&nn&&Q.type!=='key'&&whenOf(nn)?`<small>${esc(whenOf(nn))}</small>`:''}</span></button>`});
  h+='</div>';
  if(Q.done){
    const right=!!Q.goodSet[Q.pick];let why;
    if(Q.type==='key')why=n.hook||n.text;
    else{const pk=right?Q.pick:Q.correct;const ed=Q.type==='up'?edgeBetween(pk,Q.id):edgeBetween(Q.id,pk);why=ed?ed.why:''}
    const ans=Q.type==='key'?Q.opts.find(o=>o.id==='_ok').t:NODE[Q.correct].label;
    h+=`<div class="mp-fb ${right?'ok':'no'}"><b>${esc(right?M.right:M.wrong)}</b> ${right?'':esc(tf(M.answerIs,{x:ans}))+' '}${esc(why)}</div>`;
    h+=`<div class="mp-row"><button type="button" class="btn solid" data-act="nextq">${esc(M.nextQ)}</button><button type="button" class="btn" data-act="show" data-id="${esc(Q.id)}">${esc(M.seeCard)}</button><button type="button" class="btn" data-act="mode" data-m="map">${esc(M.backToMap)}</button></div>`;
  }else h+=`<p class="mp-note">${esc(M.noRush)}</p>`;
  return h+backBtn();
}
function quizPaint(){
  const Q=S.quiz;if(!Q){paint();return}
  if(!Q.done||Q.type==='key'){paint({sel:Q.id});return}
  const up=Q.type==='up',good=Object.keys(Q.goodSet),es=(up?INN[Q.id]:OUT[Q.id]).map(e=>e.i);
  paint({sel:Q.id,up:up?good:[],down:up?[]:good,eU:up?es:[],eD:up?[]:es});
}

/* ---- actions ---- */
function setTabs(){$$('[data-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.m===S.mode)))}
function setMode(m){
  S.mode=m;S.sel=null;S.topic=null;S.only=false;world.classList.remove('mp-only');setTabs();
  if(m==='routes'){S.route=null;paint()}else if(m==='train'){S.quiz=null;newQ();quizPaint();centerOn(S.quiz.id,.9)}else paint();
  renderPanel();
}
const narrow=()=>matchMedia('(max-width:900px)').matches;
document.addEventListener('click',e=>{
  const t=e.target.closest('[data-act]');if(!t)return;const a=t.dataset.act,id=t.dataset.id;
  if(a==='card'){
    const fromMap=!!t.closest('#mpWorld');
    if(S.mode==='map'){selectNode(id,true);if(fromMap&&narrow())panel.scrollIntoView({behavior:'smooth',block:'start'})}
    else if(S.mode==='routes'&&S.route){const i=S.route.nodes.indexOf(id);if(i>=0)goStep(i);else if(!fromMap){centerOn(id)}}
    else if(S.mode==='train'&&S.quiz&&S.quiz.done){S.mode='map';setTabs();selectNode(id,true)}
  }
  else if(a==='show'){S.mode='map';setTabs();selectNode(id,true)}
  else if(a==='mode')setMode(t.dataset.m);
  else if(a==='clear')clearSel();
  else if(a==='only'){S.only=!S.only;world.classList.toggle('mp-only',S.only);renderPanel()}
  else if(a==='know'){if(isKnown(id))delete known[id];else known[id]=1;saveKnown();paintKnown();renderPanel()}
  else if(a==='speak')Voice.say(S.speak,t);
  else if(a==='route'){S.route=MAP.routes[+t.dataset.i];goStep(0)}
  else if(a==='routes'){S.route=null;paint();renderPanel();fitAll()}
  else if(a==='next')goStep(Math.min(S.route.nodes.length-1,S.step+1));
  else if(a==='prev')goStep(Math.max(0,S.step-1));
  else if(a==='answer'){const Q=S.quiz;Q.done=true;Q.pick=id;S.score.n++;if(Q.goodSet[id])S.score.ok++;quizPaint();renderPanel()}
  else if(a==='nextq'){newQ();quizPaint();renderPanel();centerOn(S.quiz.id,.9)}
  else if(a==='era')goCol(+t.dataset.i);
  else if(a==='fit')fitAll();
  else if(a==='zin')zoomBy(1.3);else if(a==='zout')zoomBy(.77);
  else if(a==='tomap')vp.scrollIntoView({behavior:'smooth',block:'start'});
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&S.mode==='map'&&(S.sel||S.topic))clearSel()});
let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(()=>{clampCam();apply()},150)});

/* links from the other pages: #t3 = nodes of topic 3, #n-<id> = one node */
function fromHash(){
  const h=(location.hash||'').slice(1);let m;
  if((m=/^t(\d+)$/.exec(h))){const n=+m[1],ns=MAP.nodes.filter(x=>x.topic===n);if(ns.length){S.mode='map';setTabs();S.sel=null;S.topic=n;paint({keep:ns.map(x=>x.id)});renderPanel();centerOn(ns[0].id,.85);return true}}
  else if((m=/^n-(.+)$/.exec(h))&&NODE[m[1]]){S.mode='map';setTabs();selectNode(m[1],true);return true}
  return false;
}
window.addEventListener('hashchange',fromHash);
async function initKnown(){
  try{const r=lsGet(Store.lsName('mapa'));if(r)known=(JSON.parse(r)||{}).known||{}}catch(e){}
  paintKnown();renderPanel();
  const s=await Store.init();if(!s)return;
  const r=await Store.load('mapa');
  if(r.remote){mode='account';known=Object.assign({},(r.data&&r.data.known)||{},known);paintKnown();renderPanel();if(Object.keys(known).length)saveKnown()}
}
(function boot(){
  build();
  const w=vp.clientWidth,k=w<600?.7:.85;cam.k=k;
  if(!timeline&&S.W*k<w){fitAll()}else{cam.x=16-(LEFT-10)*k;cam.y=8;clampCam();apply()}
  /* era chips */
  const er=$('#mpEras');if(er&&MAP.eras){MAP.eras.forEach(x=>{const b=document.createElement('button');b.type='button';b.className='btn sm';b.dataset.act='era';b.dataset.i=COLIDX[x.col];b.textContent=x.label;er.appendChild(b)})}
  renderPanel();countdown();setInterval(countdown,3600000);
  if(!fromHash()&&timeline&&MAP.eras&&MAP.eras[1])goCol(COLIDX[MAP.eras[1].col],0);
  initKnown();
})();
