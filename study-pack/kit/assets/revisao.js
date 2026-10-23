/* study-pack kit — Revisão page: exercises, grading by Claude, history, "missed only". */
const TOTAL=$$('.ex').length;
let state={status:{},attempts:[]};
let dbRef=null, saveTimer=null;
const DOCNAME='revisao';
function saveSoon(){
  lsSet(Store.lsName(DOCNAME),JSON.stringify(state)); clearTimeout(saveTimer);
  if(dbRef) saveTimer=setTimeout(async()=>{try{await dbRef.set({status:state.status,attempts:state.attempts.slice(-400)}); $('#saved').textContent=T.savedAccount}catch(e){$('#saved').textContent=T.savedLocal}},900);
}
async function initStore(){
  try{const raw=lsGet(Store.lsName(DOCNAME)); if(raw){const s=JSON.parse(raw); if(s&&s.status) state=s;}}catch(e){}
  applyAll();
  const s=await Store.init();
  if(!s){$('#saved').textContent=T.savedLocal; return;}
  try{
    dbRef=s.db.doc(Store.docPath(s.uid,DOCNAME)); const snap=await dbRef.get();
    if(snap.exists){const d=snap.data(); state={status:{...(d.status||{}),...state.status},attempts:mergeAtt(d.attempts||[],state.attempts)};}
    applyAll(); $('#saved').textContent=T.savedAccount; if(Object.keys(state.status).length) saveSoon();
  }catch(e){$('#saved').textContent=T.savedLocal;}
}
function mergeAtt(a,b){const seen=new Set(),out=[];for(const x of [...a,...b]){const k=x.id+x.t;if(!seen.has(k)){seen.add(k);out.push(x)}}return out.sort((p,q)=>p.t-q.t)}
function applyAll(){ $$('.ex').forEach(ex=>markCard(ex,state.status[ex.dataset.id])); progress(); }
function markCard(ex,s){
  ex.classList.toggle('is-ok',s==='ok'); ex.classList.toggle('is-miss',s==='miss');
  const b=$('.badge',ex); if(s){b.hidden=false;b.className='badge '+s;b.textContent=s==='ok'?T.badgeOk:T.badgeMiss;} else b.hidden=true;
}
function progress(){
  let ok=0,miss=0;
  $$('.topic').forEach(sec=>{
    const n=sec.dataset.n, cards=$$('.ex',sec); let o=0,m=0;
    const dots=$(`.dots[data-n="${n}"]`); if(dots) dots.innerHTML='';
    cards.forEach(c=>{const s=state.status[c.dataset.id]; if(s==='ok')o++; if(s==='miss')m++; if(dots){const i=document.createElement('i'); if(s) i.className=s; dots.appendChild(i);}});
    ok+=o; miss+=m; sec.classList.toggle('has-miss',m>0);
    const L=cards.length||1, tc=$('.tcount',sec);
    if(tc){ tc.textContent=tf(T.tcount,{done:o+m,total:cards.length,ok:o}); $('.tprog .okb',sec).style.width=(o/L*100)+'%'; $('.tprog .badb',sec).style.width=(m/L*100)+'%'; }
  });
  $('#oText').textContent=tf(T.overall,{done:ok+miss,total:TOTAL,ok,miss});
  $('#oOk').style.width=(ok/(TOTAL||1)*100)+'%'; $('#oBad').style.width=(miss/(TOTAL||1)*100)+'%';
  $('#emptyMiss').classList.toggle('show',miss===0);
  renderHist();
}
function record(id,ok,ans){
  state.status[id]=ok?'ok':'miss'; state.attempts.push({id,ok,a:String(ans).slice(0,140),t:Date.now()});
  markCard(document.getElementById(id),state.status[id]); progress(); saveSoon();
}
function showKey(ex){ const k=$('.key',ex); if(k&&k.hidden){k.hidden=false; typeset(k);} const r=$('.redo',ex); if(r) r.hidden=false; }
function resetCard(ex){
  delete ex.dataset.done;
  $$('.opt',ex).forEach(o=>{o.disabled=false;o.classList.remove('right','wrong')});
  const fb=$('.fb',ex); if(fb) fb.hidden=true;
  const g=$('.gate',ex); if(g){ g.hidden=false; const o=$('.opts',ex); if(o) o.hidden=true; }
  const k=$('.key',ex); if(k) k.hidden=true; const v=$('.verdict',ex); if(v) v.hidden=true;
  const ta=$('textarea[id^="ta-"]',ex); if(ta) ta.value=''; const er=$('.err',ex); if(er) er.hidden=true;
  const r=$('.redo',ex); if(r) r.hidden=true;
  ex.scrollIntoView({behavior:'smooth',block:'start'});
}
/* paper-first gate: options stay hidden until "I've solved it" */
$$('.gatebtn').forEach(b=>b.addEventListener('click',()=>{ const ex=b.closest('.ex'); b.closest('.gate').hidden=true; const o=$('.opts',ex); o.hidden=false; typeset(o); setTimeout(()=>fitMath(ex),30); Focus.update(); }));
/* choice exercises (mcq / tf) */
$$('.ex.mcq,.ex.tf').forEach(ex=>{
  const correct=ex.dataset.correct;
  $$('.opt',ex).forEach(btn=>btn.addEventListener('click',()=>{
    if(ex.dataset.done) return; ex.dataset.done='1'; const i=btn.dataset.v;
    $$('.opt',ex).forEach(o=>{o.disabled=true; if(o.dataset.v===correct) o.classList.add('right');});
    if(i!==correct) btn.classList.add('wrong');
    const fb=$('.fb',ex); fb.hidden=false; $$('.why',fb).forEach(w=>w.hidden=!(w.dataset.v===i||w.dataset.v===correct));
    showKey(ex); typeset(fb); record(ex.dataset.id,i===correct,$('.L',btn).textContent);
  }));
});
$$('.ex').forEach(ex=>{ const r=$('.redo',ex); r&&r.addEventListener('click',()=>resetCard(ex)); });
/* free answer (also under calculation MCQs): corrected by Claude, else self-assessment */
let sample=null, imgOk=false;
$$('.freebox').forEach(box=>{
  const ex=box.closest('.ex'), id=ex.dataset.id, ta=$('textarea',box), err=$('.err',box), out=$('.verdict',box);
  ta.addEventListener('input',()=>{err.hidden=true});
  const sk=$('.showkey',box); sk&&sk.addEventListener('click',()=>showKey(ex));
  $$('[data-self]',ex).forEach(b=>b.addEventListener('click',()=>record(id,b.dataset.self==='ok',ta.value.trim()?T.selfEval+': '+ta.value.trim():T.selfEval)));
  let ctl=null;
  $('.stop',box).addEventListener('click',()=>ctl&&ctl.abort());
  $('.grade',box).addEventListener('click',async()=>{
    const files=$('input[type=file]',box)?.files; const hasImg=imgOk&&files&&files.length>0;
    if(!ta.value.trim()&&!hasImg){err.textContent=T.writeFirst; err.hidden=false; return;}
    const q=readable($('.q',ex)), key=readable($('.key',ex),'button,.self');
    const prompt=tf(T.gradePrompt,{course:PACK.course,langName:T.langName,q,key,img:hasImg?T.imgNote:'',ans:ta.value.trim()||T.seeImage});
    ctl=new AbortController(); out.hidden=false; out.className='verdict'; out.innerHTML=`<span class="vt">${T.thinking}</span>`;
    $('.grade',box).disabled=true; $('.stop',box).hidden=false;
    try{
      const opts={signal:ctl.signal,cache:false,onText:({text})=>{out.innerHTML=md(text)}}; if(hasImg) opts.images=files;
      const {text}=await sample(prompt,opts);
      const first=(text.trim().split('\n')[0]||'').toUpperCase(); const W=T.gradeWords;
      const v=first.includes(W.miss)?'miss':first.includes(W.part)?'part':first.includes(W.ok)?'ok':null;
      const lab=T.verdict[v||'none']; const body=text.trim().split('\n').slice(v?1:0).join('\n').trim();
      out.className='verdict '+(v==='ok'?'v-ok':v?'v-miss':''); out.innerHTML=`<span class="vt">${lab}</span>${md(body)}`; typeset(out);
      if(v) record(id,v==='ok',ta.value.trim()||T.photoWord); $('.redo',ex).hidden=false;
    }catch(e){
      const keep=e&&e.text?md(e.text):''; const msg=T.gradeErr[e&&e.code]||T.gradeErr.other;
      out.innerHTML=keep+`<p class="err">${msg}</p>`;
      if(e&&(e.code==='not_granted'||e.code==='sampling_disabled')) $$('.grade').forEach(b=>b.hidden=true);
    }finally{ $('.grade',box).disabled=false; $('.stop',box).hidden=true; }
  });
});
async function initSample(){
  if(!window.claude||!claude.use) return;
  try{ sample=await claude.use('sample'); if(!sample) return; $$('.grade').forEach(b=>b.hidden=false);
    const lim=await sample.limits().catch(()=>null); imgOk=!!(lim&&lim.images);
    if(imgOk) $$('.photo').forEach(p=>{p.hidden=false; const inp=$('input',p); if(lim.images.mediaTypes) inp.accept=lim.images.mediaTypes.join(',');});
  }catch(e){}
}
/* history */
let hFilter='all';
function renderHist(){
  const ul=$('#hlist'); if(!ul) return; const H=T.hist;
  const items=state.attempts.slice().reverse().filter(a=>hFilter==='all'||(hFilter==='ok'?a.ok:!a.ok));
  ul.innerHTML='';
  if(!items.length){ul.innerHTML=`<li class="empty-note">${H.empty}</li>`;return;}
  items.slice(0,200).forEach(a=>{
    const ex=document.getElementById(a.id); const li=document.createElement('li'); li.className='item'; const d=new Date(a.t);
    const ns=ex?Notes.list(a.id):[];
    const head=ex?`<b class="mono" style="color:var(--ink)">${esc($('.exn',ex).textContent)}</b><span>${esc($('.src',ex).textContent)}</span>`:`<span>${H.old}</span>`;
    li.innerHTML=`<div class="il">${head}<span style="color:${a.ok?'var(--ok)':'var(--bad)'};font-weight:700">${a.ok?H.right:H.wrong}</span><span>${d.toLocaleDateString(T.locale,{day:'numeric',month:'short'})} ${d.toLocaleTimeString(T.locale,{hour:'2-digit',minute:'2-digit'})}</span></div><div class="hm"></div>${ns.length?`<div class="hint">${ns.length} ${ns.length>1?H.notesN:H.notes1}: ${esc(ns.map(n=>n.text.replace(/\*\*/g,'')).join(' · ').slice(0,160))}</div>`:''}${ex?`<div><button type="button" class="btn sm">${T.redo}</button></div>`:''}`;
    $('.hm',li).textContent=a.a;
    if(ex) $('button',li).addEventListener('click',()=>{closeHist(); resetCard(ex);});
    ul.appendChild(li);
  });
}
function openHist(){$('#hist').hidden=false; $('#scrim').hidden=false; $('#histBtn').setAttribute('aria-expanded','true'); $('#histClose').focus();}
function closeHist(){$('#hist').hidden=true; if($('.side.open')) return; $('#scrim').hidden=true; $('#histBtn').setAttribute('aria-expanded','false');}
$('#histBtn')&&$('#histBtn').addEventListener('click',openHist);
$('#histClose')&&$('#histClose').addEventListener('click',closeHist);
$$('#hist [data-f]').forEach(b=>b.addEventListener('click',()=>{hFilter=b.dataset.f; $$('#hist [data-f]').forEach(x=>x.setAttribute('aria-pressed',String(x===b))); renderHist();}));
$('#scrim').addEventListener('click',closeHist);
document.addEventListener('keydown',e=>{if(e.key==='Escape') closeHist();});
$('#reviewBtn')&&$('#reviewBtn').addEventListener('click',e=>{const on=document.body.classList.toggle('review-only'); e.currentTarget.setAttribute('aria-pressed',String(on)); Focus.update();});
commonInit(); initStore(); initSample();
