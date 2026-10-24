/* study-pack kit — shared runtime for the four pages (from the CDI pack).
   PACK is written by build.py: page, title, course, short, t (UI strings), exam, urls, topics, store, features. */
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const T=PACK.t;
function tf(s,o){return String(s).replace(/\{(\w+)\}/g,(m,k)=>o&&o[k]!==undefined?o[k]:m)}
function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
const LSK=k=>PACK.store.prefix+k;
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
const OWN_PREFIX={resumo:'r',revisao:'ch',silabo:'t',plano:'d'}[PACK.page];
const ANCHOR_URL={r:PACK.urls.resumo,ch:PACK.urls.revisao,t:PACK.urls.silabo};
/* links between pack pages always open in the same tab (no blank target) */
function anchorHref(id){const m=/^(r|ch|t)(\d+)/.exec(id);if(!m)return '#'+id;return m[1]===OWN_PREFIX?'#'+id:((ANCHOR_URL[m[1]]||'')+'#'+id)}
/* tiny markdown for notes and chat: paragraphs, - lists, 1. lists, **bold**, [txt](#anchor); keeps $..$ for KaTeX */
function md(src){
  const blocks=String(src||'').replace(/\r/g,'').split(/\n{2,}/);
  return blocks.map(b=>{
    const lines=b.split('\n');
    const inline=t=>esc(t).replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>').replace(/\[([^\]]+)\]\(#([\w-]+)\)/g,(m,txt,id)=>`<a href="${anchorHref(id)}">${txt}</a>`);
    if(lines.every(l=>/^\s*[-*]\s+/.test(l))) return '<ul>'+lines.map(l=>'<li>'+inline(l.replace(/^\s*[-*]\s+/,''))+'</li>').join('')+'</ul>';
    if(lines.every(l=>/^\s*\d+[.)]\s+/.test(l))) return '<ol>'+lines.map(l=>'<li>'+inline(l.replace(/^\s*\d+[.)]\s+/,''))+'</li>').join('')+'</ol>';
    return '<p>'+lines.map(inline).join('<br>')+'</p>';
  }).join('');
}

/* ===== maths: KaTeX auto-render, then fit wide inline maths ===== */
const KOPTS={delimiters:[{left:"$$",right:"$$",display:true},{left:"\\[",right:"\\]",display:true},{left:"$",right:"$",display:false},{left:"\\(",right:"\\)",display:false}],throwOnError:false,strict:"ignore",ignoredTags:["script","noscript","style","textarea","pre","code","option","input"],ignoredClasses:["nomath"]};
function fitMath(root){
  (root||document).querySelectorAll('.katex').forEach(m=>{
    if(m.closest('.katex-display')||!m.offsetParent) return;
    m.classList.remove('mxw'); m.style.fontSize='';
    let b=m.parentElement; while(b&&getComputedStyle(b).display.startsWith('inline')) b=b.parentElement;
    if(!b) return; const cs=getComputedStyle(b); const avail=b.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight);
    const w=m.getBoundingClientRect().width; if(!avail||w<=avail+1) return;
    const k=Math.max(.62,(avail-8)/w); m.style.fontSize=(k*1.06*100).toFixed(1)+'%';
    if(m.getBoundingClientRect().width>avail+4) m.classList.add('mxw');
  });
}
function typeset(el){
  el=el||document.body;
  try{ if(window.renderMathInElement) renderMathInElement(el,KOPTS); }catch(e){}
  requestAnimationFrame(()=>fitMath(el)); return Promise.resolve();
}
let fmT=null; const fmSoon=()=>{clearTimeout(fmT); fmT=setTimeout(()=>fitMath(),120)};
addEventListener('resize',fmSoon);
document.addEventListener('click',()=>setTimeout(fmSoon,60));
document.addEventListener('toggle',fmSoon,true);
let toastT=null;
function toast(msg){let t=$('#packToast'); if(!t){t=document.createElement('div'); t.id='packToast'; t.className='ptoast'; t.setAttribute('role','status'); document.body.appendChild(t);} t.textContent=msg; t.hidden=false; clearTimeout(toastT); toastT=setTimeout(()=>t.hidden=true,1800);}
/* double-click a formula: copy its LaTeX. Selecting + copying already gives $…$ (copy-tex). */
document.addEventListener('dblclick',ev=>{
  const k=ev.target.closest&&ev.target.closest('.katex'); if(!k) return; const an=k.querySelector('annotation[encoding="application/x-tex"]'); if(!an) return;
  const disp=!!k.closest('.katex-display'); const tex=(disp?'$$':'$')+an.textContent.trim()+(disp?'$$':'$');
  const fallback=()=>{const ta=document.createElement('textarea'); ta.value=tex; ta.style.cssText='position:fixed;left:-9999px'; document.body.appendChild(ta); ta.select(); let ok=false; try{ok=document.execCommand('copy')}catch(e){} ta.remove(); toast(ok?T.copied:T.copyHint)};
  try{navigator.clipboard.writeText(tex).then(()=>toast(T.copied),fallback)}catch(e){fallback()}
});

/* readable text of a block for Claude: every rendered formula goes back to its LaTeX ($…$).
   Never send textContent of a block that holds maths. */
function readable(el,skip){
  if(!el) return '';
  let out='';
  (function walk(n){
    if(n.nodeType===3){ out+=n.nodeValue; return; }
    if(n.nodeType!==1) return;
    if(skip&&n.matches&&n.matches(skip)) return;
    if(n.hidden&&!n.matches('.key')) return;
    if(n.classList&&n.classList.contains('katex')){
      const an=n.querySelector('annotation[encoding="application/x-tex"]'); const disp=!!n.closest('.katex-display');
      if(an){ out+=disp?' $$'+an.textContent.trim()+'$$ ':'$'+an.textContent.trim()+'$'; return; }
      const lab=n.getAttribute('aria-label'); if(lab){out+=' '+lab+' '; return;}
    }
    if(/^(P|DIV|LI|H\d|BR|SECTION|ARTICLE|OL|UL|DETAILS|SUMMARY)$/.test(n.tagName)) out+='\n';
    for(const ch of n.childNodes) walk(ch);
  })(el);
  return out.replace(/[ \t]+/g,' ').replace(/\n\s*\n+/g,'\n').trim();
}
const fmtD=t=>new Date(t).toLocaleDateString(T.locale,{day:'numeric',month:'short'});

/* ===== light / dark (shared by the four pages) ===== */
(function(){const t=lsGet(LSK('theme')); if(t) document.documentElement.dataset.theme=t;})();
function toggleTheme(){
  const root=document.documentElement;
  const dark=root.dataset.theme? root.dataset.theme==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  root.dataset.theme=dark?'light':'dark'; lsSet(LSK('theme'),root.dataset.theme);
  window.dispatchEvent(new Event('themechange'));
}
document.addEventListener('click',e=>{ if(e.target.closest('#themeBtn')) toggleTheme(); });

/* ===== countdown in calendar days (exam date − today), never ceil on milliseconds ===== */
function calDays(){
  if(!PACK.exam||!PACK.exam.date) return null;
  const [y,m,d]=PACK.exam.date.split('-').map(Number); const n=new Date();
  return Math.round((Date.UTC(y,m-1,d)-Date.UTC(n.getFullYear(),n.getMonth(),n.getDate()))/86400000);
}
function countdown(){
  const n=$('#cdN'); if(!n) return; const d=calDays(); if(d===null) return;
  const ex=PACK.exam.label;
  n.textContent=Math.max(0,d);
  $('#cdL').textContent= d<0?tf(T.examPast,{exam:ex}):d===0?tf(T.examToday,{exam:ex}):tf(d===1?T.dayTo:T.daysTo,{exam:ex});
}

/* ===== go to the #anchor of the URL once maths is rendered ===== */
function goHash(){
  const id=(location.hash||'').slice(1); if(!id) return;
  const el=document.getElementById(id); if(!el) return;
  el.scrollIntoView({block:'start'}); el.classList.add('flash'); setTimeout(()=>el.classList.remove('flash'),1600);
}

/* ===== storage: account db when granted, browser otherwise. Keys never change between versions. ===== */
const Store=(function(){
  let ready=null;
  function init(){
    if(ready) return ready;
    ready=(async()=>{
      if(!window.claude||!claude.use) return null;
      try{ const [db,user]=await Promise.all([claude.use('db'),claude.use('user')]); if(!db||!user) return null; const uid=await user.id(); if(!uid) return null; return {db,uid}; }catch(e){return null}
    })();
    return ready;
  }
  const docPath=(uid,name)=>'data/users/'+uid+'/'+((PACK.store.docs||{})[name]||(PACK.store.prefix+name));
  const lsName=name=>((PACK.store.ls||{})[name])||LSK(name);
  async function load(name){
    let local=null; try{const r=lsGet(lsName(name)); if(r) local=JSON.parse(r)}catch(e){}
    const s=await init(); if(!s) return {data:local,remote:false};
    try{const snap=await s.db.doc(docPath(s.uid,name)).get(); return {data:snap.exists?snap.data():local,remote:true}}catch(e){return {data:local,remote:false}}
  }
  const timers={};
  function save(name,data,ms=700){
    lsSet(lsName(name),JSON.stringify(data)); clearTimeout(timers[name]);
    timers[name]=setTimeout(async()=>{const s=await init(); if(!s) return false; try{await s.db.doc(docPath(s.uid,name)).set(data); document.dispatchEvent(new CustomEvent('stored',{detail:{name,remote:true}}));}catch(e){}},ms);
  }
  return {init,load,save,docPath,lsName};
})();

/* ===== current topic ===== */
let CUR_TOPIC=null;
function trackTopics(){
  const secs=$$('[data-topic-sec]'); if(!secs.length) return;
  const vis=new Map();
  const io=new IntersectionObserver(es=>{
    es.forEach(e=>vis.set(e.target,e.isIntersecting?e.intersectionRect.height:0));
    let best=null,bh=0; vis.forEach((h,el)=>{if(h>bh){bh=h;best=el}});
    if(best){CUR_TOPIC=+best.dataset.n; document.dispatchEvent(new CustomEvent('topicchange',{detail:CUR_TOPIC}));}
  },{threshold:[0,.1,.25,.5,.75,1]});
  secs.forEach(s=>io.observe(s)); CUR_TOPIC=+secs[0].dataset.n;
  document.addEventListener('topicchange',e=>$$('.side a').forEach(a=>a.classList.toggle('cur',+a.dataset.n===e.detail)));
}

/* ===== topic rail on phones ===== */
function initSide(){
  const btn=$('#sideBtn'); if(!btn) return;
  const close=()=>{$('.side').classList.remove('open'); if(!$$('.drawer').some(d=>!d.hidden)) $('#scrim').hidden=true;};
  btn.addEventListener('click',()=>{$('.side').classList.add('open'); $('#scrim').hidden=false;});
  $('#scrim').addEventListener('click',close); $$('.side a').forEach(a=>a.addEventListener('click',close));
  document.addEventListener('keydown',e=>{if(e.key==='Escape') close();});
  window.closeSide=close;
}

/* ===== focus mode: the block on the reading line (40% of the screen) stays sharp, the rest dims.
   Block by block, never a whole section. A clicked or focused block comes to the front. ===== */
const Focus=(function(){
  let blocks=[], tick=false, pinned=null, pinT=null;
  function update(){
    tick=false; if(!document.body.classList.contains('focus-mode')) return;
    let best=pinned;
    if(!best){ const mid=innerHeight*0.4; let bd=1e9;
      for(const b of blocks){ if(!b.offsetParent) continue; const r=b.getBoundingClientRect(); if(!r.height) continue;
        const d=(r.top<=mid&&r.bottom>=mid)?0:Math.min(Math.abs(r.top-mid),Math.abs(r.bottom-mid)); if(d<bd){bd=d;best=b;} } }
    blocks.forEach(b=>b.classList.toggle('is-focus',b===best));
  }
  function pin(b){ pinned=b; update(); clearTimeout(pinT); pinT=setTimeout(()=>{pinned=null;},1500); }
  function init(){
    blocks=$$('.fblk'); const btn=$('#focusBtn'); if(!btn) return;
    const set=on=>{document.body.classList.toggle('focus-mode',on); btn.setAttribute('aria-pressed',String(on)); lsSet(LSK('focus'),on?'1':''); update();};
    btn.addEventListener('click',()=>set(!document.body.classList.contains('focus-mode')));
    if(lsGet(LSK('focus'))) set(true);
    addEventListener('scroll',()=>{ if(pinned) return; if(!tick){tick=true; requestAnimationFrame(update);} },{passive:true});
    const grab=e=>{ if(!document.body.classList.contains('focus-mode')) return; const b=e.target.closest('.fblk'); if(b) pin(b); };
    document.addEventListener('pointerdown',grab); document.addEventListener('focusin',grab);
    document.addEventListener('toggle',()=>update(),true);
  }
  return {init,update};
})();

/* ===== notes (hidden until the icon is clicked) ===== */
const NOTE_ICON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h10l4 4v14H5z"/><path d="M15 3v4h4"/><path d="M8.5 12h7M8.5 16h5"/></svg>';
const Notes=(function(){
  const N=T.notesUI; const DOC='notes-'+PACK.page;
  let data={items:{}}, remote=false;
  const hosts=()=>$$('[data-note]');
  function list(key){return data.items[key]||[]}
  function persist(){Store.save(DOC,data); refreshIcons(); renderPanel();}
  function add(key,note){(data.items[key]=data.items[key]||[]).push({id:Date.now().toString(36)+Math.random().toString(36).slice(2,6),date:Date.now(),kind:'mine',...note}); persist(); if($(`.notebox[data-for="${CSS.escape(key)}"]`)) renderBox(key);}
  function update(key,id,text){const n=list(key).find(x=>x.id===id); if(n){n.text=text;n.date=Date.now()} persist();}
  function del(key,id){data.items[key]=list(key).filter(x=>x.id!==id); if(!data.items[key].length) delete data.items[key]; persist();}
  function meta(el){return {topic:+(el.dataset.topic||0),label:el.dataset.label||''}}
  function refreshIcons(){
    hosts().forEach(h=>{
      const b=$(`.nbtn[data-k="${CSS.escape(h.dataset.note)}"]`); if(!b) return;
      const ns=list(h.dataset.note); b.classList.toggle('has',ns.length>0); b.classList.toggle('hasq',ns.some(n=>n.kind==='q'));
      let d=$('.ndot',b); if(ns.length){ if(!d){d=document.createElement('span');d.className='ndot';b.appendChild(d)} d.textContent=ns.length; } else if(d) d.remove();
      b.setAttribute('aria-label',ns.length?tf(N.count,{n:ns.length}):N.add);
    });
    $$('[data-notecount]').forEach(el=>{const n=Object.values(data.items).reduce((a,l)=>a+l.length,0); el.textContent=n?` (${n})`:''});
  }
  function noteHTML(n){
    return `<div class="note ${n.kind==='q'?'q':''}" data-id="${n.id}"><div class="nmeta"><span class="nkind">${n.kind==='q'?N.kindQ:N.kindMine}</span><span>${fmtD(n.date)}</span><span class="nacts"><button type="button" class="linkbtn" data-nedit>${N.edit}</button><button type="button" class="linkbtn" data-ndel>${N.del}</button></span></div><div class="nbody">${md(n.text)}</div></div>`;
  }
  function renderBox(key){
    const box=$(`.notebox[data-for="${CSS.escape(key)}"]`); if(!box) return;
    const ns=list(key); const fid='nt-'+key.replace(/[^\w-]/g,'_');
    box.innerHTML=ns.map(noteHTML).join('')+`<div class="neditor" hidden><label class="lbl nomath" for="${fid}">${N.editorLbl}</label><textarea id="${fid}" rows="3"></textarea><div class="ntools"><button type="button" class="btn sm solid" data-nsave>${N.save}</button><button type="button" class="btn sm ghost" data-ncancel>${N.cancel}</button></div></div><div><button type="button" class="btn sm" data-nnew>${N.new}</button></div>`;
    if(!ns.length) openEditor(box,null);
    typeset(box);
  }
  function openEditor(box,id){
    const ed=$('.neditor',box); ed.hidden=false; ed.dataset.edit=id||''; const ta=$('textarea',ed);
    ta.value=id?(list(box.dataset.for).find(n=>n.id===id)||{}).text||'':''; $('[data-nnew]',box).parentElement.hidden=true; ta.focus();
  }
  function toggle(btn){
    const key=btn.dataset.k; const host=$(`[data-note="${CSS.escape(key)}"]`);
    const open=btn.getAttribute('aria-expanded')==='true';
    let box=$(`.notebox[data-for="${CSS.escape(key)}"]`);
    if(open){box&&box.remove(); btn.setAttribute('aria-expanded','false'); return;}
    box=document.createElement('div'); box.className='notebox'; box.dataset.for=key;
    const slot=[...host.querySelectorAll('.nslot')].find(x=>x.closest('[data-note]')===host)||host; slot.appendChild(box);
    btn.setAttribute('aria-expanded','true'); renderBox(key);
  }
  document.addEventListener('click',e=>{
    const b=e.target.closest('.nbtn[data-k]'); if(b){toggle(b);return;}
    const box=e.target.closest('.notebox'); if(!box) return; const key=box.dataset.for;
    if(e.target.closest('[data-nnew]')) openEditor(box,null);
    else if(e.target.closest('[data-ncancel]')){ if(!list(key).length){const btn=$(`.nbtn[data-k="${CSS.escape(key)}"]`); btn&&toggle(btn);} else renderBox(key); }
    else if(e.target.closest('[data-nsave]')){
      const ed=$('.neditor',box), t=$('textarea',ed).value.trim(); const host=$(`[data-note="${CSS.escape(key)}"]`);
      if(t){ if(ed.dataset.edit) update(key,ed.dataset.edit,t); else add(key,{text:t,...meta(host)}); }
      renderBox(key);
    }
    else if(e.target.closest('[data-nedit]')) openEditor(box,e.target.closest('.note').dataset.id);
    else if(e.target.closest('[data-ndel]')){ del(key,e.target.closest('.note').dataset.id); renderBox(key); }
  });
  function attach(){
    hosts().forEach(h=>{
      const key=h.dataset.note; if($(`.nbtn[data-k="${CSS.escape(key)}"]`)) return;
      const b=document.createElement('button'); b.type='button'; b.className='nbtn'; b.dataset.k=key; b.setAttribute('aria-expanded','false'); b.setAttribute('aria-label',N.add); b.innerHTML=NOTE_ICON;
      const at=[...h.querySelectorAll('.nicon')].find(x=>x.closest('[data-note]')===h)||h; at.appendChild(b);
    });
    refreshIcons();
  }
  let filter='all';
  function renderPanel(){
    const ul=$('#notesList'); if(!ul) return; const rows=[];
    Object.entries(data.items).forEach(([key,ns])=>ns.forEach(n=>{ if(filter==='mine'&&n.kind==='q')return; if(filter==='q'&&n.kind!=='q')return; rows.push({key,...n}); }));
    rows.sort((a,b)=>(a.topic-b.topic)||(a.date-b.date));
    if(!rows.length){ul.innerHTML=`<li class="empty-note">${filter==='q'?N.emptyQ:N.empty}</li>`;return;}
    let last=null,h='';
    rows.forEach(r=>{ if(r.topic!==last){last=r.topic; h+=`<li class="grp">${r.topic?r.topic+' · '+esc(PACK.topics[r.topic]||''):N.general}</li>`;}
      h+=`<li class="item"><div class="il"><span class="nkind" style="color:${r.kind==='q'?'var(--accent2)':'var(--accent)'}">${r.kind==='q'?N.kindQ:N.noteWord}</span><span>${esc(r.label)}</span><span>${fmtD(r.date)}</span><a href="#${esc(r.key)}" data-jump="${esc(r.key)}" style="margin-left:auto">${N.go}</a></div><div class="nbody">${md(r.text)}</div></li>`; });
    ul.innerHTML=h; typeset(ul);
  }
  function openPanel(){$('#notesDrawer').hidden=false; $('#notesScrim').hidden=false; renderPanel(); $('#notesClose').focus();}
  function closePanel(){$('#notesDrawer').hidden=true; $('#notesScrim').hidden=true;}
  document.addEventListener('click',e=>{
    if(e.target.closest('#notesBtn')) openPanel();
    else if(e.target.closest('#notesClose')||e.target.closest('#notesScrim')) closePanel();
    else if(e.target.closest('[data-nf]')){filter=e.target.closest('[data-nf]').dataset.nf; $$('[data-nf]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.nf===filter))); renderPanel();}
    else if(e.target.closest('[data-jump]')){e.preventDefault(); const k=e.target.closest('[data-jump]').dataset.jump; closePanel(); const el=$(`[data-note="${CSS.escape(k)}"]`); if(el){el.scrollIntoView({block:'center'}); const b=$(`.nbtn[data-k="${CSS.escape(k)}"]`); if(b&&b.getAttribute('aria-expanded')!=='true') toggle(b);} }
  });
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&$('#notesDrawer')&&!$('#notesDrawer').hidden) closePanel(); });
  async function init(){
    if(!hosts().length) return; attach();
    const r=await Store.load(DOC); remote=r.remote; if(r.data&&r.data.items) data=r.data;
    refreshIcons(); renderPanel();
    const w=$('#notesWhere'); if(w) w.textContent=remote?N.whereAccount:N.whereLocal;
  }
  return {init,add,list,attach,refreshIcons,all:()=>data.items};
})();

/* ===== tutor chat ===== */
const Tutor=(function(){
  const U=T.tutor;
  let sample=null, conv=[], ctx=null, busy=null, sinceSave=0, offered=false;
  const CONF=new RegExp(U.conf,'i');
  const SKIP='.notebox,.nbtn,.nicon,button,textarea,input,label,.key[hidden],.verdict,.fb[hidden],.photo,.err,.xact,.gate,.sol:not([open])>*:not(summary)';
  const topicKey=n=>({resumo:'r',revisao:'ch',silabo:'t'}[PACK.page])+n;
  const topicOf=()=>ctx&&ctx.topic||CUR_TOPIC||1;
  function topicText(n){ return readable(document.getElementById(topicKey(n)),SKIP).slice(0,9000); }
  function blockAtCenter(){
    const cand=$$('[data-note]').filter(el=>!el.hasAttribute('data-topic-sec'));
    const mid=innerHeight*0.4; let best=null,bd=1e9;
    for(const el of cand){const r=el.getBoundingClientRect(); if(!r.height) continue; const d=(r.top<=mid&&r.bottom>=mid)?0:Math.min(Math.abs(r.top-mid),Math.abs(r.bottom-mid)); if(d<bd||(d===bd&&best&&best.contains(el))){bd=d;best=el;}}
    return bd<innerHeight*0.5?best:null;
  }
  function ctxFrom(host,kind){
    if(!host) return null;
    const body=host.querySelector('.q,.xstmt')||host;
    return {kind:kind||(host.classList.contains('ex')?'ex':host.classList.contains('xmp')?'example':'blk'),key:host.dataset.note,topic:+host.dataset.topic||CUR_TOPIC||1,label:host.dataset.label,text:readable(body,SKIP).slice(0,3000),
      attempted:!!(host.classList.contains('is-ok')||host.classList.contains('is-miss')||((host.querySelector('textarea[id^="ta-"]')||{}).value||'').trim())};
  }
  function instr(){
    const n=topicOf();
    let s=tf(U.sys,{course:PACK.course,title:PACK.title,langName:T.langName,topics:Object.entries(PACK.topics).map(([k,v])=>k+' '+v).join('; '),n,name:PACK.topics[n],text:topicText(n)});
    if(ctx&&ctx.text){ s+=tf(U.ctx,{label:ctx.label,text:ctx.text}); if(ctx.kind==='ex'&&!ctx.attempted) s+=U.noSpoil; }
    return s;
  }
  function bubble(role,content){const d=document.createElement('div'); d.className='msg '+(role==='user'?'u':'a'); d.innerHTML=md(content); $('#msgs').appendChild(d); $('#msgs').scrollTop=1e9; return d;}
  function updateHead(){
    const n=topicOf(); $('#chatTopic').textContent=tf(U.topicLbl,{n,name:PACK.topics[n]});
    const c=$('#ctxChip'); if(ctx&&ctx.label){c.hidden=false; $('#ctxLbl').textContent=U.about+ctx.label;} else c.hidden=true;
  }
  function greet(){
    const n=topicOf(); const what=ctx&&ctx.label?'<b>'+esc(ctx.label)+'</b>':'<b>'+esc(n+' · '+PACK.topics[n])+'</b>';
    $('#msgs').innerHTML=`<div class="msg a" data-greet><p>${tf(U.greet,{what})}</p></div>`; updateHead();
  }
  function saveBtn(i){const w=document.createElement('div'); w.className='mact'; w.innerHTML=`<button type="button" class="btn sm ghost" data-savenote="${i}">${U.saveNote}</button>`; return w;}
  function open(c){
    const wasOpen=!$('#chat').hidden; const nc=c||ctxFrom(blockAtCenter());
    if(!wasOpen||c){ if(!wasOpen){conv=[];sinceSave=0;offered=false;} ctx=nc; }
    $('#chat').hidden=false; $('#chatFab').hidden=true;
    if(!conv.length) greet(); else updateHead(); $('#chatIn').focus();
  }
  function close(){
    $('#chat').hidden=true; $('#chatFab').hidden=false; if(busy){busy.ctl.abort(); busy=null;}
    conv=[]; ctx=null; sinceSave=0; offered=false; $('#msgs').innerHTML=''; $('#chatSend').disabled=false;
  }
  function buildMsgs(){
    let c=conv.slice(-12).filter(m=>m&&m.content); while(c.length&&c[0].role!=='user') c.shift();
    const merged=[]; c.forEach(m=>{const l=merged[merged.length-1]; if(l&&l.role===m.role) l.content+='\n\n'+m.content; else merged.push({role:m.role,content:m.content});});
    if(!merged.length||merged[merged.length-1].role!=='user') merged.push({role:'user',content:(conv[conv.length-1]||{}).content||''});
    merged[0]={role:'user',content:instr()+'\n\n--- '+U.q+' ---\n'+merged[0].content}; return merged;
  }
  async function send(text){
    text=(text||'').trim(); if(!text) return;
    if(busy){ const b=busy; busy=null; b.ctl.abort(); if(b.streamed){conv.push({role:'assistant',content:b.streamed}); b.out.appendChild(saveBtn(conv.length-1));} else b.out.remove(); }
    $('[data-greet]',$('#msgs'))?.remove();
    conv.push({role:'user',content:text}); typeset(bubble('user',text));
    const out=bubble('assistant',T.thinking); const job={ctl:new AbortController(),out,streamed:''}; busy=job;
    const timer=setTimeout(()=>job.ctl.abort(),120000);
    const opts={signal:job.ctl.signal,cache:false,onText:({text})=>{ if(busy!==job) return; job.streamed=text; out.innerHTML=md(text); $('#msgs').scrollTop=1e9; }};
    const msgs=buildMsgs();
    try{
      let r;
      try{ r=await sample(msgs,opts); }
      catch(e1){ if(busy!==job||(e1&&['rate_limited','not_granted','cancelled','sampling_disabled'].includes(e1.code))) throw e1;
        r=await sample(msgs.map(m=>(m.role==='user'?U.student+': ':U.tutorW+': ')+m.content).join('\n\n')+'\n\n'+U.tutorW+':',opts); }
      if(busy!==job) return;
      const t=(r&&r.text)||job.streamed||'';
      conv.push({role:'assistant',content:t}); out.innerHTML=md(t); out.appendChild(saveBtn(conv.length-1)); typeset(out);
      sinceSave++; if(!offered&&(CONF.test(text)||sinceSave>=2)) offer(conv.length-1);
    }catch(e){
      if(busy!==job) return;
      if(job.streamed){ conv.push({role:'assistant',content:job.streamed}); out.appendChild(saveBtn(conv.length-1)); typeset(out); }
      else{ const m=e&&e.code==='rate_limited'?U.errRate:e&&e.code==='not_granted'?U.errPerm:e&&e.code==='cancelled'?U.errTime:U.errOther;
        out.innerHTML=`<p>${m}</p>${e&&(e.code||e.message)?`<p class="hint">${U.detail}${esc((String(e.code||'')+' '+String(e.message||'')).slice(0,160))}</p>`:''}`; conv.pop(); }
    }finally{ clearTimeout(timer); if(busy===job) busy=null; }
  }
  function offer(i){
    offered=true; const d=document.createElement('div'); d.className='offer';
    d.innerHTML=`<span>${tf(U.offer,{where:ctx&&ctx.label?' — <b>'+esc(ctx.label)+'</b> —':''})}</span><div class="ntools"><button type="button" class="btn sm solid" data-savenote="${i}">${U.offerYes}</button><button type="button" class="btn sm ghost" data-nooffer>${U.offerNo}</button></div>`;
    $('#msgs').appendChild(d); $('#msgs').scrollTop=1e9;
  }
  async function saveNote(i,btn){
    if(!conv[i]) return; const n=topicOf();
    btn.disabled=true; btn.textContent=U.writing;
    const talk=conv.slice(Math.max(0,i-5),i+1).map(m=>(m.role==='user'?U.student+': ':U.tutorW+': ')+m.content).join('\n\n');
    let note; try{ note=await sample.json(tf(U.notePrompt,{course:PACK.course,langName:T.langName,talk}),{modelTier:'quick'}); }
    catch(e){ note={unclear:(conv[i-1]||{}).content||U.doubt,explanation:conv[i].content}; }
    const targetKey=(ctx&&ctx.key)||topicKey(n); const host=$(`[data-note="${CSS.escape(targetKey)}"]`);
    Notes.add(targetKey,{kind:'q',topic:n,label:(host&&host.dataset.label)||(ctx&&ctx.label)||(T.topic+' '+n),text:`**${U.unclearLbl}** ${note.unclear||''}\n\n${note.explanation||''}`});
    btn.textContent=U.saved; sinceSave=0; offered=false;
  }
  document.addEventListener('click',e=>{
    const a=e.target.closest('[data-ask]');
    if(a){ open(ctxFrom(a.closest('[data-note]'),a.dataset.ask==='blk'?null:a.dataset.ask)); return; }
    if(e.target.closest('#chatFab')) open(null);
    else if(e.target.closest('#chatClose')) close();
    else if(e.target.closest('#ctxClear')){ctx=null; updateHead();}
    else if(e.target.closest('[data-savenote]')){const b=e.target.closest('[data-savenote]'); saveNote(+b.dataset.savenote,b);}
    else if(e.target.closest('[data-nooffer]')) e.target.closest('.offer').remove();
  });
  async function init(){
    if(!$('#chat')) return;
    document.addEventListener('topicchange',()=>{ if(!$('#chat').hidden&&!ctx) updateHead(); });
    $('#chatForm').addEventListener('submit',e=>{e.preventDefault(); const t=$('#chatIn'); const v=t.value; if(!v.trim()) return; if(!sample){t.placeholder=U.loading; return;} t.value=''; send(v);});
    $('#chatIn').addEventListener('keydown',e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault(); $('#chatForm').requestSubmit();} });
    document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&!$('#chat').hidden) close(); });
    if(!window.claude||!claude.use){ const o=$('#chatOff'); if(o) o.hidden=false; return; }
    try{ sample=await claude.use('sample'); }catch(e){ sample=null; }
    if(!sample){ const o=$('#chatOff'); if(o) o.hidden=false; return; }
    $('#chatFab').hidden=false; $$('[data-ask]').forEach(b=>b.hidden=false);
  }
  return {init,open,get sample(){return sample}};
})();

/* ===== graph calculator (Desmos-like: math.js + canvas), floating window ===== */
const GC=(function(){
  const G=T.gc; const KEY=LSK('gc');
  const COLORS=['--accent','--accent2','--bad','--warn','--ok','--ink'];
  let st={x:null,y:null,w:400,h:360,min:false,open:false,deg:false,rows:[{s:'f(x)=x^2-2',c:0},{s:'y=a*sin(x)',c:1},{s:'a=1',c:2,min:-5,max:5}],view:{cx:0,cy:0,sc:40}};
  try{const r=lsGet(KEY); if(r) st={...st,...JSON.parse(r)}}catch(e){}
  let el=null,cv=null,ctx=null,dpr=1,compiled=[],marks=[],trace=null,raf=0;
  const save=()=>{ if(!el) return; lsSet(KEY,JSON.stringify({...st,rows:st.rows.map(r=>({s:r.s,c:r.c,hidden:r.hidden,min:r.min,max:r.max}))})); };
  const tok=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim()||'#888';
  const col=i=>tok(COLORS[i%COLORS.length]);
  const RESERVED=new Set(['x','y','t','e','pi','i','E','PI','Infinity','true','false']);
  function baseScope(){
    const k=st.deg?Math.PI/180:1, ik=st.deg?180/Math.PI:1;
    return {sin:x=>Math.sin(x*k),cos:x=>Math.cos(x*k),tan:x=>Math.tan(x*k),sen:x=>Math.sin(x*k),tg:x=>Math.tan(x*k),cotg:x=>1/Math.tan(x*k),cot:x=>1/Math.tan(x*k),sec:x=>1/Math.cos(x*k),
      asin:x=>Math.asin(x)*ik,acos:x=>Math.acos(x)*ik,atan:x=>Math.atan(x)*ik,arcsin:x=>Math.asin(x)*ik,arcsen:x=>Math.asin(x)*ik,arccos:x=>Math.acos(x)*ik,arctan:x=>Math.atan(x)*ik,arctg:x=>Math.atan(x)*ik,
      sh:Math.sinh,ch:Math.cosh,th:Math.tanh,sinh:Math.sinh,cosh:Math.cosh,tanh:Math.tanh,ln:Math.log,log:(x,b)=>b===undefined?Math.log(x):Math.log(x)/Math.log(b),sqrt:Math.sqrt,abs:Math.abs,exp:Math.exp};
  }
  const num=v=>typeof v==='number'?v:(v&&typeof v.re==='number'&&Math.abs(v.im)<1e-12?v.re:NaN);
  const fmt=v=>{ if(!isFinite(v)) return String(v); const a=Math.abs(v); if(a!==0&&(a<1e-4||a>=1e7)) return v.toExponential(4); return String(+v.toPrecision(8)); };
  function splitTop(s){let d=0,cur='',out=[];for(const ch of s){if('([{'.includes(ch))d++;if(')]}'.includes(ch))d--; if(ch===','&&d===0){out.push(cur);cur='';}else cur+=ch;} out.push(cur); return out.map(x=>x.trim());}
  function compile(){
    const scope=baseScope(); const out=[]; const used=new Set(); const defined=new Set(Object.keys(scope));
    st.rows.forEach((r,i)=>{
      const s=(r.s||'').trim(); const o={i,row:r,kind:'empty',s}; out[i]=o; if(!s) return;
      try{
        const m=/^([a-zA-Z_]\w*)\s*=\s*([^=<>].*)$/.exec(s);
        if(m&&!RESERVED.has(m[1])){ const node=math.parse(m[2]); const syms=node.filter(n=>n.isSymbolNode).map(n=>n.name);
          if(!syms.some(v=>v==='x'||v==='t')&&syms.every(v=>defined.has(v)||math[v]!==undefined||v==='pi'||v==='e')){ o.kind='var'; o.name=m[1]; o.node=node; defined.add(m[1]); return; } }
        const fd=/^([a-zA-Z_]\w*)\s*\(\s*([a-z](?:\s*,\s*[a-z])*)\s*\)\s*=\s*(.+)$/.exec(s);
        if(fd){ o.kind='fdef'; o.name=fd[1]; o.args=fd[2].split(',').map(a=>a.trim()); o.node=math.parse(fd[3]); defined.add(fd[1]); }
      }catch(e){o.kind='err';o.err=e.message}
    });
    out.forEach(o=>{
      if(o.kind==='var'){ try{const v=o.node.evaluate(scope); if(typeof v==='number'){scope[o.name]=v; o.value=v;} else {o.kind='err';o.err=G.notNum}}catch(e){o.kind='err';o.err=e.message} }
      else if(o.kind==='fdef'){ const code=o.node.compile(); const args=o.args; scope[o.name]=(...a)=>{const sc=Object.create(scope); args.forEach((n,j)=>sc[n]=a[j]); return code.evaluate(sc);}; }
    });
    function collect(node){ node.filter(n=>n.isSymbolNode).forEach(n=>{ const v=n.name; if(!RESERVED.has(v)&&!(v in scope)&&math[v]===undefined) used.add(v); }); }
    out.forEach(o=>{
      if(o.kind!=='empty'){ if(o.kind==='fdef'&&o.args.length===1&&o.args[0]==='x'){ o.plot='fx'; o.f=x=>num(scope[o.name](x)); } return; }
      const s=o.s; if(!s) return;
      try{ let m;
        if((m=/^y\s*(<=|>=|<|>|=)\s*(.+)$/.exec(s))){ const c=math.parse(m[2]); collect(c); const code=c.compile(); o.kind='plot'; o.plot=m[1]==='='?'fx':'ineq'; o.op=m[1]; o.f=x=>num(code.evaluate(Object.assign(Object.create(scope),{x}))); }
        else if((m=/^x\s*=\s*(.+)$/.exec(s))){ const c=math.parse(m[1]); collect(c); o.kind='plot'; o.plot='vline'; o.v=+c.evaluate(scope); }
        else if(/^\(.*,.*\)$/.test(s)){ const parts=splitTop(s.slice(1,-1)); if(parts.length!==2) throw new Error(G.point);
          const a=math.parse(parts[0]),b=math.parse(parts[1]); collect(a);collect(b);
          const hasT=[a,b].some(n=>n.filter(q=>q.isSymbolNode&&q.name==='t').length);
          if(hasT){const ca=a.compile(),cb=b.compile(); o.kind='plot'; o.plot='param'; o.fx=t=>num(ca.evaluate(Object.assign(Object.create(scope),{t}))); o.fy=t=>num(cb.evaluate(Object.assign(Object.create(scope),{t})));}
          else {o.kind='plot'; o.plot='point'; o.px=+a.evaluate(scope); o.py=+b.evaluate(scope); o.res=`(${fmt(o.px)}, ${fmt(o.py)})`;}
        }
        else { const c=math.parse(s); collect(c); const syms=c.filter(n=>n.isSymbolNode).map(n=>n.name);
          if(syms.includes('x')){const code=c.compile(); o.kind='plot'; o.plot='fx'; o.f=x=>num(code.evaluate(Object.assign(Object.create(scope),{x})));}
          else { const v=c.evaluate(scope); o.kind='num'; o.res=typeof v==='number'?fmt(v):(v&&v.toString?v.toString():String(v)); } }
      }catch(e){o.kind='err';o.err=String(e.message||e).slice(0,60)}
    });
    const add=[...used].filter(v=>/^[a-zA-Z]$/.test(v)&&!out.some(o=>o.kind==='var'&&o.name===v));
    if(add.length){ add.forEach(v=>st.rows.push({s:v+'=1',c:st.rows.length%COLORS.length,min:-5,max:5})); return compile(); }
    compiled=out; return out;
  }
  function build(){
    el=document.createElement('section'); el.className='gc'; el.setAttribute('aria-label',G.title);
    el.innerHTML=`<div class="gcbar"><b>${G.title}</b><button type="button" class="gcib" data-gc="min" aria-label="${G.min}">–</button><button type="button" class="gcib" data-gc="close" aria-label="${G.close}">×</button></div>
    <div class="gcbody"><div class="gctools"><button type="button" class="gcib" data-gc="add">${G.add}</button><button type="button" class="gcib" data-gc="deg" aria-pressed="${st.deg}">${st.deg?G.deg:G.rad}</button><button type="button" class="gcib" data-gc="reset">${G.reset}</button><button type="button" class="gcib" data-gc="clearm">${G.clear}</button></div>
    <div class="gcex" id="gcex"></div><div class="gccv"><canvas id="gccv"></canvas></div></div><div class="gcrs" aria-hidden="true"></div>`;
    document.body.appendChild(el); cv=$('#gccv',el); ctx=cv.getContext('2d');
    place(); renderRows(); bindWin(); bindCanvas();
    new ResizeObserver(()=>draw()).observe($('.gccv',el));
    window.addEventListener('themechange',()=>{renderRows();});
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>renderRows());
  }
  function place(){
    const W=innerWidth,H=innerHeight; st.w=Math.min(st.w,W-16); st.h=Math.min(st.h,H-80);
    if(st.x==null){st.x=Math.max(8,W-st.w-24); st.y=Math.max(70,H-st.h-90);}
    st.x=Math.min(Math.max(0,st.x),W-120); st.y=Math.min(Math.max(0,st.y),H-44);
    Object.assign(el.style,{left:st.x+'px',top:st.y+'px',width:st.w+'px',height:st.h+'px'});
    el.classList.toggle('min',!!st.min); $('[data-gc="min"]',el).textContent=st.min?'▢':'–';
  }
  function renderRows(){
    if(!el) return; const box=$('#gcex',el); box.innerHTML='';
    st.rows.forEach((r,i)=>{
      const row=document.createElement('div'); row.className='gcrow'; row.dataset.i=i; const c=col(r.c);
      row.innerHTML=`<button type="button" class="gcdot" style="border-color:${c};background:${r.hidden?'transparent':c}" aria-label="${G.toggle}"></button><input type="text" id="gce-${i}" value="${esc(r.s)}" spellcheck="false" autocomplete="off" aria-label="${tf(G.expr,{n:i+1})}"><span class="gcres"></span><button type="button" class="gcx" aria-label="${G.del}">×</button><div class="gctex"></div>`;
      box.appendChild(row);
    });
    refresh();
  }
  let texT=0;
  function refresh(){
    compile();
    $$('.gcrow',el).forEach(row=>{
      const i=+row.dataset.i, o=compiled[i]||{}, res=$('.gcres',row);
      res.classList.toggle('err',o.kind==='err'); res.textContent=o.kind==='err'?G.err:(o.kind==='var'?'':(o.res||'')); res.title=o.err||'';
      let sl=$('.gcslider',row);
      if(o.kind==='var'&&/^[\w]+\s*=\s*-?[\d.]+\s*$/.test(o.s)){
        const r=st.rows[i]; r.min??=-5; r.max??=5;
        if(!sl){sl=document.createElement('div'); sl.className='gcslider'; row.appendChild(sl);
          sl.innerHTML=`<input type="number" id="gcmin-${i}" value="${r.min}" aria-label="${G.lo}"><input type="range" id="gcr-${i}" min="${r.min}" max="${r.max}" step="${(r.max-r.min)/200}" value="${o.value}"><input type="number" id="gcmax-${i}" value="${r.max}" aria-label="${G.hi}">`;}
        else { const rg=$('input[type=range]',sl); if(document.activeElement!==rg) rg.value=o.value; }
      } else if(sl) sl.remove();
      if(o.kind==='var'&&!sl) res.textContent='= '+fmt(o.value);
    });
    clearTimeout(texT); texT=setTimeout(()=>{ if(!window.katex) return; $$('.gcrow',el).forEach(row=>{ const s=st.rows[+row.dataset.i].s; const t=$('.gctex',row); let tex='';
      try{ if(s.trim()) tex=s.split(/(<=|>=|=|<|>)/).map(p=>/^(<=|>=|=|<|>)$/.test(p)?({'<=':'\\le ','>=':'\\ge ','<':'\\lt ','>':'\\gt '}[p]||p):math.parse(p).toTex({parenthesis:'auto'})).join(''); }catch(e){tex=''}
      if(t.dataset.tex!==tex){t.dataset.tex=tex; try{ katex.render(tex,t,{throwOnError:false}); }catch(e){ t.textContent=''; } } }); },350);
    save(); draw();
  }
  function bindWin(){
    el.addEventListener('click',e=>{
      const b=e.target.closest('[data-gc]'); const row=e.target.closest('.gcrow');
      if(b){const a=b.dataset.gc;
        if(a==='close') hide(); else if(a==='min'){st.min=!st.min; place(); save(); requestAnimationFrame(draw);}
        else if(a==='add'){st.rows.push({s:'',c:st.rows.length%COLORS.length}); renderRows(); $$('.gcrow input[type=text]',el).pop().focus();}
        else if(a==='deg'){st.deg=!st.deg; b.setAttribute('aria-pressed',st.deg); b.textContent=st.deg?G.deg:G.rad; refresh();}
        else if(a==='reset'){st.view={cx:0,cy:0,sc:40}; save(); draw();}
        else if(a==='clearm'){marks=[]; draw();}
        return;}
      if(row&&e.target.closest('.gcdot')){const r=st.rows[+row.dataset.i]; r.hidden=!r.hidden; renderRows();}
      if(row&&e.target.closest('.gcx')){st.rows.splice(+row.dataset.i,1); renderRows();}
    });
    el.addEventListener('input',e=>{
      const row=e.target.closest('.gcrow'); if(!row) return; const i=+row.dataset.i, r=st.rows[i];
      if(e.target.type==='text'){ r.s=e.target.value; refresh(); }
      else if(e.target.type==='range'){ const name=r.s.split('=')[0].trim(); r.s=name+'='+(+(+e.target.value).toPrecision(4)); $('input[type=text]',row).value=r.s; refresh(); }
      else if(e.target.type==='number'){ const v=+e.target.value; if(!isFinite(v)) return; if(e.target.id.startsWith('gcmin'))r.min=v; else r.max=v; const rg=$('input[type=range]',row); rg.min=r.min; rg.max=r.max; rg.step=(r.max-r.min)/200; save(); }
    });
    el.addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.closest('.gcrow input[type=text]')){ const i=+e.target.closest('.gcrow').dataset.i; if(i===st.rows.length-1){st.rows.push({s:'',c:st.rows.length%COLORS.length}); renderRows(); $$('.gcrow input[type=text]',el).pop().focus();} } });
    const bar=$('.gcbar',el);
    bar.addEventListener('pointerdown',e=>{ if(e.target.closest('button')) return; e.preventDefault(); bar.setPointerCapture(e.pointerId); const ox=e.clientX-st.x, oy=e.clientY-st.y;
      const mv=ev=>{st.x=ev.clientX-ox; st.y=ev.clientY-oy; place();}; const up=()=>{bar.removeEventListener('pointermove',mv); save();};
      bar.addEventListener('pointermove',mv); bar.addEventListener('pointerup',up,{once:true}); bar.addEventListener('pointercancel',up,{once:true}); });
    const rs=$('.gcrs',el);
    rs.addEventListener('pointerdown',e=>{ e.preventDefault(); rs.setPointerCapture(e.pointerId); const sx=e.clientX,sy=e.clientY,w0=st.w,h0=st.h;
      const mv=ev=>{st.w=Math.max(280,w0+ev.clientX-sx); st.h=Math.max(240,h0+ev.clientY-sy); place(); draw();}; const up=()=>{rs.removeEventListener('pointermove',mv); save();};
      rs.addEventListener('pointermove',mv); rs.addEventListener('pointerup',up,{once:true}); rs.addEventListener('pointercancel',up,{once:true}); });
    window.addEventListener('resize',()=>{ if(el&&!el.hidden){place(); draw();} });
  }
  const W=()=>cv.clientWidth, H=()=>cv.clientHeight;
  const sx=x=>W()/2+(x-st.view.cx)*st.view.sc, sy=y=>H()/2-(y-st.view.cy)*st.view.sc;
  const wx=px=>st.view.cx+(px-W()/2)/st.view.sc, wy=py=>st.view.cy-(py-H()/2)/st.view.sc;
  function niceStep(sc){const target=80/sc; const p=Math.pow(10,Math.floor(Math.log10(target))); for(const m of [1,2,5,10]) if(m*p>=target) return m*p; return 10*p;}
  function draw(){ cancelAnimationFrame(raf); raf=requestAnimationFrame(render); }
  function render(){
    if(!el||el.hidden||st.min) return; const w=W(),h=H(); if(!w||!h) return; dpr=window.devicePixelRatio||1;
    if(cv.width!==Math.round(w*dpr)||cv.height!==Math.round(h*dpr)){cv.width=Math.round(w*dpr); cv.height=Math.round(h*dpr);}
    ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,w,h);
    const bg=tok('--surface'),grid=tok('--line'),ink=tok('--ink'),muted=tok('--muted');
    ctx.fillStyle=bg; ctx.fillRect(0,0,w,h);
    const step=niceStep(st.view.sc), x0=wx(0),x1=wx(w),y0=wy(h),y1=wy(0);
    ctx.lineWidth=1; ctx.strokeStyle=grid; ctx.beginPath();
    for(let x=Math.ceil(x0/step)*step;x<=x1;x+=step){const p=Math.round(sx(x))+.5; ctx.moveTo(p,0); ctx.lineTo(p,h);}
    for(let y=Math.ceil(y0/step)*step;y<=y1;y+=step){const p=Math.round(sy(y))+.5; ctx.moveTo(0,p); ctx.lineTo(w,p);}
    ctx.stroke();
    ctx.strokeStyle=muted; ctx.lineWidth=1.3; ctx.beginPath(); const ax=sx(0),ay=sy(0); ctx.moveTo(0,ay); ctx.lineTo(w,ay); ctx.moveTo(ax,0); ctx.lineTo(ax,h); ctx.stroke();
    ctx.fillStyle=muted; ctx.font='11px '+tok('--f-mono'); ctx.textBaseline='top';
    const lab=v=>{const s=+v.toPrecision(6); return Math.abs(s)<1e-10?'0':String(s)};
    const ly=Math.min(Math.max(ay+3,2),h-14), lx=Math.min(Math.max(ax+4,2),w-40);
    for(let x=Math.ceil(x0/step)*step;x<=x1;x+=step){ if(Math.abs(x)<step/2) continue; ctx.textAlign='center'; ctx.fillText(lab(x),sx(x),ly); }
    ctx.textAlign='left'; ctx.textBaseline='middle';
    for(let y=Math.ceil(y0/step)*step;y<=y1;y+=step){ if(Math.abs(y)<step/2) continue; ctx.fillText(lab(y),lx,sy(y)); }
    compiled.forEach(o=>{
      if(o.kind!=='plot'&&o.plot!=='fx') return; if(o.row.hidden) return;
      const c=col(o.row.c); ctx.strokeStyle=c; ctx.fillStyle=c; ctx.lineWidth=2.2;
      if(o.plot==='fx'||o.plot==='ineq'){
        if(o.plot==='ineq'){ ctx.globalAlpha=.16; ctx.beginPath(); const up=o.op[0]==='>';
          for(let px=0;px<=w;px+=2){const y=o.f(wx(px)); const py=isFinite(y)?Math.min(Math.max(sy(y),-10),h+10):(up?h+10:-10); ctx.rect(px,up?0:py,2,up?py:h-py);} ctx.fill(); ctx.globalAlpha=1;
          if(!o.op.includes('=')) ctx.setLineDash([6,5]); }
        ctx.beginPath(); let pen=false, prev=null;
        for(let px=0;px<=w;px+=1){ const y=o.f(wx(px)); if(!isFinite(y)){pen=false;prev=null;continue;} const py=sy(y);
          if(prev!==null&&Math.abs(py-prev)>h*1.5){pen=false;} if(py<-h*4||py>h*5){pen=false; prev=py; continue;}
          if(!pen){ctx.moveTo(px,py);pen=true;} else ctx.lineTo(px,py); prev=py; }
        ctx.stroke(); ctx.setLineDash([]);
      } else if(o.plot==='vline'){ ctx.beginPath(); ctx.moveTo(sx(o.v),0); ctx.lineTo(sx(o.v),h); ctx.stroke(); }
      else if(o.plot==='param'){ ctx.beginPath(); let pen=false; const N=600; for(let k=0;k<=N;k++){const t=-2*Math.PI+4*Math.PI*k/N; const X=o.fx(t),Y=o.fy(t); if(!isFinite(X)||!isFinite(Y)){pen=false;continue;} if(!pen){ctx.moveTo(sx(X),sy(Y));pen=true;} else ctx.lineTo(sx(X),sy(Y));} ctx.stroke(); }
      else if(o.plot==='point'){ ctx.beginPath(); ctx.arc(sx(o.px),sy(o.py),5,0,7); ctx.fill(); }
    });
    const dot=(X,Y,txt,c)=>{ const px=sx(X),py=sy(Y); ctx.fillStyle=bg; ctx.strokeStyle=c; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(px,py,5,0,7); ctx.fill(); ctx.stroke();
      ctx.font='12px '+tok('--f-mono'); const tw=ctx.measureText(txt).width+10; let bx=px+8, by=py-24; if(bx+tw>w) bx=px-tw-8; if(by<0) by=py+8;
      ctx.fillStyle=bg; ctx.globalAlpha=.92; ctx.fillRect(bx,by,tw,18); ctx.globalAlpha=1; ctx.strokeStyle=grid; ctx.lineWidth=1; ctx.strokeRect(bx+.5,by+.5,tw,18); ctx.fillStyle=ink; ctx.textAlign='left'; ctx.textBaseline='middle'; ctx.fillText(txt,bx+5,by+9); };
    marks.forEach(m=>dot(m.x,m.y,`${m.lbl} (${fmt(+m.x.toPrecision(5))}, ${fmt(+m.y.toPrecision(5))})`,m.col));
    if(trace) dot(trace.x,trace.y,`(${fmt(+trace.x.toPrecision(5))}, ${fmt(+trace.y.toPrecision(5))})`,trace.col);
  }
  function fns(){return compiled.filter(o=>!o.row.hidden&&(o.plot==='fx')&&o.f)}
  function nearest(px,py){ let best=null; fns().forEach(o=>{const y=o.f(wx(px)); if(!isFinite(y)) return; const d=Math.abs(sy(y)-py); if(d<14&&(!best||d<best.d)) best={d,o,x:wx(px),y};}); return best; }
  function bisect(g,a,b){let fa=g(a); for(let k=0;k<60;k++){const m=(a+b)/2,fm=g(m); if(!isFinite(fm)) return null; if(Math.sign(fm)===Math.sign(fa)){a=m;fa=fm}else b=m;} return (a+b)/2;}
  function features(px,py){
    const span=24/st.view.sc, x0=wx(px)-span, x1=wx(px)+span, N=240, found=[]; const F=fns();
    const scan=(g,lbl,o,yOf)=>{ let pa=x0,ga=g(pa); for(let k=1;k<=N;k++){const pb=x0+(x1-x0)*k/N, gb=g(pb); if(isFinite(ga)&&isFinite(gb)&&(ga===0||Math.sign(ga)!==Math.sign(gb))){ const r=ga===0?pa:bisect(g,pa,pb); if(r!=null){const y=yOf(r); if(isFinite(y)&&Math.abs(g(r))<1e-6*(1+Math.abs(y))*1e3) found.push({x:r,y,lbl,col:col(o.row.c)});}} pa=pb; ga=gb; } };
    F.forEach(o=>{ scan(o.f,'0',o,()=>0);
      const hh=1e-5*(1+Math.abs(x0)); const d=x=>(o.f(x+hh)-o.f(x-hh))/(2*hh);
      let pa=x0,da=d(pa); for(let k=1;k<=N;k++){const pb=x0+(x1-x0)*k/N, db=d(pb); if(isFinite(da)&&isFinite(db)&&Math.sign(da)!==Math.sign(db)&&Math.abs(da-db)<1e6){const r=bisect(d,pa,pb); if(r!=null){const y=o.f(r); if(isFinite(y)) found.push({x:r,y,lbl:da>0?G.max:G.minPt,col:col(o.row.c)});}} pa=pb; da=db;} });
    for(let a=0;a<F.length;a++)for(let b=a+1;b<F.length;b++){const g=x=>F[a].f(x)-F[b].f(x); scan(g,'∩',F[a],x=>F[a].f(x));}
    let best=null; found.forEach(f=>{const dd=Math.hypot(sx(f.x)-px,sy(f.y)-py); if(dd<30&&(!best||dd<best.dd)) best={...f,dd};}); return best;
  }
  function bindCanvas(){
    const pts=new Map(); let start=null, moved=false, pinch=null;
    cv.addEventListener('pointerdown',e=>{ cv.setPointerCapture(e.pointerId); pts.set(e.pointerId,{x:e.offsetX,y:e.offsetY}); moved=false; start={x:e.offsetX,y:e.offsetY,cx:st.view.cx,cy:st.view.cy};
      if(pts.size===2){const [a,b]=[...pts.values()]; pinch={d:Math.hypot(a.x-b.x,a.y-b.y),sc:st.view.sc,mx:(a.x+b.x)/2,my:(a.y+b.y)/2,cx:st.view.cx,cy:st.view.cy};} });
    cv.addEventListener('pointermove',e=>{
      if(!pts.has(e.pointerId)){ const n=nearest(e.offsetX,e.offsetY); trace=n?{x:n.x,y:n.y,col:col(n.o.row.c)}:null; draw(); return; }
      pts.set(e.pointerId,{x:e.offsetX,y:e.offsetY});
      if(pinch&&pts.size===2){const [a,b]=[...pts.values()]; const d=Math.hypot(a.x-b.x,a.y-b.y); const sc=Math.min(Math.max(pinch.sc*d/pinch.d,1e-3),1e6); const wxm=pinch.cx+(pinch.mx-W()/2)/pinch.sc, wym=pinch.cy-(pinch.my-H()/2)/pinch.sc; st.view.sc=sc; st.view.cx=wxm-(pinch.mx-W()/2)/sc; st.view.cy=wym+(pinch.my-H()/2)/sc; moved=true; draw(); return;}
      const dx=e.offsetX-start.x, dy=e.offsetY-start.y; if(Math.hypot(dx,dy)>3) moved=true;
      if(moved){ st.view.cx=start.cx-dx/st.view.sc; st.view.cy=start.cy+dy/st.view.sc; trace=null; draw(); }
    });
    const end=e=>{ pts.delete(e.pointerId); if(pts.size<2) pinch=null; if(!moved&&pts.size===0){ const f=features(e.offsetX,e.offsetY); if(f){ marks.push(f); draw(); } } save(); };
    cv.addEventListener('pointerup',end); cv.addEventListener('pointercancel',e=>{pts.delete(e.pointerId); pinch=null;});
    cv.addEventListener('pointerleave',()=>{trace=null; draw();});
    cv.addEventListener('wheel',e=>{ e.preventDefault(); const f=Math.exp(-e.deltaY*0.0015); const px=e.offsetX,py=e.offsetY; const X=wx(px),Y=wy(py); st.view.sc=Math.min(Math.max(st.view.sc*f,1e-3),1e6); st.view.cx=X-(px-W()/2)/st.view.sc; st.view.cy=Y+(py-H()/2)/st.view.sc; draw(); clearTimeout(cv._t); cv._t=setTimeout(save,300); },{passive:false});
  }
  function show(){ if(!window.math){ const b=$('.gcbtn'); if(b){b.textContent=G.loading; setTimeout(()=>b.textContent=T.calc,1500);} return; } if(!el) build(); el.hidden=false; st.open=true; st.min=false; place(); save(); requestAnimationFrame(draw); $$('.gcbtn').forEach(b=>b.setAttribute('aria-pressed','true')); }
  function hide(){ if(el) el.hidden=true; st.open=false; save(); $$('.gcbtn').forEach(b=>b.setAttribute('aria-pressed','false')); }
  function plot(expr){
    show(); if(!el) return; const s=/[=<>]/.test(expr)?expr:'y='+expr;
    if(!st.rows.some(r=>r.s.replace(/\s/g,'')===s.replace(/\s/g,''))){ const emptyI=st.rows.findIndex(r=>!r.s.trim()); if(emptyI>=0) st.rows[emptyI].s=s; else st.rows.push({s,c:st.rows.length%COLORS.length}); }
    st.view={cx:0,cy:0,sc:40}; renderRows();
  }
  document.addEventListener('click',e=>{
    if(e.target.closest('.gcbtn')){ (el&&!el.hidden)?hide():show(); }
    const p=e.target.closest('[data-plot]'); if(p) plot(p.dataset.plot);
  });
  function init(){ if(!$('.gcbtn')) return; if(st.open){ const go=()=>window.math?show():setTimeout(go,300); go(); } }
  return {init,show,hide,plot};
})();

/* ===== boot ===== */
function commonInit(){
  countdown(); setInterval(countdown,3600000);
  trackTopics(); initSide(); Focus.init(); Notes.init(); Tutor.init(); GC.init();
  const boot=()=>{ typeset(document.body); setTimeout(goHash,60); };
  if(window.renderMathInElement) boot(); else { let n=0; const w=()=>{ if(window.renderMathInElement||n++>40) boot(); else setTimeout(w,100); }; w(); }
}
