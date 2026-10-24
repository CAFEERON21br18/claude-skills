/* study-pack kit — Plano page. PLAN = {days:[{d:"YYYY-MM-DD",note,s:[{t,a,m}]}]} written by build.py.
   Ticks are keyed by date + index: never move dated sessions in an update. */
const P=T.plan, DAYS=PLAN.days, NAMES=PACK.topics, ORDER=['learn','ex','rev','test'];
const NS='http://www.w3.org/2000/svg';
const COL=a=>({learn:'var(--accent)',ex:'var(--accent2)',rev:'var(--warn)',test:'var(--bad)'}[a]);
let done={}, ref=null, timer=null;
function todayISO(){const d=new Date(); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)}
const TODAY=todayISO();
const keyOf=(di,si)=>DAYS[di].d+'#'+si;
const wd=d=>new Date(d+'T12:00:00Z').toLocaleDateString(T.locale,{weekday:'short',timeZone:'UTC'}).replace('.','');
const fmtDate=d=>new Date(d+'T12:00:00Z').toLocaleDateString(T.locale,{day:'numeric',month:'long',timeZone:'UTC'});
const label=s=>s.t?`${s.t} · ${NAMES[s.t]}`:(s.a==='test'?P.mixed:P.reserve);
const h=m=>{const H=Math.floor(m/60),M=m%60; return (H?H+'h':'')+(M?String(M).padStart(H?2:1,'0')+(H?'':' min'):'')||'0h'};
const U=PACK.urls;
function summary(){
  const d=calDays(); $('#sDays').textContent=d===null?'–':Math.max(0,d);
  let tot=0,dn=0,ns=0,nd=0; DAYS.forEach((D,di)=>D.s.forEach((s,si)=>{tot+=s.m; ns++; if(done[keyOf(di,si)]){dn+=s.m; nd++;}}));
  $('#sHours').textContent=Math.round(tot/60)+'h'; $('#sDone').textContent=tf(P.hoursDone,{d:h(dn),t:Math.round(tot/60)+'h'});
  $('#oText').textContent=tf(T.planOverall,{done:nd,total:ns,hd:h(dn),ht:Math.round(tot/60)+'h'});
  $('#oOk').style.width=(dn/(tot||1)*100)+'%';
}
function renderDays(){
  const box=$('#days'); box.innerHTML='';
  DAYS.forEach((D,di)=>{
    const tot=D.s.reduce((a,s)=>a+s.m,0);
    const sec=document.createElement('section'); sec.className='day'+(D.d===TODAY?' today':'')+(D.d<TODAY?' past':''); sec.id='d'+D.d;
    sec.innerHTML=`<div class="dh"><h3>${wd(D.d)}, ${fmtDate(D.d)}</h3><span class="hrs">${h(tot)}</span>${D.d===TODAY?`<span class="tag now">${P.today}</span>`:''}${D.note?`<span class="tag">${esc(D.note)}</span>`:''}</div><ul class="sess"></ul>`;
    const ul=$('ul',sec);
    D.s.forEach((s,si)=>{
      const k=keyOf(di,si), id='c'+di+'-'+si; const li=document.createElement('li'); if(done[k]) li.classList.add('done');
      const pg=T.page;
      const links=s.t?[`<a href="${U.silabo}#t${s.t}">${pg.silabo} ${s.t}</a>`,`<a href="${U.resumo}#r${s.t}">${pg.resumo} ${s.t}</a>`,`<a href="${U.revisao}#ch${s.t}">${pg.revisao} ${s.t}</a>`]
        :[`<a href="${U.silabo}">${pg.silabo}</a>`,`<a href="${U.revisao}">${P.revMissed}</a>`];
      li.innerHTML=`<input type="checkbox" id="${id}" ${done[k]?'checked':''}><label class="what" for="${id}"><span class="chip ${s.a}">${P.act[s.a]}</span><span class="tname"></span></label><span class="smin">${h(s.m)}</span><span class="go">${links.join('')}</span>`;
      $('.tname',li).textContent=label(s);
      $('input',li).addEventListener('change',e=>{ if(e.target.checked) done[k]=true; else delete done[k]; li.classList.toggle('done',e.target.checked); save(); summary(); drawProgress(); });
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
  const W=Math.max(640,DAYS.length*52), H=230, m={l:34,r:8,t:10,b:38};
  const maxM=Math.max(60,...DAYS.map(D=>D.s.reduce((a,s)=>a+s.m,0))); const top=Math.ceil(maxM/60)*60;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.barsAria});
  const iw=W-m.l-m.r, ih=H-m.t-m.b, bw=iw/DAYS.length, y=v=>m.t+ih-v/top*ih;
  for(let v=0;v<=top;v+=60){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'var(--line)','stroke-width':1},svg); const t=el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end'},svg); t.textContent=(v/60)+'h';}
  DAYS.forEach((D,i)=>{
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
  const rows=Object.keys(NAMES).map(Number).sort((a,b)=>a-b).concat([0]);
  const cw=44, rh=26, m={l:150,t:8,b:30}, W=m.l+DAYS.length*cw+8, H=m.t+rows.length*rh+m.b;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.timelineTitle});
  const nm=t=>t?`${t} ${NAMES[t].length>17?NAMES[t].slice(0,16)+'…':NAMES[t]}`:P.act.test;
  rows.forEach((t,r)=>{ const yy=m.t+r*rh+rh/2; el('line',{x1:m.l,x2:W-8,y1:yy,y2:yy,stroke:'var(--line)','stroke-width':1},svg);
    const tx=el('text',{x:m.l-8,y:yy+4,'text-anchor':'end'},svg); tx.textContent=nm(t); tx.style.fill='var(--ink)'; });
  DAYS.forEach((D,i)=>{
    const cx=m.l+i*cw+cw/2; const t=el('text',{x:cx,y:H-10,'text-anchor':'middle'},svg); t.textContent=D.d.slice(8);
    const by={}; D.s.forEach(s=>{(by[s.t]=by[s.t]||[]).push(s)});
    Object.entries(by).forEach(([tt,ss])=>{
      const r=rows.indexOf(+tt); if(r<0) return; const yy=m.t+r*rh+rh/2;
      const a=ss.some(s=>s.a==='learn')?'learn':ss.some(s=>s.a==='test')?'test':ss.some(s=>s.a==='ex')?'ex':'rev';
      if(a==='rev') el('circle',{cx,cy:yy,r:6,fill:'var(--surface)',stroke:COL('rev'),'stroke-width':3},svg); else el('circle',{cx,cy:yy,r:7,fill:COL(a),stroke:'var(--surface)','stroke-width':2},svg);
      const hit=el('rect',{x:cx-cw/2,y:yy-rh/2,width:cw,height:rh,fill:'transparent'},svg);
      const html=`<b>${esc(nm(+tt))}</b><br>${wd(D.d)}, ${fmtDate(D.d)}<br>`+ss.map(s=>`${P.act[s.a]}: ${h(s.m)}`).join('<br>');
      hit.addEventListener('mousemove',e=>showTip(e,html)); hit.addEventListener('mouseleave',hideTip);
    });
  });
  $('#timeline').replaceChildren(svg);
}
function drawProgress(){
  const W=Math.max(640,DAYS.length*52), H=200, m={l:34,r:70,t:12,b:30};
  const n=DAYS.length; let p=0,dn=0; const plan=[],don=[];
  DAYS.forEach((D,di)=>{p+=D.s.reduce((a,s)=>a+s.m,0); D.s.forEach((s,si)=>{if(done[keyOf(di,si)]) dn+=s.m}); plan.push(p); if(D.d<=TODAY) don.push(dn);});
  const max=Math.max(60,Math.ceil(p/240)*240);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,role:'img','aria-label':P.progTitle});
  const iw=W-m.l-m.r, ih=H-m.t-m.b, x=i=>m.l+i*(iw/Math.max(1,n-1)), y=v=>m.t+ih-v/max*ih;
  for(let v=0;v<=max;v+=max/4){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'var(--line)','stroke-width':1},svg); const t=el('text',{x:m.l-6,y:y(v)+4,'text-anchor':'end'},svg); t.textContent=Math.round(v/60)+'h';}
  el('path',{d:plan.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(''),fill:'none',stroke:'var(--muted)','stroke-width':2,'stroke-dasharray':'5 5'},svg);
  const lp=el('text',{x:x(n-1)+6,y:y(plan[n-1])+4},svg); lp.textContent=P.planned;
  if(don.length){ el('path',{d:don.map((v,i)=>(i?'L':'M')+x(i)+','+y(v)).join(''),fill:'none',stroke:'var(--accent)','stroke-width':2.5},svg);
    const li=don.length-1; el('circle',{cx:x(li),cy:y(don[li]),r:5,fill:'var(--accent)',stroke:'var(--surface)','stroke-width':2},svg);
    const ld=el('text',{x:x(li)+8,y:y(don[li])-8},svg); ld.textContent=P.done+' '+h(don[li]||0); ld.style.fill='var(--ink)'; }
  DAYS.forEach((D,i)=>{ if(i%2===0||i===n-1){const t=el('text',{x:x(i),y:H-8,'text-anchor':'middle'},svg); t.textContent=D.d.slice(8);}
    const hit=el('rect',{x:x(i)-iw/Math.max(1,n-1)/2,y:m.t,width:iw/Math.max(1,n-1),height:ih,fill:'transparent'},svg);
    hit.addEventListener('mousemove',e=>showTip(e,`<b>${wd(D.d)}, ${fmtDate(D.d)}</b><br>${P.planned}: ${h(plan[i])}`+(i<don.length?`<br>${P.done}: ${h(don[i])}`:'')));
    hit.addEventListener('mouseleave',hideTip); });
  $('#prog').replaceChildren(svg);
}
function save(){
  lsSet(Store.lsName('plano'),JSON.stringify(done)); clearTimeout(timer);
  if(ref) timer=setTimeout(async()=>{try{await ref.set({done}); $('#saved').textContent=T.savedAccount}catch(e){$('#saved').textContent=T.savedLocal}},800);
}
async function initStore(){
  try{const r=lsGet(Store.lsName('plano')); if(r) done=JSON.parse(r)||{};}catch(e){}
  const s=await Store.init(); if(!s){$('#saved').textContent=T.savedLocal; return;}
  try{ ref=s.db.doc(Store.docPath(s.uid,'plano')); const snap=await ref.get(); if(snap.exists) done={...(snap.data().done||{}),...done};
    renderDays(); summary(); drawProgress(); $('#saved').textContent=T.savedAccount; if(Object.keys(done).length) save(); }catch(e){$('#saved').textContent=T.savedLocal;}
}
$('#todayBtn')&&$('#todayBtn').addEventListener('click',()=>{const td=document.getElementById('d'+TODAY)||$$('.day').find(d=>d.id.slice(1)>TODAY); td&&td.scrollIntoView({behavior:'smooth',block:'start'});});
$('#hideDoneBtn')&&$('#hideDoneBtn').addEventListener('click',e=>{const on=document.body.classList.toggle('hide-done'); e.currentTarget.setAttribute('aria-pressed',String(on)); lsSet(LSK('hidedone'),on?'1':'');});
if(lsGet(LSK('hidedone'))){document.body.classList.add('hide-done'); $('#hideDoneBtn')&&$('#hideDoneBtn').setAttribute('aria-pressed','true');}
window.addEventListener('themechange',()=>{drawBars(); drawTimeline(); drawProgress();});
renderDays(); summary(); drawBars(); drawTimeline(); drawProgress(); commonInit(); initStore();
