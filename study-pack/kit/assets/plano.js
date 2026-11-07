/* study-pack kit — Plano page. PLAN = {days:[{d:"YYYY-MM-DD",note,s:[{t,a,m,q?}]}]} written by plan.py.
   Ticks are keyed by date + index of the ORIGINAL plan ("2026-11-03#2"): never move dated sessions in an update.
   The page adapts the plan live, without touching PLAN:
   - sessions of past days that were not ticked move to the next days (learn/exercises first);
   - the load of the next days follows the real pace (minutes done / planned over the last 4 days, 50–100 %);
   - a topic scored < 60 % in a finished test gets a 20-min extra review the next day;
   - when it no longer fits before the exam, the least important reviews are dropped (never learn/exercises).
   "Plano original" shows the plan as it was made. */
const P=T.plan, DAYS=PLAN.days, NAMES=PACK.topics, ORDER=['learn','ex','rev','quiz','test'];
const NS='http://www.w3.org/2000/svg';
const COL=a=>({learn:'var(--accent)',ex:'var(--accent2)',rev:'var(--warn)',quiz:'var(--ok)',test:'var(--bad)'}[a]);
const PRI={learn:0,ex:1,test:2,quiz:3,rev:4};
let done={}, ref=null, timer=null, RES={results:{}}, showOrig=false, VIEW=null;
function todayISO(){const d=new Date(); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)}
const TODAY=todayISO();
const keyOf=(di,si)=>DAYS[di].d+'#'+si;
const wd=d=>new Date(d+'T12:00:00Z').toLocaleDateString(T.locale,{weekday:'short',timeZone:'UTC'}).replace('.','');
const fmtDate=d=>new Date(d+'T12:00:00Z').toLocaleDateString(T.locale,{day:'numeric',month:'long',timeZone:'UTC'});
const fmtShort=d=>new Date(d+'T12:00:00Z').toLocaleDateString(T.locale,{day:'numeric',month:'short',timeZone:'UTC'});
const h=m=>{const H=Math.floor(m/60),M=Math.round(m%60); return (H?H+'h':'')+(M?String(M).padStart(H?2:1,'0')+(H?'':' min'):'')||'0h'};
const U=PACK.urls;
const TESTS=PACK.tests||[];
const testOf=s=>s.a==='quiz'?TESTS.find(t=>t.id==='d'+s.orig):s.a==='test'?TESTS.find(t=>t.kind==='mock'):null;
const pct=(a,b)=>b?Math.round(a/b*100):0;
const nextDay=d=>new Date(Date.parse(d+'T12:00:00Z')+86400000).toISOString().slice(0,10);
function label(s){
  if(s.a==='quiz') return tf(P.quizLbl,{t:(s.q||[]).join(', ')});
  if(s.t) return `${s.t} · ${NAMES[s.t]}`;
  return s.a==='test'?P.mixed:P.reserve;
}
function isDone(s){
  if(done[s.key]) return true;
  if(s.a==='quiz'){ const r=RES.results['d'+s.orig]; return !!(r&&!r.pending); }
  return false;
}
/* ---------- the adapted plan ---------- */
function adapt(){
  const base=DAYS.map((D,di)=>({d:D.d,note:D.note,s:D.s.map((s,si)=>({...s,key:keyOf(di,si),orig:D.d}))}));
  if(showOrig) return {days:base,info:null};
  const past=base.filter(D=>D.d<TODAY), future=base.filter(D=>D.d>=TODAY);
  let pm=0,dm=0; past.slice(-4).forEach(D=>D.s.forEach(s=>{ if(s.a==='quiz') return; pm+=s.m; if(isDone(s)) dm+=s.m; }));
  const pace=pm?Math.min(1,Math.max(.5,dm/pm)):1;
  let queue=[]; past.forEach(D=>D.s.forEach(s=>{ if(!isDone(s)&&s.a!=='quiz'&&s.a!=='test') queue.push({...s,carried:D.d}); }));
  const moved=queue.length;
  /* extra reviews from finished tests (latest result per topic), next day */
  const latest={};
  Object.entries(RES.results).forEach(([id,r])=>{ if(r.pending) return; Object.entries(r.byTopic||{}).forEach(([n,v])=>{ if(v[1]&&(!latest[n]||latest[n].t<r.t)) latest[n]={t:r.t,p:pct(v[0],v[1]),id}; }); });
  const boosts=Object.entries(latest).filter(([,v])=>v.p<60).map(([n,v])=>({t:+n,a:'rev',m:20,key:`boost:${v.id}:${n}`,orig:TODAY,boost:v.p,isBoost:true,gen:true,from:new Date(v.t).toISOString().slice(0,10)}))
    .filter(b=>!(done[b.key]&&TODAY>nextDay(b.from)));
  const out=past.map(D=>({...D,s:D.s.map(s=>({...s,missed:!isDone(s)&&s.a!=='quiz'}))}));
  let nboost=0;
  const pr=s=>s.isBoost?1.5:PRI[s.a];
  const F=future.map(D=>{ const fixed=D.s.filter(s=>s.a==='quiz'||s.a==='test'); const planned=D.s.reduce((a,s)=>a+s.m,0);
    const placed=D.s.filter(s=>isDone(s)&&!fixed.includes(s));
    return {D,fixed,planned,budget:D.d===TODAY?planned:Math.round(planned*pace),placed,own:D.s.filter(s=>!isDone(s)&&!fixed.includes(s)),
      used:[...fixed,...placed].reduce((a,s)=>a+s.m,0)}; });
  /* pass 1: each day gets what fits in its budget (planned load × pace), most important first */
  F.forEach(x=>{
    const todayBoosts=boosts.filter(b=>b.from<x.D.d&&!b.placed).filter(b=>{ /* an extra review on a topic already reviewed that day upgrades that review */
      const twin=x.own.find(o=>o.a==='rev'&&o.t===b.t); if(!twin) return true;
      twin.boost=b.boost; twin.isBoost=true; b.placed=true; nboost++; return false; });
    const cands=[...todayBoosts,...queue,...x.own].sort((p,q)=>(pr(p)-pr(q))||((p.carried||p.orig)<(q.carried||q.orig)?-1:1));
    const rest=[];
    cands.forEach(s=>{
      if(s.a==='rev'&&s.carried&&x.own.some(o=>o!==s&&o.a==='rev'&&o.t===s.t)) return; /* a late review merges with that day's review of the same topic */
      const fits=x.used+s.m<=x.budget+5||(!x.placed.length&&s.m<=x.budget+30)||(s.isBoost&&x.used+s.m<=x.budget+25);
      if(fits){ x.placed.push(s); x.used+=s.m; if(s.gen){ s.placed=true; nboost++; } } else rest.push(s);
    });
    queue=rest.filter(s=>!s.gen);
  });
  /* pass 2: learning, exercises and extra reviews are never dropped: they go back on the earliest days that still have room
     up to the ORIGINAL load (+30 min), else on the last day. Only plain reviews can be cut. */
  const keep=[...queue.filter(s=>s.a==='learn'||s.a==='ex'||s.isBoost),...boosts.filter(b=>!b.placed)]; queue=queue.filter(s=>!keep.includes(s));
  keep.forEach(s=>{ const x=F.find(y=>y.used+s.m<=y.planned+30)||F[F.length-1]; if(!x) return; x.placed.push(s); x.used+=s.m; if(s.gen){ s.placed=true; nboost++; } });
  F.forEach(x=>{ x.placed.sort((p,q)=>pr(p)-pr(q)); out.push({d:x.D.d,note:x.D.note,s:[...x.placed,...x.fixed]}); });
  const cut=queue.filter(s=>!s.gen).length;
  queue=queue.filter(s=>!s.gen);
  const info={pace,moved,boost:nboost,cut,cutList:queue};
  return {days:out,info};
}
function renderAdapt(){
  const box=$('#adapt'); if(!box) return; const i=VIEW.info;
  if(showOrig){ box.hidden=false; box.innerHTML=`<span>${P.showOrig}</span>`; return; }
  if(!i){ box.hidden=true; return; }
  const lines=[]; if(i.pace<.995) lines.push(tf(P.adaptPace,{p:Math.round(i.pace*100)}));
  if(i.moved) lines.push(tf(P.adaptMoved,{n:i.moved})); if(i.boost) lines.push(tf(P.adaptBoost,{n:i.boost})); if(i.cut) lines.push(tf(P.adaptCut,{n:i.cut}));
  box.hidden=false; box.innerHTML=`<b>${P.adaptTitle}</b>`+(lines.length?lines.map(l=>`<span>${esc(l)}</span>`).join(''):`<span>${P.adaptNone}</span>`);
}
function summary(){
  const d=calDays(); $('#sDays').textContent=d===null?'–':Math.max(0,d);
  let tot=0,dn=0,ns=0,nd=0; VIEW.days.forEach(D=>D.s.forEach(s=>{tot+=s.m; ns++; if(isDone(s)){dn+=s.m; nd++;}}));
  $('#sHours').textContent=Math.round(tot/60)+'h'; $('#sDone').textContent=tf(P.hoursDone,{d:h(dn),t:Math.round(tot/60)+'h'});
  $('#oText').textContent=tf(T.planOverall,{done:nd,total:ns,hd:h(dn),ht:Math.round(tot/60)+'h'});
  $('#oOk').style.width=(dn/(tot||1)*100)+'%';
}
function renderDays(){
  const box=$('#days'); box.innerHTML='';
  VIEW.days.forEach((D,di)=>{
    const tot=D.s.reduce((a,s)=>a+s.m,0);
    const sec=document.createElement('section'); sec.className='day'+(D.d===TODAY?' today':'')+(D.d<TODAY?' past':''); sec.id='d'+D.d;
    sec.innerHTML=`<div class="dh"><h3>${wd(D.d)}, ${fmtDate(D.d)}</h3><span class="hrs">${h(tot)}</span>${D.d===TODAY?`<span class="tag now">${P.today}</span>`:''}${D.note?`<span class="tag">${esc(D.note)}</span>`:''}</div><ul class="sess"></ul>`;
    const ul=$('ul',sec);
    D.s.forEach((s,si)=>{
      const id='c'+di+'-'+si; const li=document.createElement('li'); const ok=isDone(s); if(ok) li.classList.add('done'); if(s.carried) li.classList.add('carried');
      const pg=T.page; const tst=testOf(s);
      let links;
      if((s.a==='quiz'||s.a==='test')&&tst&&U.testes) links=[`<a href="${U.testes}#${tst.id}">${P.toTests}</a>`];
      else if(s.t) links=[`<a href="${U.silabo}#t${s.t}">${pg.silabo} ${s.t}</a>`,`<a href="${U.resumo}#r${s.t}">${pg.resumo} ${s.t}</a>`,`<a href="${U.revisao}#ch${s.t}">${pg.revisao} ${s.t}</a>`];
      else links=[`<a href="${U.silabo}">${pg.silabo}</a>`,`<a href="${U.revisao}">${P.revMissed}</a>`];
      const tags=(s.carried?`<span class="tag moved">${esc(tf(P.movedFrom,{d:fmtShort(s.carried)}))}</span>`:'')+(s.boost!==undefined?`<span class="tag boost">${esc(tf(P.boost,{p:s.boost}))}</span>`:'');
      li.innerHTML=`<input type="checkbox" id="${id}" ${ok?'checked':''}><label class="what" for="${id}"><span class="chip ${s.a}">${P.act[s.a]}</span><span class="tname"></span>${tags}</label><span class="smin">${h(s.m)}</span><span class="go">${links.join('')}</span>`;
      $('.tname',li).textContent=label(s);
      $('input',li).addEventListener('change',e=>{ if(e.target.checked) done[s.key]=true; else delete done[s.key]; save(); refresh(); });
      ul.appendChild(li);
    });
    box.appendChild(sec);
  });
}
const tip=document.createElement('div'); tip.className='tip'; tip.hidden=true; document.body.appendChild(tip);
function showTip(e,html){tip.innerHTML=html; tip.hidden=false; const x=Math.min(e.clientX+12,innerWidth-250); tip.style.left=x+'px'; tip.style.top=(e.clientY+14)+'px';}
function hideTip(){tip.hidden=true}
function el(n,a,p){const x=document.createElementNS(NS,n); for(const k in a) x.setAttribute(k,a[k]); p&&p.appendChild(x); return x}
function drawBars(){
  const DD=VIEW.days; const W=Math.max(640,DD.length*52), H=230, m={l:34,r:8,t:10,b:38};
  const maxM=Math.max(60,...DD.map(D=>D.s.reduce((a,s)=>a+s.m,0))); const top=Math.ceil(maxM/60)*60;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.barsAria});
  const iw=W-m.l-m.r, ih=H-m.t-m.b, bw=iw/DD.length, y=v=>m.t+ih-v/top*ih;
  for(let v=0;v<=top;v+=60){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'var(--line)','stroke-width':1},svg); const t=el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end'},svg); t.textContent=(v/60)+'h';}
  DD.forEach((D,i)=>{
    const g=el('g',{},svg); let acc=0; const x=m.l+i*bw+bw*0.2, w=bw*0.6;
    const parts=ORDER.map(a=>({a,m:D.s.filter(s=>s.a===a).reduce((p,s)=>p+s.m,0)})).filter(p=>p.m>0);
    parts.forEach((p,pi)=>{ const isTop=pi===parts.length-1, y0=y(acc), y1=y(acc+p.m); acc+=p.m; const hgt=Math.max(0,y0-y1-(isTop?0:2));
      if(isTop){const r=Math.min(4,hgt/2,w/2); el('path',{d:`M${x},${y0}V${y1+r}Q${x},${y1} ${x+r},${y1}H${x+w-r}Q${x+w},${y1} ${x+w},${y1+r}V${y0}Z`,fill:COL(p.a)},g)}
      else el('rect',{x,y:y1+2,width:w,height:hgt,fill:COL(p.a)},g); });
    const tx=el('text',{x:x+w/2,y:H-22,'text-anchor':'middle'},svg); tx.textContent=D.d.slice(8); if(D.d===TODAY) tx.style.fill='var(--ink)';
    const tw=el('text',{x:x+w/2,y:H-8,'text-anchor':'middle'},svg); tw.textContent=wd(D.d);
    const hit=el('rect',{x:m.l+i*bw,y:m.t,width:bw,height:ih,fill:'transparent'},svg);
    const html=`<b>${wd(D.d)}, ${fmtDate(D.d)}</b><br>`+parts.map(p=>`${P.act[p.a]}: ${h(p.m)}`).join('<br>')+`<br>Total: ${h(acc)}`;
    hit.addEventListener('mousemove',e=>showTip(e,html)); hit.addEventListener('mouseleave',hideTip);
    hit.addEventListener('click',()=>document.getElementById('d'+D.d).scrollIntoView({behavior:'smooth'}));
  });
  $('#bars').replaceChildren(svg);
}
function drawTimeline(){
  const DD=VIEW.days; const rows=Object.keys(NAMES).map(Number).sort((a,b)=>a-b).concat([0]);
  const cw=44, rh=26, m={l:150,t:8,b:30}, W=m.l+DD.length*cw+8, H=m.t+rows.length*rh+m.b;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.timelineTitle});
  const nm=t=>t?`${t} ${NAMES[t].length>17?NAMES[t].slice(0,16)+'…':NAMES[t]}`:P.act.test;
  rows.forEach((t,r)=>{ const yy=m.t+r*rh+rh/2; el('line',{x1:m.l,x2:W-8,y1:yy,y2:yy,stroke:'var(--line)','stroke-width':1},svg);
    const tx=el('text',{x:m.l-8,y:yy+4,'text-anchor':'end'},svg); tx.textContent=nm(t); tx.style.fill='var(--ink)'; });
  DD.forEach((D,i)=>{
    const cx=m.l+i*cw+cw/2; const t=el('text',{x:cx,y:H-10,'text-anchor':'middle'},svg); t.textContent=D.d.slice(8);
    const by={}; D.s.forEach(s=>{ const ts=s.a==='quiz'?(s.q||[]):[s.t]; ts.forEach(x=>{(by[x]=by[x]||[]).push(s)}); });
    Object.entries(by).forEach(([tt,ss])=>{
      const r=rows.indexOf(+tt); if(r<0) return; const yy=m.t+r*rh+rh/2;
      const a=ss.some(s=>s.a==='learn')?'learn':ss.some(s=>s.a==='test')?'test':ss.some(s=>s.a==='ex')?'ex':ss.some(s=>s.a==='rev')?'rev':'quiz';
      if(a==='rev'||a==='quiz') el('circle',{cx,cy:yy,r:6,fill:'var(--surface)',stroke:COL(a),'stroke-width':3},svg); else el('circle',{cx,cy:yy,r:7,fill:COL(a),stroke:'var(--surface)','stroke-width':2},svg);
      const hit=el('rect',{x:cx-cw/2,y:yy-rh/2,width:cw,height:rh,fill:'transparent'},svg);
      const html=`<b>${esc(nm(+tt))}</b><br>${wd(D.d)}, ${fmtDate(D.d)}<br>`+ss.map(s=>`${P.act[s.a]}: ${h(s.m)}`).join('<br>');
      hit.addEventListener('mousemove',e=>showTip(e,html)); hit.addEventListener('mouseleave',hideTip);
    });
  });
  $('#timeline').replaceChildren(svg);
}
function drawProgress(){
  const DD=VIEW.days; const W=Math.max(640,DD.length*52), H=200, m={l:34,r:70,t:12,b:30};
  const n=DD.length; let p=0,dn=0; const plan=[],don=[];
  DD.forEach(D=>{p+=D.s.reduce((a,s)=>a+s.m,0); D.s.forEach(s=>{if(isDone(s)) dn+=s.m}); plan.push(p); if(D.d<=TODAY) don.push(dn);});
  const max=Math.max(60,Math.ceil(p/240)*240);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.progTitle});
  const iw=W-m.l-m.r, ih=H-m.t-m.b, x=i=>m.l+i*(iw/Math.max(1,n-1)), y=v=>m.t+ih-v/max*ih;
  for(let v=0;v<=max;v+=max/4){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'var(--line)','stroke-width':1},svg); const t=el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end'},svg); t.textContent=Math.round(v/60)+'h';}
  el('path',{d:plan.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(''),fill:'none',stroke:'var(--muted)','stroke-width':2,'stroke-dasharray':'5 5'},svg);
  const lp=el('text',{x:x(n-1)+6,y:y(plan[n-1])+4},svg); lp.textContent=P.planned;
  if(don.length){ el('path',{d:don.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(''),fill:'none',stroke:'var(--accent)','stroke-width':2.5},svg);
    const li=don.length-1; el('circle',{cx:x(li),cy:y(don[li]),r:5,fill:'var(--accent)',stroke:'var(--surface)','stroke-width':2},svg);
    const ld=el('text',{x:x(li)+8,y:y(don[li])-8},svg); ld.textContent=P.done+' '+h(don[li]||0); ld.style.fill='var(--ink)'; }
  DD.forEach((D,i)=>{ if(i%2===0||i===n-1){const t=el('text',{x:x(i),y:H-8,'text-anchor':'middle'},svg); t.textContent=D.d.slice(8);}
    const hit=el('rect',{x:x(i)-iw/Math.max(1,n-1)/2,y:m.t,width:iw/Math.max(1,n-1),height:ih,fill:'transparent'},svg);
    hit.addEventListener('mousemove',e=>showTip(e,`<b>${wd(D.d)}, ${fmtDate(D.d)}</b><br>${P.planned}: ${h(plan[i])}`+(i<don.length?`<br>${P.done}: ${h(don[i])}`:'')));
    hit.addEventListener('mouseleave',hideTip); });
  $('#prog').replaceChildren(svg);
}
function refresh(){ VIEW=adapt(); renderAdapt(); renderDays(); summary(); drawBars(); drawTimeline(); drawProgress(); }
function save(){
  lsSet(Store.lsName('plano'),JSON.stringify(done)); clearTimeout(timer);
  if(ref) timer=setTimeout(async()=>{try{await ref.set({done}); $('#saved').textContent=T.savedAccount}catch(e){$('#saved').textContent=T.savedLocal}},800);
}
async function initStore(){
  try{const r=lsGet(Store.lsName('plano')); if(r) done=JSON.parse(r)||{};}catch(e){}
  if(TESTS.length){ const r=await Store.load('testes'); if(r.data&&r.data.results) RES=r.data; }
  refresh();
  const s=await Store.init(); if(!s){$('#saved').textContent=T.savedLocal; return;}
  try{ ref=s.db.doc(Store.docPath(s.uid,'plano')); const snap=await ref.get(); if(snap.exists) done={...(snap.data().done||{}),...done};
    refresh(); $('#saved').textContent=T.savedAccount; if(Object.keys(done).length) save(); }catch(e){$('#saved').textContent=T.savedLocal;}
}
$('#todayBtn')&&$('#todayBtn').addEventListener('click',()=>{const td=document.getElementById('d'+TODAY)||$$('.day').find(d=>d.id.slice(1)>TODAY); td&&td.scrollIntoView({behavior:'smooth',block:'start'});});
$('#hideDoneBtn')&&$('#hideDoneBtn').addEventListener('click',e=>{const on=document.body.classList.toggle('hide-done'); e.currentTarget.setAttribute('aria-pressed',String(on)); lsSet(LSK('hidedone'),on?'1':'');});
$('#origBtn')&&$('#origBtn').addEventListener('click',e=>{showOrig=!showOrig; e.currentTarget.setAttribute('aria-pressed',String(showOrig)); refresh();});
if(lsGet(LSK('hidedone'))){document.body.classList.add('hide-done'); $('#hideDoneBtn')&&$('#hideDoneBtn').setAttribute('aria-pressed','true');}
window.addEventListener('themechange',()=>{drawBars(); drawTimeline(); drawProgress();});
VIEW=adapt(); refresh(); commonInit(); initStore();
