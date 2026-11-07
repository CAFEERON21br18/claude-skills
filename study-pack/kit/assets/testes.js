/* study-pack kit — Testes page: daily tests (from the plan), topic tests, full mock tests.
   Answer everything first, then grade: full step-by-step solution for every question.
   Results are saved in "<prefix>testes" ({results:{testId:{t,ok,tot,byTopic:{n:[ok,tot]},pending}}}) and read by the Plano. */
const X=T.tests;
let RES={results:{}}, sample=null, imgOk=false;
function pct(ok,tot){return tot?Math.round(ok/tot*100):0}
function saveRes(){ Store.save('testes',RES); }
function overall(){
  const cards=$$('.tst'), done=cards.filter(c=>RES.results[c.dataset.test]&&!RES.results[c.dataset.test].pending);
  const ps=done.map(c=>{const r=RES.results[c.dataset.test]; return pct(r.ok,r.tot);});
  $('#oText').textContent=tf(X.overall,{done:done.length,total:cards.length,avg:ps.length?Math.round(ps.reduce((a,b)=>a+b,0)/ps.length)+'%':X.noAvg});
  $('#oOk').style.width=(done.length/(cards.length||1)*100)+'%';
  cards.forEach(c=>{ const r=RES.results[c.dataset.test], b=$('.tscore',c);
    if(r&&!r.pending){ b.hidden=false; b.textContent=tf(X.score,{p:pct(r.ok,r.tot)}); b.classList.toggle('low',pct(r.ok,r.tot)<60); b.title=tf(X.last,{p:pct(r.ok,r.tot),d:fmtD(r.t)}); }
    else b.hidden=true; });
}
/* ----- answering (no feedback until the end) ----- */
$$('.tst').forEach(card=>{
  const body=$('.tstbody',card), start=$('.tstart',card);
  start.addEventListener('click',()=>{ const open=!body.hidden; body.hidden=open; start.textContent=open?X.start:X.open; if(!open){ typeset(body); card.scrollIntoView({behavior:'smooth',block:'start'}); } });
  $$('.gatebtn',card).forEach(b=>b.addEventListener('click',()=>{ const ex=b.closest('.ex'); b.closest('.gate').hidden=true; const o=$('.opts',ex); o.hidden=false; typeset(o); setTimeout(()=>fitMath(ex),30); }));
  $$('.ex.mcq .opt,.ex.tf .opt',card).forEach(o=>o.addEventListener('click',()=>{ const ex=o.closest('.ex'); if(card.dataset.graded) return;
    $$('.opt',ex).forEach(x=>{x.classList.toggle('sel',x===o); x.setAttribute('aria-pressed',String(x===o));}); ex.dataset.ans=o.dataset.v; }));
  $('.tfinish',card).addEventListener('click',()=>finish(card));
  $('.tredo',card).addEventListener('click',()=>redo(card));
  $$('.ex.free',card).forEach(ex=>{
    $$('[data-self]',ex).forEach(b=>b.addEventListener('click',()=>{ ex.dataset.self=b.dataset.self; $$('[data-self]',ex).forEach(x=>x.setAttribute('aria-pressed',String(x===b))); mark(ex,b.dataset.self==='ok'); score(card); }));
    const g=$('.grade',ex); if(g) g.addEventListener('click',()=>grade(card,ex));
  });
});
function mark(ex,ok){ ex.classList.toggle('is-ok',ok); ex.classList.toggle('is-miss',!ok); const b=$('.badge',ex); b.hidden=false; b.className='badge '+(ok?'ok':'miss'); b.textContent=ok?T.badgeOk:T.badgeMiss; }
function finish(card){
  card.dataset.graded='1';
  $$('.ex',card).forEach(ex=>{
    if(ex.classList.contains('free')){ const k=$('.key',ex); k.hidden=false; typeset(k); return; }
    const correct=ex.dataset.correct, ans=ex.dataset.ans;
    const g=$('.gate',ex); if(g){ g.hidden=true; $('.opts',ex).hidden=false; }
    $$('.opt',ex).forEach(o=>{o.disabled=true; if(o.dataset.v===correct) o.classList.add('right'); if(ans!==undefined&&o.dataset.v===ans&&ans!==correct) o.classList.add('wrong');});
    if(ans===undefined){ const u=document.createElement('p'); u.className='unans'; u.textContent=X.unanswered; $('.q',ex).after(u); }
    const fb=$('.fb',ex); fb.hidden=false; $$('.why',fb).forEach(w=>w.hidden=!(w.dataset.v===ans||w.dataset.v===correct));
    const k=$('.key',ex); k.hidden=false; typeset(fb); typeset(k);
    mark(ex,ans===correct);
  });
  $('.tfinish',card).hidden=true; $('.tredo',card).hidden=false;
  score(card); setTimeout(()=>fitMath(card),60);
}
function score(card){
  const by={}; let ok=0,tot=0,pending=0;
  $$('.ex',card).forEach(ex=>{ const n=ex.dataset.topic; by[n]=by[n]||[0,0];
    let good=null;
    if(ex.classList.contains('free')){ if(ex.dataset.self) good=ex.dataset.self==='ok'; else { pending++; return; } }
    else good=ex.dataset.ans===ex.dataset.correct;
    by[n][1]++; tot++; if(good){by[n][0]++; ok++;} });
  const r={t:Date.now(),ok,tot,byTopic:by,pending}; RES.results[card.dataset.test]=r; saveRes(); overall();
  const box=$('.tresult',card); box.hidden=false;
  const rows=Object.entries(by).filter(([,v])=>v[1]).map(([n,v])=>`<tr><td>${T.topic} ${n} · ${esc(PACK.topics[n]||'')}</td><td class="mono${pct(v[0],v[1])<60?' lowt':''}">${v[0]}/${v[1]}</td></tr>`).join('');
  const weak=Object.entries(by).filter(([,v])=>v[1]&&pct(v[0],v[1])<60).map(([n])=>n);
  box.innerHTML=`<b>${tf(X.result,{ok,tot,p:pct(ok,tot)})}</b>${pending?`<p class="hint">${tf(X.pending,{n:pending})}</p>`:''}<div><b>${X.byTopic}</b><table>${rows}</table></div>`
    +(pending?'':`<p>${weak.length?tf(X.weak,{list:weak.map(n=>T.topic+' '+n).join(', ')}):X.strong}</p>`);
}
function redo(card){
  delete card.dataset.graded; delete RES.results[card.dataset.test]; saveRes(); overall();
  $$('.ex',card).forEach(ex=>{ delete ex.dataset.ans; delete ex.dataset.self; ex.classList.remove('is-ok','is-miss'); $('.badge',ex).hidden=true;
    $$('.opt',ex).forEach(o=>{o.disabled=false; o.classList.remove('right','wrong','sel'); o.removeAttribute('aria-pressed');});
    const g=$('.gate',ex); if(g){ g.hidden=false; $('.opts',ex).hidden=true; }
    $$('.unans',ex).forEach(u=>u.remove()); const fb=$('.fb',ex); if(fb) fb.hidden=true; $('.key',ex).hidden=true;
    const ta=$('textarea',ex); if(ta) ta.value=''; const v=$('.verdict',ex); if(v) v.hidden=true; $$('[data-self]',ex).forEach(x=>x.removeAttribute('aria-pressed')); });
  $('.tfinish',card).hidden=false; $('.tredo',card).hidden=true; $('.tresult',card).hidden=true;
  card.scrollIntoView({behavior:'smooth',block:'start'});
}
/* free answers can be graded by Claude (after the end, or any time) */
async function grade(card,ex){
  const box=$('.freebox',ex), ta=$('textarea',box), err=$('.err',box), out=$('.verdict',box);
  const files=$('input[type=file]',box)?.files; const hasImg=imgOk&&files&&files.length>0;
  if(!ta.value.trim()&&!hasImg){err.textContent=T.writeFirst; err.hidden=false; return;}
  const prompt=tf(T.gradePrompt,{course:PACK.course,langName:T.langName,q:readable($('.q',ex)),key:readable($('.key',ex),'button,.self'),img:hasImg?T.imgNote:'',ans:ta.value.trim()||T.seeImage});
  out.hidden=false; out.className='verdict'; out.innerHTML=`<span class="vt">${T.thinking}</span>`; const g=$('.grade',box); g.disabled=true;
  try{
    const opts={cache:false,onText:({text})=>{out.innerHTML=md(text)}}; if(hasImg) opts.images=files;
    const {text}=await sample(prompt,opts); const first=(text.trim().split('\n')[0]||'').toUpperCase(); const W=T.gradeWords;
    const v=first.includes(W.miss)?'miss':first.includes(W.part)?'part':first.includes(W.ok)?'ok':null;
    out.className='verdict '+(v==='ok'?'v-ok':v?'v-miss':''); out.innerHTML=`<span class="vt">${T.verdict[v||'none']}</span>${md(text.trim().split('\n').slice(v?1:0).join('\n'))}`; typeset(out);
    if(v&&ex.classList.contains('free')){ ex.dataset.self=v==='ok'?'ok':'miss'; mark(ex,v==='ok'); if(card.dataset.graded) score(card); }
  }catch(e){ out.innerHTML=`<p class="err">${T.gradeErr[e&&e.code]||T.gradeErr.other}</p>`; }
  finally{ g.disabled=false; }
}
async function initSample(){
  if(!window.claude||!claude.use){ $('#gradeOff').hidden=false; return; }
  try{ sample=await claude.use('sample'); if(!sample){ $('#gradeOff').hidden=false; return; } $$('.grade').forEach(b=>b.hidden=false);
    const lim=await sample.limits().catch(()=>null); imgOk=!!(lim&&lim.images); if(imgOk) $$('.photo').forEach(p=>p.hidden=false);
  }catch(e){ $('#gradeOff').hidden=false; }
}
/* today's test */
function todayISO(){const d=new Date(); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10)}
const TODAY=todayISO();
$$('.tst[data-date]').forEach(c=>c.classList.toggle('today',c.dataset.date===TODAY));
$('#todayBtn')&&$('#todayBtn').addEventListener('click',()=>{ const c=$$('.tst[data-date]').find(x=>x.dataset.date>=TODAY)||$('.tst'); if(c){ c.scrollIntoView({behavior:'smooth',block:'start'}); c.classList.add('flash'); setTimeout(()=>c.classList.remove('flash'),1600); } });
(async()=>{ const r=await Store.load('testes'); if(r.data&&r.data.results) RES=r.data; $('#saved').textContent=r.remote?T.savedAccount:T.savedLocal; overall(); })();
commonInit(); initSample();
