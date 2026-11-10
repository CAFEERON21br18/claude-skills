/* study-pack kit — method parts (Resumo + Revisão): saved pads, Cornell cover, complete-the-map, Kumon gate. */
(function(){
  const M=T.methods||{};
  /* "Write what you remember", Feynman, SQ3R and Hansei pads + Feynman checklist: kept in this browser */
  $$('[data-pad]').forEach(ta=>{const k=LSK('m-'+ta.dataset.pad); const v=lsGet(k); if(v) ta.value=v; let t=null; ta.addEventListener('input',()=>{clearTimeout(t); t=setTimeout(()=>lsSet(k,ta.value),400);});});
  $$('[data-chk]').forEach(c=>{const k=LSK('m-'+c.dataset.chk); c.checked=lsGet(k)==='1'; c.addEventListener('change',()=>lsSet(k,c.checked?'1':'0'));});
  $$('details.qd,details.sq,details.hint1').forEach(d=>d.addEventListener('toggle',()=>{if(d.open) typeset(d);}));
  /* Cornell: cover the notes column, tap a cell to check yourself */
  $$('.m-cornell').forEach(sec=>{
    const b=$('.ctog',sec), tb=$('table.cornell',sec);
    b&&b.addEventListener('click',()=>{const on=tb.classList.toggle('covered'); b.setAttribute('aria-pressed',String(on)); b.textContent=on?M.cornell.uncover:M.cornell.cover; $$('.cnote',tb).forEach(x=>{x.classList.remove('shown'); x.setAttribute('aria-expanded',String(!on));});});
    $$('.cnote',sec).forEach(x=>x.addEventListener('click',()=>{if(!tb.classList.contains('covered')) return; const s=x.classList.toggle('shown'); x.setAttribute('aria-expanded',String(s));}));
  });
  /* Complete the map: loose comparison, then the answer is shown */
  const norm=s=>String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^\w]+/g,' ').trim();
  $$('.mcheck').forEach(b=>b.addEventListener('click',()=>{
    const sec=b.closest('.mpart');
    $$('.mfill',sec).forEach(i=>{const ok=i.value.trim()&&(norm(i.value)===norm(i.dataset.ans)||norm(i.dataset.ans).includes(norm(i.value))&&norm(i.value).length>3);
      i.classList.toggle('ok',!!ok); i.classList.toggle('miss',!ok); const a=i.nextElementSibling; a.hidden=false; typeset(a);});
  }));
  /* Mind map: curved links from the centre to each branch (wide layout only; phones get the CSS spine) */
  function drawMap(m){
    const svg=$('.mlinks',m), c=$('.mctr',m); if(!svg||!c) return;
    if(getComputedStyle(svg).display==='none'){svg.innerHTML='';return;}
    const R=m.getBoundingClientRect(), C=c.getBoundingClientRect(); let d='';
    svg.setAttribute('viewBox',`0 0 ${R.width} ${R.height}`);
    $$('.mbr',m).forEach(b=>{const B=b.getBoundingClientRect(), left=B.right<=C.left+1;
      const x1=(left?C.left:C.right)-R.left, y1=C.top+C.height/2-R.top, x2=(left?B.right:B.left)-R.left, y2=B.top+Math.min(26,B.height/2)-R.top, mx=(x1+x2)/2;
      const col=getComputedStyle(b).borderTopColor;
      d+=`<path d="M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}" fill="none" stroke="${col}" stroke-width="2.5" stroke-linecap="round"/>`;});
    svg.innerHTML=d;
  }
  const maps=$$('.mmap'); if(maps.length){const ro=new ResizeObserver(es=>es.forEach(e=>drawMap(e.target))); maps.forEach(m=>{ro.observe(m); drawMap(m);});}
  /* Kumon: a level opens when 90 % of the level before is right */
  function kumon(){
    if(typeof state==='undefined') return;
    $$('.m-ku').forEach(sec=>{
      let open=true;
      $$('.klevel',sec).forEach(lv=>{
        $('.klock',lv).hidden=open; $('.kbody',lv).hidden=!open; lv.classList.toggle('locked',!open);
        const cards=$$('.ex',lv), ok=cards.filter(c=>state.status[c.dataset.id]==='ok').length;
        open=open&&cards.length>0&&ok/cards.length>=0.9;
      });
    });
  }
  if(typeof record==='function'){const r0=record; record=function(){r0.apply(null,arguments); kumon();}; }
  if(typeof applyAll==='function'){const a0=applyAll; applyAll=function(){a0(); kumon();}; }
  kumon();
})();
