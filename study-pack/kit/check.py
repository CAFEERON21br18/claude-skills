#!/usr/bin/env python3
"""study-pack kit — render check. Run before EVERY publish; publish only when it prints ALL CHECKS PASSED.

    python3 check.py OUT_DIR [--shots]

For each page, at 400 px and 1440 px, light and dark, with gated options and solutions opened:
  1. no horizontal page scroll (scrollWidth − innerWidth = 0)
  2. nothing clipped: no element holding maths with overflow ≠ visible and scrollHeight > clientHeight + 2
  3. 0 .katex-error and no "$" left unrendered in the text
  4. no JS error
  5. the header is the fixed one: brand | 4 tabs | tools in the fixed order for that page
  6. no target="_blank", one tab marked aria-current
  7. interactions run: note icon, focus mode, calculator, gate + option, plan tick
--shots saves screenshots of the header and of 3 dense blocks per page in OUT_DIR/shots/ — look at them.
"""
import sys, json, asyncio, pathlib, tarfile, subprocess, re
from playwright.async_api import async_playwright

KIT = pathlib.Path(__file__).resolve().parent
CACHE = KIT / '.cache'
EXPECT_TOOLS = {  # fixed order of the header tools (ids / classes), optional ones may be absent but never reordered
    'silabo': ['count', 'focusBtn', 'notesBtn', 'themeBtn'],
    'resumo': ['count', 'gcbtn', 'focusBtn', 'notesBtn', 'themeBtn'],
    'revisao': ['count', 'gcbtn', 'focusBtn', 'reviewBtn', 'histBtn', 'notesBtn', 'themeBtn'],
    'testes': ['count', 'todayBtn', 'themeBtn'],
    'mapa': ['count', 'themeBtn'],
    'plano': ['count', 'origBtn', 'todayBtn', 'hideDoneBtn', 'themeBtn'],
}

def npm(pkg, ver, inner):
    CACHE.mkdir(exist_ok=True)
    tgz = CACHE / f'{pkg}-{ver}.tgz'
    if not tgz.exists():
        subprocess.run(['npm', 'pack', f'{pkg}@{ver}', '--silent', '--pack-destination', str(CACHE)], check=True, capture_output=True)
    with tarfile.open(tgz) as t:
        return t.extractfile('package/' + inner).read()

LOCAL = {
    'katex.min.js': ('katex', '0.16.9', 'dist/katex.min.js'),
    'auto-render.min.js': ('katex', '0.16.9', 'dist/contrib/auto-render.min.js'),
    'copy-tex.min.js': ('katex', '0.16.9', 'dist/contrib/copy-tex.min.js'),
    'math.min.js': ('mathjs', '12.4.1', 'lib/browser/math.js'),
}

JS_CHECK = r"""(page)=>{
  const out={errors:[]};
  out.hscroll=document.documentElement.scrollWidth-innerWidth;
  const clipped=[];
  document.querySelectorAll('body *').forEach(el=>{
    if(el.closest('.katex-mathml')||el.closest('.drawer')||el.closest('.chat')||el.closest('.gc')||el.closest('.side')) return;
    if(!el.querySelector('.katex')) return;
    const cs=getComputedStyle(el); if(cs.overflowY==='visible'&&cs.overflowX==='visible') return;
    if(el.matches('.katex-display,.katex.mxw')){ if(el.scrollHeight>el.clientHeight+2) clipped.push(el.className); return; }
    if(el.scrollHeight>el.clientHeight+2||el.scrollWidth>el.clientWidth+2) clipped.push((el.id?'#'+el.id:'')+'.'+String(el.className).split(' ').join('.'));
  });
  out.clipped=clipped.slice(0,8);
  out.katexErr=document.querySelectorAll('.katex-error').length;
  out.katexN=document.querySelectorAll('.katex').length;
  const _src=document.getElementById('pack-src'); out.hasMaths=!!_src&&/\$/.test(_src.textContent);
  const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{acceptNode:n=>{const p=n.parentElement; if(!p||p.closest('script,style,textarea,.katex,code,pre,.nomath')) return NodeFilter.FILTER_REJECT; return /\$/.test(n.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;}});
  const raw=[]; let n; while((n=w.nextNode())&&raw.length<5) raw.push(n.nodeValue.trim().slice(0,60)); out.rawDollar=raw;
  const wrap=document.querySelector('.top .band .wrap');
  out.headerKids=wrap?[...wrap.children].map(c=>c.className):[];
  out.tools=[...document.querySelectorAll('.top .tools > *')].map(c=>c.id||(c.classList.contains('count')?'count':c.classList.contains('gcbtn')?'gcbtn':c.className));
  out.navN=document.querySelectorAll('.navlinks a').length; out.cur=document.querySelectorAll('.navlinks a[aria-current="page"]').length;
  out.blank=document.querySelectorAll('[target="_blank"]').length;
  return out;
}"""

async def run(out_dir, shots):
    out_dir = pathlib.Path(out_dir); fails = []
    pages = [p for p in ('silabo', 'resumo', 'revisao', 'testes', 'mapa', 'plano') if (out_dir / f'{p}.html').exists()]
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for page in pages:
            for width, height in ((400, 860), (1440, 900)):
                for scheme in ('light', 'dark'):
                    ctx = await b.new_context(viewport={'width': width, 'height': height}, color_scheme=scheme)
                    pg = await ctx.new_page(); errs = []
                    pg.on('pageerror', lambda e, errs=errs: errs.append(str(e)))
                    pg.on('console', lambda m, errs=errs: errs.append(m.text) if m.type == 'error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
                    async def route(r):
                        u = r.request.url; name = u.rsplit('/', 1)[-1]
                        if 'cdnjs' in u and name in LOCAL:
                            await r.fulfill(body=npm(*LOCAL[name]), content_type='application/javascript')
                        elif u.startswith('file:'):
                            await r.continue_()
                        else:
                            await r.abort()
                    await pg.route('**/*', route)
                    await pg.goto((out_dir / f'{page}.html').resolve().as_uri(), wait_until='load')
                    await pg.wait_for_timeout(700)
                    # open everything that can hide maths
                    await pg.evaluate("""()=>{document.querySelectorAll('details').forEach(d=>d.open=true);
                      document.querySelectorAll('.gatebtn').forEach(b=>b.click());
                      document.querySelectorAll('.key,.fb,.why').forEach(k=>k.hidden=false);}""")
                    await pg.wait_for_timeout(400)
                    r = await pg.evaluate(JS_CHECK, page)
                    tag = f'{page} {width}px {scheme}'
                    if r['hscroll'] > 0: fails.append(f'{tag}: horizontal scroll {r["hscroll"]}px')
                    if r['clipped']: fails.append(f'{tag}: clipped maths in {r["clipped"]}')
                    if r['katexErr']: fails.append(f'{tag}: {r["katexErr"]} .katex-error')
                    if r['rawDollar']: fails.append(f'{tag}: unrendered $ in {r["rawDollar"]}')
                    if page not in ('plano', 'mapa', 'testes') and r['hasMaths'] and r['katexN'] == 0: fails.append(f'{tag}: no maths rendered at all (KaTeX not loaded?)')
                    if r['headerKids'] != ['brand', 'navlinks', 'tools']: fails.append(f'{tag}: header must be brand|navlinks|tools, got {r["headerKids"]}')
                    exp = [t for t in EXPECT_TOOLS[page] if t in r['tools']]
                    if r['tools'] != exp: fails.append(f'{tag}: tools order {r["tools"]} ≠ {EXPECT_TOOLS[page]}')
                    if r['cur'] != 1 or r['navN'] < 3: fails.append(f'{tag}: pack tabs wrong ({r["navN"]} tabs, {r["cur"]} current)')
                    if r['blank']: fails.append(f'{tag}: target=_blank found')
                    if width == 1440 and scheme == 'light':
                        if shots:
                            sd = out_dir / 'shots'; sd.mkdir(exist_ok=True)
                            dense = await pg.query_selector_all('.mtx, .katex-display')
                            for i, el in enumerate(dense[:3]):
                                try:
                                    await el.scroll_into_view_if_needed(); await el.screenshot(path=str(sd / f'{page}-dense{i+1}.png'))
                                except Exception:
                                    pass
                            await pg.evaluate('()=>scrollTo(0,0)')
                            await pg.screenshot(path=str(sd / f'{page}-top.png'))
                        await interact(pg, page, fails, tag)
                    if width == 400 and scheme == 'dark' and shots:
                        sd = out_dir / 'shots'; sd.mkdir(exist_ok=True)
                        await pg.evaluate('()=>scrollTo(0,0)'); await pg.screenshot(path=str(sd / f'{page}-phone-dark.png'))
                    for e in errs:
                        fails.append(f'{tag}: JS error {e[:160]}')
                    await ctx.close()
        await b.close()
    return fails

async def interact(pg, page, fails, tag):
    try:
        if page == 'mapa':
            await interact_mapa(pg, fails, tag); return
        if page == 'testes':
            await interact_testes(pg, fails, tag); return
        if page != 'plano':
            await pg.click('.nbtn >> nth=0'); await pg.wait_for_selector('.notebox', timeout=2000)
            await pg.click('#focusBtn'); await pg.wait_for_selector('.fblk.is-focus', timeout=2000)
            await pg.click('#notesBtn'); await pg.wait_for_selector('#notesDrawer:not([hidden])', timeout=2000); await pg.click('#notesClose')
        if page in ('resumo', 'revisao') and await pg.query_selector('.gcbtn'):
            await pg.click('.gcbtn'); await pg.wait_for_selector('.gc canvas', timeout=4000)
        if page == 'revisao':
            o = await pg.query_selector('.ex.mcq .opt')
            if o:
                await pg.evaluate("()=>{const ex=document.querySelector('.ex.mcq'); ex.querySelector('.opts').hidden=false;}")
                await o.click(); await pg.wait_for_selector('.ex.mcq .badge:not([hidden])', timeout=2000)
            await pg.click('#histBtn'); await pg.wait_for_selector('#hist:not([hidden]) li.item', timeout=2000)
            await pg.click('#histClose')
            # every exercise must show a complete correction: method + steps + answer
            bad = await pg.evaluate("()=>[...document.querySelectorAll('.ex .key')].filter(k=>!k.querySelector('.howto')||k.querySelectorAll('.steps li').length<1||!k.querySelector('.ans')).length")
            if bad: fails.append(f'{tag}: {bad} exercise(s) without a complete correction (method, steps, answer)')
            # a tutor note ("didn't understand") is shown at the start of its exercise
            await pg.evaluate("""()=>{const c=JSON.parse(document.getElementById('pack-config').textContent); const pre=(c.storage&&c.storage.prefix)||c.slug+'-';
              const ex=document.querySelector('.ex[data-note]'); localStorage.setItem(pre+'notes-revisao',JSON.stringify({items:{[ex.id]:[{id:'chk1',date:Date.now(),kind:'q',topic:1,label:'x',unclear:'CHECK-NOTE',text:'**Não percebi:** CHECK-NOTE\\n\\nexpl'}]}}));}""")
            await pg.reload(); await pg.wait_for_timeout(900)
            pos = await pg.evaluate("()=>{const q=document.querySelector('.ex > .qtop'); if(!q) return 'none'; return q.previousElementSibling&&q.previousElementSibling.classList.contains('exhead')&&q.innerText.includes('CHECK-NOTE')?'ok':'misplaced'}")
            if pos != 'ok': fails.append(f'{tag}: tutor note on an exercise is {pos} (must be at the top of the exercise)')
        if page == 'plano':
            await pg.click('.sess input >> nth=0'); await pg.wait_for_timeout(200)
            t = await pg.inner_text('#oText')
            if not t.startswith('1'):
                fails.append(f'{tag}: ticking a session did not update the strip ({t})')
            past = await pg.evaluate("()=>{const t=new Date(); const iso=new Date(t-t.getTimezoneOffset()*60000).toISOString().slice(0,10); return PLAN_DAYS_PAST(iso)}".replace('PLAN_DAYS_PAST(iso)', "[...document.querySelectorAll('.day')].filter(d=>d.id.slice(1)<iso).length"))
            if past:
                moved = await pg.evaluate("()=>document.querySelectorAll('.tag.moved').length")
                if not moved: fails.append(f'{tag}: past sessions left undone did not move to the next days')
                if await pg.evaluate("()=>document.getElementById('adapt').hidden"): fails.append(f'{tag}: the adapted-plan box is not shown')
                # a weak test result adds an extra review
                await pg.evaluate("""()=>{const c=JSON.parse(document.getElementById('pack-config').textContent); if(!c.features.tests) return; const pre=(c.storage&&c.storage.prefix)||c.slug+'-';
                  localStorage.setItem(pre+'testes',JSON.stringify({results:{m1:{t:Date.now()-86400000,ok:0,tot:2,byTopic:{'1':[0,2]},pending:0}}}));}""")
                await pg.reload(); await pg.wait_for_timeout(900)
                if await pg.evaluate("()=>JSON.parse(document.getElementById('pack-config').textContent).features.tests") and not await pg.evaluate("()=>document.querySelectorAll('.tag.boost').length"):
                    fails.append(f'{tag}: a topic failed in a test did not get an extra review')
                await pg.click('#origBtn'); await pg.wait_for_timeout(200)
                if await pg.evaluate("()=>document.querySelectorAll('.tag.moved,.tag.boost').length"): fails.append(f'{tag}: "original plan" still shows adapted sessions')
    except Exception as e:
        fails.append(f'{tag}: interaction failed: {str(e)[:160]}')

async def interact_testes(pg, fails, tag):
    """Testes: open a test, answer one question, finish: every question shows its full correction and the score is saved."""
    card = await pg.query_selector('.tst')
    await pg.click('.tst >> nth=0 >> .tstart')
    await pg.evaluate("()=>{const c=document.querySelector('.tst'); c.querySelectorAll('.gatebtn').forEach(b=>b.click());}")
    o = await pg.query_selector('.tst >> nth=0 >> .ex.mcq .opt, .tst >> nth=0 >> .ex.tf .opt')
    first = await pg.query_selector('.tst .ex.mcq .opt, .tst .ex.tf .opt')
    if first: await first.click()
    if await pg.evaluate("()=>document.querySelectorAll('.tst .opt.right').length"): fails.append(f'{tag}: a test shows the right answer before "finish"')
    await pg.click('.tst >> nth=0 >> .tfinish'); await pg.wait_for_selector('.tst .tresult:not([hidden])', timeout=2000)
    hidden_keys = await pg.evaluate("()=>[...document.querySelector('.tst').querySelectorAll('.ex .key')].filter(k=>k.hidden||!k.querySelector('.howto')).length")
    if hidden_keys: fails.append(f'{tag}: {hidden_keys} test question(s) without their full correction after finishing')
    await pg.reload(); await pg.wait_for_timeout(800)
    if await pg.evaluate("()=>document.querySelector('.tst .tscore').hidden") and await pg.evaluate("()=>!document.querySelector('.tst .ex.free')"):
        fails.append(f'{tag}: the test score was not saved')

async def interact_mapa(pg, fails, tag):
    """Mapa: pick a card, check the panel fields, follow a route, answer a training question, tick 'known'."""
    await pg.click('.mp-card >> nth=3'); await pg.wait_for_selector('#mpPanel h2', timeout=2000)
    n_sec = await pg.evaluate("()=>document.querySelectorAll('#mpPanel .mp-sec').length")
    if n_sec < 4: fails.append(f'{tag}: mapa panel shows only {n_sec} sections (context, explanation, key points, links expected)')
    if not await pg.query_selector('.mp-card.is-sel'): fails.append(f'{tag}: mapa: card not marked selected')
    bad = await pg.evaluate("()=>{const t=document.getElementById('mpPanel').innerText;return (/\\$/.test(t)?1:0)+document.querySelectorAll('#mpPanel .katex-error').length}")
    if bad: fails.append(f'{tag}: mapa panel shows raw $ or a KaTeX error')
    await pg.click('#mpPanel [data-act=know]'); await pg.wait_for_selector('.mp-card.known', timeout=2000)
    await pg.click('[data-tab][data-m=routes]'); await pg.click('#mpPanel [data-act=route] >> nth=0'); await pg.wait_for_selector('.mp-prog', timeout=2000)
    await pg.click('#mpPanel [data-act=next]'); await pg.wait_for_selector('.mp-because', timeout=2000)
    await pg.click('[data-tab][data-m=train]'); await pg.wait_for_selector('.mp-opt', timeout=2000)
    await pg.click('.mp-opt >> nth=0'); await pg.wait_for_selector('.mp-fb', timeout=2000)

if __name__ == '__main__':
    fails = asyncio.run(run(sys.argv[1], '--shots' in sys.argv))
    if fails:
        print(f'{len(fails)} PROBLEM(S):'); [print(' -', f) for f in fails]; sys.exit(1)
    print('ALL CHECKS PASSED')
