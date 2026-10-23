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
    'plano': ['count', 'todayBtn', 'hideDoneBtn', 'themeBtn'],
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
    pages = [p for p in ('silabo', 'resumo', 'revisao', 'plano') if (out_dir / f'{p}.html').exists()]
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
                    if page != 'plano' and r['katexN'] == 0: fails.append(f'{tag}: no maths rendered at all (KaTeX not loaded?)')
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
        if page == 'plano':
            await pg.click('.sess input >> nth=0'); await pg.wait_for_timeout(200)
            t = await pg.inner_text('#oText')
            if not t.startswith('1'):
                fails.append(f'{tag}: ticking a session did not update the strip ({t})')
    except Exception as e:
        fails.append(f'{tag}: interaction failed: {str(e)[:160]}')

if __name__ == '__main__':
    fails = asyncio.run(run(sys.argv[1], '--shots' in sys.argv))
    if fails:
        print(f'{len(fails)} PROBLEM(S):'); [print(' -', f) for f in fails]; sys.exit(1)
    print('ALL CHECKS PASSED')
