#!/usr/bin/env python3
"""study-pack kit — build the four pack pages from JSON.

    python3 build.py PACK_DIR [--out OUT_DIR] [--pages silabo,resumo,revisao,plano]

PACK_DIR holds pack.json, topics/<n>.json and (for the plan) plan.json — see SCHEMA.md.
Every page gets the same header, rail, tools and styles. Do not hand-edit the output:
change the JSON and rebuild. The build stops on any schema error.
"""
import json, re, sys, os, base64, html, tarfile, io, subprocess, argparse, datetime, pathlib

KIT = pathlib.Path(__file__).resolve().parent
CACHE = KIT / '.cache'
PAGES = ['silabo', 'resumo', 'revisao', 'plano']
KATEX_V = '0.16.9'
MATHJS_V = '12.4.1'
CDN = 'https://cdnjs.cloudflare.com/ajax/libs'
MATRIX_RE = re.compile(r'\\begin\{(p|b|B|v|V)?matrix\}|\\begin\{array\}|\\begin\{cases\}')

class BuildError(Exception):
    pass

def fail(msg):
    raise BuildError(msg)

# ---------------------------------------------------------------- inputs
def load_pack(d):
    d = pathlib.Path(d)
    if not (d / 'pack.json').exists():
        fail(f'{d}/pack.json not found')
    pack = json.load(open(d / 'pack.json', encoding='utf-8'))
    topics = {}
    for t in pack.get('topics', []):
        f = d / 'topics' / f"{t['n']}.json"
        topics[t['n']] = json.load(open(f, encoding='utf-8')) if f.exists() else {'n': t['n']}
    plan = json.load(open(d / 'plan.json', encoding='utf-8')) if (d / 'plan.json').exists() else None
    validate(pack, topics, plan)
    return pack, topics, plan

def validate(pack, topics, plan):
    req = ['slug', 'course', 'short', 'lang', 'theme', 'font', 'features', 'topics', 'urls']
    for k in req:
        if k not in pack:
            fail(f'pack.json: missing "{k}"')
    if pack['lang'] not in ('pt', 'fr', 'en'):
        fail('pack.json: lang must be pt, fr or en')
    ns = [t['n'] for t in pack['topics']]
    if ns != list(range(1, len(ns) + 1)):
        fail(f'pack.json: topics must be numbered 1..N in order, got {ns}')
    for t in pack['topics']:
        if not t.get('name'):
            fail(f'pack.json: topic {t["n"]} has no name')
    seen = set()
    for n, tp in topics.items():
        for b in tp.get('resumo', []) + tp.get('lesson', []):
            if b.get('kind', 'p') not in ('p', 'def', 'thm', 'formula', 'method', 'trap', 'bookerr', 'note'):
                fail(f'topic {n}: unknown block kind {b.get("kind")}')
        for x in tp.get('examples', []):
            for k in ('title', 'statement', 'steps', 'answer', 'origin'):
                if k not in x:
                    fail(f'topic {n}: example "{x.get("title","?")}" missing "{k}"')
        for e in tp.get('exercises', []):
            for k in ('id', 'type', 'q', 'origin', 'key'):
                if k not in e:
                    fail(f'topic {n}: exercise {e.get("id","?")} missing "{k}"')
            if e['id'] in seen:
                fail(f'duplicate exercise id {e["id"]}')
            seen.add(e['id'])
            if e['type'] not in ('mcq', 'tf', 'free'):
                fail(f'exercise {e["id"]}: type must be mcq, tf or free')
            if e['type'] == 'mcq':
                if len(e.get('options', [])) != 4:
                    fail(f'exercise {e["id"]}: mcq needs exactly 4 options')
                if len(e.get('why', [])) != 4:
                    fail(f'exercise {e["id"]}: mcq needs 4 "why" lines (one per option)')
                if not isinstance(e.get('correct'), int) or not 0 <= e['correct'] < 4:
                    fail(f'exercise {e["id"]}: correct must be 0..3')
            if e['type'] == 'tf' and e.get('correct') not in (0, 1):
                fail(f'exercise {e["id"]}: tf correct must be 0 (true) or 1 (false)')
    if pack['features'].get('plan') and plan is None:
        fail('features.plan is on but plan.json is missing (run plan.py)')

# ---------------------------------------------------------------- text
class Ctx:
    def __init__(self, pack, page, S):
        self.pack, self.page, self.S = pack, page, S
        self.prefix = {'silabo': 't', 'resumo': 'r', 'revisao': 'ch', 'plano': 'd'}[page]

    def href(self, anchor):
        m = re.match(r'^(r|ch|t)(\d+)', anchor)
        if not m:
            return '#' + anchor
        if m.group(1) == self.prefix:
            return '#' + anchor
        page = {'r': 'resumo', 'ch': 'revisao', 't': 'silabo'}[m.group(1)]
        return f"{self.pack['urls'].get(page, '')}#{anchor}"

def inline(s, cx):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'\[\[(\d+)(?:\|([^\]]+))?\]\]',
               lambda m: f'<a class="recall" href="#{cx.prefix}{m.group(1)}">{m.group(2) or (cx.S["topic"] + " " + m.group(1))}</a>', s)
    s = re.sub(r'\[([^\]]+)\]\(#([\w-]+)\)', lambda m: f'<a href="{cx.href(m.group(2))}">{m.group(1)}</a>', s)
    return s

def md(src, cx):
    """Paragraphs, '- ' lists, '1. ' lists, **bold**, [txt](#r3), [[3]] recall links. $…$ is left for KaTeX."""
    out = []
    for b in re.split(r'\n{2,}', str(src or '').replace('\r', '').strip()):
        lines = b.split('\n')
        if all(re.match(r'^\s*[-*]\s+', l) for l in lines):
            out.append('<ul>' + ''.join('<li>' + inline(re.sub(r'^\s*[-*]\s+', '', l), cx) + '</li>' for l in lines) + '</ul>')
        elif all(re.match(r'^\s*\d+[.)]\s+', l) for l in lines):
            out.append('<ol>' + ''.join('<li>' + inline(re.sub(r'^\s*\d+[.)]\s+', '', l), cx) + '</li>' for l in lines) + '</ol>')
        elif b.strip():
            out.append('<p>' + '<br>'.join(inline(l, cx) for l in lines) + '</p>')
    return ''.join(out)

def mtx(*texts):
    return ' mtx' if any(MATRIX_RE.search(str(t or '')) for t in texts) else ''

def js(o):
    """JSON safe inside a <script> element."""
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')

def a(s):
    return html.escape(str(s), quote=True)

# ---------------------------------------------------------------- assets
def npm_file(pkg, ver, inner):
    CACHE.mkdir(exist_ok=True)
    tgz = CACHE / f'{pkg}-{ver}.tgz'
    if not tgz.exists():
        subprocess.run(['npm', 'pack', f'{pkg}@{ver}', '--silent', '--pack-destination', str(CACHE)], check=True, capture_output=True)
    with tarfile.open(tgz) as t:
        return t.extractfile('package/' + inner).read()

def katex_css():
    css = npm_file('katex', KATEX_V, 'dist/katex.min.css').decode()
    def repl(m):
        name = m.group(1)
        data = npm_file('katex', KATEX_V, f'dist/fonts/{name}.woff2')
        return f'src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format("woff2")'
    css = re.sub(r'src:url\(fonts/([\w-]+)\.woff2\) format\("woff2"\)(?:,url\([^)]*\) format\("[^"]*"\))*', repl, css)
    if 'fonts/' in css:
        fail('KaTeX CSS still references external fonts')
    return css

def font_block(font):
    mono = 'family=Atkinson+Hyperlegible+Mono:wght@400;600'
    if font.lower().replace(' ', '') == 'opendyslexic':
        faces = ''
        for w, f in ((400, 'OpenDyslexic-Regular'), (700, 'OpenDyslexic-Bold')):
            data = npm_file('open-dyslexic', '1.0.3', f'woff/{f}.woff')
            faces += f'@font-face{{font-family:"OpenDyslexic";font-weight:{w};font-style:normal;font-display:swap;src:url(data:font/woff;base64,{base64.b64encode(data).decode()}) format("woff")}}'
        link = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{mono}&display=swap">'
        return link, f'<style>{faces}</style>', '"OpenDyslexic",ui-sans-serif,system-ui,sans-serif'
    fam = font.strip().replace(' ', '+')
    link = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fam}:wght@400;700&{mono}&display=swap">'
    return link, '', f'"{font}",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif'

def theme_css(pack, family):
    th = pack['theme']
    if isinstance(th, str):
        themes = json.load(open(KIT / 'themes.json', encoding='utf-8'))
        if th not in themes:
            fail(f'unknown theme {th}; use one of {[k for k in themes if not k.startswith("_")]} or a custom object')
        th = themes[th]
    def tok(d):
        return ';'.join(f'--{k}:{v}' for k, v in d.items())
    dyslexic = 'OpenDyslexic' in family
    base = (f':root{{{tok(th["light"])};--dim:.15;--f-body:{family};--f-mono:"Atkinson Hyperlegible Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;color-scheme:light}}'
            f'@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{tok(th["dark"])};color-scheme:dark}}}}'
            f':root[data-theme="dark"]{{{tok(th["dark"])};color-scheme:dark}}')
    if dyslexic:
        base += 'body{font-size:17px;line-height:1.8;letter-spacing:.01em}'
    return base

# ---------------------------------------------------------------- shared pieces
MOON = '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
SUN = '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'

MONTHS = {
    'pt': ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'],
    'fr': ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'],
    'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
}

def kicker(pack):
    parts = [pack['short']]
    if pack.get('school'):
        parts.append(pack['school'])
    ex = pack.get('exam')
    if ex and ex.get('date'):
        y, m, d = map(int, ex['date'].split('-'))
        s = f"{ex.get('label', '')} {d} {MONTHS[pack['lang']][m - 1]} {y}".strip()
        if ex.get('time'):
            s += ', ' + ex['time']
        parts.append(s)
    return ' · '.join(parts)

def header(pack, page, S):
    F = pack['features']
    cur = ' aria-current="page"'
    nav = ''.join(
        f'<a href="{a(pack["urls"].get(p, "") or "#")}"{cur if p == page else ""}>{S["page"][p]}</a>'
        for p in PAGES if p != 'plano' or F.get('plan'))
    tools = []
    if pack.get('exam') and F.get('countdown', True):
        tools.append('<div class="count"><b id="cdN" class="mono">–</b><span id="cdL"></span></div>')
    if page in ('resumo', 'revisao') and F.get('calc'):
        tools.append(f'<button type="button" class="btn gcbtn" aria-pressed="false">{S["calc"]}</button>')
    if page in ('silabo', 'resumo', 'revisao') and F.get('focus', True):
        tools.append(f'<button type="button" class="btn" id="focusBtn" aria-pressed="false">{S["focus"]}</button>')
    if page == 'revisao' and F.get('review_only', True):
        tools.append(f'<button type="button" class="btn" id="reviewBtn" aria-pressed="false">{S["reviewOnly"]}</button>')
    if page == 'revisao' and F.get('history', True):
        tools.append(f'<button type="button" class="btn" id="histBtn" aria-expanded="false" aria-controls="hist">{S["history"]}</button>')
    if page == 'plano':
        tools.append(f'<button type="button" class="btn" id="todayBtn">{S["today"]}</button>')
        tools.append(f'<button type="button" class="btn" id="hideDoneBtn" aria-pressed="false">{S["hideDone"]}</button>')
    if page != 'plano':
        tools.append(f'<button type="button" class="btn" id="notesBtn">{S["notes"]}<span data-notecount></span></button>')
    tools.append(f'<button type="button" class="theme" id="themeBtn" aria-label="{a(S["themeAria"])}" title="{a(S["themeAria"])}">{MOON}{SUN}</button>')
    title = f'{S["pageLong"][page]} — {pack["course"]}'
    strip = ''
    if page == 'revisao' and F.get('progress', True):
        strip = '<div class="overall"><div class="wrap"><span id="oText" class="mono"></span><div class="bar" aria-hidden="true"><i class="okb" id="oOk"></i><i class="badb" id="oBad"></i></div><span id="saved" class="saved"></span></div></div>'
    if page == 'plano':
        strip = '<div class="overall"><div class="wrap"><span id="oText" class="mono"></span><div class="bar" aria-hidden="true"><i class="okb" id="oOk"></i></div><span id="saved" class="saved"></span></div></div>'
    return (f'<div class="top"><div class="band"><div class="wrap"><div class="brand"><span class="eyebrow">{a(kicker(pack))}</span><h1>{a(title)}</h1></div>'
            f'<nav class="navlinks" aria-label="{a(S["packNav"])}">{nav}</nav><div class="tools">{"".join(tools)}</div></div></div>{strip}</div>'), title

def rail(pack, page, S):
    lis = ''.join(
        f'<li><a href="#{ {"silabo": "t", "resumo": "r", "revisao": "ch"}[page]}{t["n"]}" data-n="{t["n"]}"><span class="nn mono">{t["n"]}</span><span class="nt">{a(t["name"])}</span>'
        + (f'<span class="dots" data-n="{t["n"]}"></span>' if page == 'revisao' else '') + '</a></li>'
        for t in pack['topics'])
    return f'<nav class="side" aria-label="{a(S["topics"])}"><span class="eyebrow sidelbl">{S["topics"]}</span><ol>{lis}</ol></nav>'

def drawers(pack, page, S):
    F = pack['features']
    N, H, U = S['notesUI'], S['hist'], S['tutor']
    out = '<div class="scrim" id="scrim" hidden></div>'
    if page in ('silabo', 'resumo', 'revisao'):
        out += f'<button type="button" class="btn sidebtn" id="sideBtn">{S["topicsBtn"]}</button>'
    if page == 'revisao' and F.get('history', True):
        out += (f'<aside class="drawer" id="hist" hidden aria-label="{a(H["title"])}"><header><h3>{H["title"]}</h3><button type="button" class="btn sm" id="histClose">{S["close"]}</button></header>'
                f'<div class="filters"><button type="button" class="btn sm" data-f="all" aria-pressed="true">{H["all"]}</button><button type="button" class="btn sm" data-f="ok" aria-pressed="false">{H["ok"]}</button><button type="button" class="btn sm" data-f="miss" aria-pressed="false">{H["miss"]}</button></div><ul class="dlist" id="hlist"></ul></aside>')
    if page != 'plano':
        out += (f'<div class="scrim" id="notesScrim" hidden></div><aside class="drawer" id="notesDrawer" hidden aria-label="{a(N["title"])}"><header><h3>{N["title"]}</h3><button type="button" class="btn sm" id="notesClose">{S["close"]}</button></header>'
                f'<div class="filters"><button type="button" class="btn sm" data-nf="all" aria-pressed="true">{N["all"]}</button><button type="button" class="btn sm" data-nf="mine" aria-pressed="false">{N["mine"]}</button><button type="button" class="btn sm" data-nf="q" aria-pressed="false">{N["q"]}</button></div>'
                f'<p class="hint" id="notesWhere"></p><ul class="dlist" id="notesList"></ul></aside>')
    if page != 'plano' and F.get('tutor', True):
        out += (f'<button type="button" class="btn solid chatfab" id="chatFab" hidden>{U["fab"]}</button>'
                f'<section class="chat" id="chat" hidden aria-label="{a(U["title"].format(short=pack["short"]))}"><header><div class="ct"><b>{a(U["title"].format(short=pack["short"]))}</b><span class="eyebrow" id="chatTopic"></span></div><button type="button" class="btn sm" id="chatClose">{S["close"]}</button></header>'
                f'<div class="ctxchip" id="ctxChip" hidden><span id="ctxLbl"></span><button type="button" class="linkbtn" id="ctxClear">{U["clear"]}</button></div>'
                f'<div class="msgs" id="msgs" aria-live="polite"></div><form class="chatform" id="chatForm"><label class="lbl" for="chatIn" hidden>{U["q"]}</label><textarea id="chatIn" rows="1" placeholder="{a(U["ph"])}"></textarea><button type="submit" class="btn solid" id="chatSend">{U["send"]}</button></form></section>')
    return out

def askb(S):
    return f'<button type="button" class="askb" data-ask="blk" hidden aria-label="{a(S["tutor"]["askBlk"])}" title="{a(S["tutor"]["askBlk"])}">?</button>'

def plot_btn(expr, pack, S):
    return f'<button type="button" class="btn sm ghost plotbtn" data-plot="{a(expr)}">{S["plot"]}</button>' if expr and pack['features'].get('calc') else ''

def th(n, name, meta):
    return (f'<div class="th fblk"><span class="tn mono">{n}</span><div class="thb"><h2>{a(name)}</h2>'
            + (f'<div class="tmeta"><span class="eyebrow">{a(meta)}</span></div>' if meta else '') + '</div><span class="nicon"></span></div>')

def origin_label(x, S):
    o = x.get('origin') or 'new'
    if o == 'new':
        return S['origin']['new']
    if x.get('reconstructed'):
        return f"{o} · {S['origin']['reconstructed']}"
    return o

def block_html(b, i, n, key_prefix, label_prefix, cx, pack, S):
    kind = b.get('kind', 'p')
    k = f'{key_prefix}{n}-b{i}'
    title = b.get('title') or (S['kind'].get(kind, '') if kind != 'p' else '')
    lbl = f'{label_prefix} {n} · {title or S["kind"]["note"] + " " + str(i)}'
    body = md(b.get('body', ''), cx)
    extra = mtx(b.get('body'))
    pb = plot_btn(b.get('plot'), pack, S)
    pbh = f'<div class="xact">{pb}</div>' if pb else ''
    if kind == 'p':
        return f'<div class="prose blk fblk{extra}" data-note="{k}" data-topic="{n}" data-label="{a(lbl)}"><span class="nicon">{askb(S)}</span>{body}{pbh}<div class="nslot"></div></div>'
    return (f'<div class="card {kind} blk fblk{extra}" data-note="{k}" data-topic="{n}" data-label="{a(lbl)}"><span class="nicon">{askb(S)}</span>'
            f'<h4>{a(title)}</h4><div class="prose">{body}</div>{pbh}<div class="nslot"></div></div>')

def steps_html(steps, cx, S):
    out = []
    for s in steps:
        li = f'<div class="sdo{mtx(s.get("do"))}">{md(s.get("do", ""), cx)}</div>'
        if s.get('why'):
            li += f'<div class="swhy"><b>{S["why"]}</b> {md(s["why"], cx)}</div>'
        if s.get('trap'):
            li += f'<div class="strap"><b>{S["trap"]}</b> {md(s["trap"], cx)}</div>'
        if s.get('by_claude'):
            li += f'<span class="tagc">{S["completedByClaude"]}</span>'
        if s.get('flag'):
            li += f'<div class="flag"><b>{S["stepWrong"]}</b>{md(s["flag"].get("text", ""), cx)}<div><b>{S["corrected"]}</b> {md(s["flag"].get("fix", ""), cx)}</div></div>'
        out.append(f'<li>{li}</li>')
    return '<ol class="steps">' + ''.join(out) + '</ol>'

def example_html(x, n, j, key, cx, pack, S, open_=False):
    num = f'{n}.{j}' if j else f'{n}'
    pb = plot_btn(x.get('plot'), pack, S)
    tutor = pack['features'].get('tutor', True)
    ask = f'<button type="button" class="btn sm ghost" data-ask="example" hidden>{S["tutor"]["ask"]}</button>' if tutor else ''
    return (f'<article class="xmp fblk" id="{key}" data-note="{key}" data-topic="{n}" data-label="{a(S["example"] + " " + num)}">'
            f'<div class="xh"><span class="xn mono">{num}</span><h4>{a(x["title"])}</h4><span class="src eyebrow">{a(origin_label(x, S))}</span><span class="nicon"></span></div>'
            f'<div class="xstmt prose{mtx(x["statement"])}">{md(x["statement"], cx)}</div>'
            f'<details class="sol"{" open" if open_ else ""}><summary>{S["showSolution"]}</summary>{steps_html(x["steps"], cx, S)}'
            f'<div class="ans{mtx(x["answer"])}"><b>{S["result"]}</b> {md(x["answer"], cx)}</div></details>'
            f'<div class="xact">{ask}{pb}</div><div class="nslot"></div></article>')

def xlinks(items):
    return '<div class="xlinks fblk">' + ''.join(f'<a href="{a(h)}">{t}</a>' for h, t in items) + '</div>'

# ---------------------------------------------------------------- pages
def page_silabo(pack, topics, S, cx):
    U = pack['urls']
    secs = []
    for t in pack['topics']:
        n = t['n']; tp = topics[n]
        lis = ''.join(f'<li class="fblk{mtx(b)}">{inline(b, cx)}</li>' for b in tp.get('syllabus', []))
        if not lis:
            fail(f'topic {n}: syllabus bullets missing')
        secs.append(f'<section class="topic" id="t{n}" data-n="{n}" data-topic-sec data-note="t{n}" data-topic="{n}" data-label="{a(S["page"]["silabo"] + f" {n} · " + t["name"])}">'
                    + th(n, t['name'], t.get('meta')) + f'<ul class="syl">{lis}</ul>'
                    + xlinks([(f'{U["resumo"]}#r{n}', S['readAll'].format(n=n)), (f'{U["revisao"]}#ch{n}', S['practice'].format(n=n))])
                    + '<div class="nslot"></div></section>')
    intro = f'<div class="intro"><p class="hint">{a(S["intro"]["silabo"].format(n=len(pack["topics"])))}</p><p class="hint">{a(S["intro"]["notesHint"])}</p></div>'
    return f'<div class="wrap layout">{rail(pack, "silabo", S)}<main>{intro}{"".join(secs)}</main></div>'

def page_resumo(pack, topics, S, cx):
    U = pack['urls']
    secs = []
    for t in pack['topics']:
        n = t['n']; tp = topics[n]
        blocks = ''.join(block_html(b, i + 1, n, 'r', S['page']['resumo'], cx, pack, S) for i, b in enumerate(tp.get('resumo', [])))
        exs = tp.get('examples', [])
        if len(exs) < 3:
            fail(f'topic {n}: the Resumo needs at least 3 solved examples (has {len(exs)})')
        xs = ''.join(example_html(x, n, j + 1, f'r{n}-x{j + 1}', cx, pack, S) for j, x in enumerate(exs))
        links = [(f'{U["silabo"]}#t{n}', S['essential'].format(n=n)), (f'{U["revisao"]}#ch{n}', S['practice'].format(n=n))]
        secs.append(f'<section class="topic" id="r{n}" data-n="{n}" data-topic-sec data-note="r{n}" data-topic="{n}" data-label="{a(S["page"]["resumo"] + f" {n} · " + t["name"])}">'
                    + th(n, t['name'], t.get('meta')) + xlinks(links) + '<div class="nslot"></div>'
                    + f'<div class="lesson">{blocks}</div><h3 class="exh fblk">{S["examples"]}</h3><div class="xs">{xs}</div>' + xlinks(links) + '</section>')
    intro = f'<div class="intro"><p>{a(S["intro"]["resumo"])}</p><p class="hint">{a(S["intro"]["notesHint"])}</p></div>'
    return f'<div class="wrap layout">{rail(pack, "resumo", S)}<main>{intro}{"".join(secs)}</main></div>'

def free_box(eid, S, with_showkey):
    sk = f'<button type="button" class="btn showkey">{S["showKey"]}</button>' if with_showkey else ''
    return (f'<div class="freebox"><label class="lbl" for="ta-{eid}">{S["yourWork"]}</label><textarea id="ta-{eid}" rows="5" placeholder="{a(S["workPh"])}"></textarea>'
            f'<div class="photo" hidden><label class="lbl" for="ph-{eid}">{S["photo"]}</label><input type="file" id="ph-{eid}" accept="image/*" multiple></div><p class="err" hidden></p>'
            f'<div class="acts"><button type="button" class="btn solid grade" hidden>{S["grade"]}</button><button type="button" class="btn stop" hidden>{S["stop"]}</button>{sk}</div><div class="verdict" hidden></div></div>')

def exercise_html(e, n, j, cx, pack, S):
    eid = e['id']; typ = e['type']
    key = e['key']
    keyh = (f'<div class="key" hidden><h5>{S["keyTitle"]}</h5>{steps_html(key.get("steps", []), cx, S)}'
            + (f'<div class="ans{mtx(key.get("answer"))}"><b>{S["result"]}</b> {md(key["answer"], cx)}</div>' if key.get('answer') else '')
            + (f'<div class="self"><span>{S["howWent"]}</span><button type="button" class="btn sm" data-self="ok">{S["gotIt"]}</button><button type="button" class="btn sm" data-self="miss">{S["missed"]}</button></div>' if typ == 'free' else '')
            + '</div>')
    body = ''
    if typ in ('mcq', 'tf'):
        opts = e['options'] if typ == 'mcq' else [S['true'], S['false']]
        letters = 'ABCD' if typ == 'mcq' else ['V' if pack['lang'] == 'pt' else 'V' if pack['lang'] == 'fr' else 'T', 'F']
        cls = 'opts two' if (typ == 'tf' or e.get('layout') == 'two') else 'opts'
        ob = ''.join(f'<button type="button" class="opt{mtx(o)}" data-v="{i}"><span class="L">{letters[i]}</span><span class="ot">{inline(o, cx) if typ == "mcq" else a(o)}</span></button>' for i, o in enumerate(opts))
        gate = bool(e.get('gate'))
        if gate:
            body += f'<div class="gate fblk"><p class="hint">{S["gateHint"]}</p><button type="button" class="btn gatebtn">{S["gateBtn"]}</button></div>'
        body += f'<div class="{cls}"{" hidden" if gate else ""}>{ob}</div>'
        whys = e.get('why') or ['', '']
        body += '<div class="fb" hidden>' + ''.join(f'<div class="why{mtx(w)}" data-v="{i}" hidden><b class="wl">{letters[i]}</b>{md(w, cx)}</div>' for i, w in enumerate(whys) if w) + '</div>'
        if e.get('free_too'):
            body += free_box(eid, S, False)
        body += keyh
    else:
        body += free_box(eid, S, True) + keyh
    tutor = pack['features'].get('tutor', True)
    ask = f'<button type="button" class="btn sm ghost" data-ask="ex" hidden>{S["tutor"]["ask"]}</button>' if tutor else ''
    pb = plot_btn(e.get('plot'), pack, S)
    corr = f' data-correct="{e["correct"]}"' if typ in ('mcq', 'tf') else ''
    lbl = f'{n}.{j} · {origin_label(e, S)}'
    return (f'<article class="ex {typ} fblk" id="{eid}" data-id="{eid}" data-n="{n}"{corr} data-note="{eid}" data-topic="{n}" data-label="{a(lbl)}">'
            f'<div class="exhead"><span class="exn mono">{n}.{j}</span><span class="src eyebrow">{a(origin_label(e, S))}</span><span class="badge" hidden></span><span class="nicon"></span></div>'
            f'<div class="q prose{mtx(e["q"])}">{md(e["q"], cx)}</div>{body}<div class="xact">{ask}{pb}</div><button type="button" class="btn redo sm" hidden>{S["redo"]}</button><div class="nslot"></div></article>')

def page_revisao(pack, topics, S, cx):
    U = pack['urls']; F = pack['features']
    secs = []
    for t in pack['topics']:
        n = t['n']; tp = topics[n]
        blocks = ''.join(block_html(b, i + 1, n, 'ch', S['page']['revisao'], cx, pack, S) for i, b in enumerate(tp.get('lesson', [])))
        w = tp.get('worked')
        wk = f'<h3 class="exh fblk">{S["workedExample"]}</h3><div class="xs">{example_html(w, n, 0, f"ch{n}-x0", cx, pack, S, open_=True)}</div>' if w else ''
        exs = tp.get('exercises', [])
        shortage = f'<p class="shortage">{a(tp["shortage"])}</p>' if tp.get('shortage') else (f'<p class="shortage">{a(S["shortage"])}</p>' if not exs else '')
        exh = ''.join(exercise_html(e, n, j + 1, cx, pack, S) for j, e in enumerate(exs))
        prog = f'<div class="tprog"><div class="bar" aria-hidden="true"><i class="okb"></i><i class="badb"></i></div><span class="tcount mono"></span></div>' if F.get('progress', True) else ''
        secs.append(f'<section class="topic" id="ch{n}" data-n="{n}" data-topic-sec data-note="ch{n}" data-topic="{n}" data-label="{a(S["page"]["revisao"] + f" {n} · " + t["name"])}">'
                    + th(n, t['name'], t.get('meta'))
                    + xlinks([(f'{U["resumo"]}#r{n}', S['fullVersion'].format(n=n)), (f'{U["silabo"]}#t{n}', S['essential'].format(n=n))])
                    + prog + '<div class="nslot"></div>'
                    + f'<div class="lesson">{blocks}</div>{wk}<h3 class="exh fblk">{S["yourExercises"] if pack.get("exercise", {}).get("source") == "mine" else S["exercises"]}</h3>{shortage}<div class="exs">{exh}</div></section>')
    intro = f'<div class="intro"><p class="hint">{a(S["intro"]["revisao"])}</p><p class="hint">{a(S["intro"]["notesHint"])}</p><p class="hint" id="chatOff" hidden>{a(S["tutor"]["off"])}</p></div>'
    empty = f'<p class="empty" id="emptyMiss">{a(S["emptyMiss"])}</p>'
    return f'<div class="wrap layout">{rail(pack, "revisao", S)}<main>{intro}{empty}{"".join(secs)}</main></div>'

def page_plano(pack, plan, S):
    P = S['plan']; ex = pack.get('exam') or {}
    if ex.get('date'):
        y, m, d = map(int, ex['date'].split('-'))
        exam_day = f'{d} {MONTHS[pack["lang"]][m - 1]}'
    else:
        exam_day = '–'
    sub_hours = plan.get('hours_note', '')
    return (f'<main class="wrap pmain"><div class="sum"><div><b class="mono">{a(exam_day)}</b><span>{a(ex.get("label", ""))}{", " + a(ex["time"]) if ex.get("time") else ""}</span></div>'
            f'<div><b id="sDays" class="mono">–</b><span>{P["daysLeft"]}</span></div><div><b id="sHours" class="mono">–</b><span id="sDone">{P["hoursPlanned"]}</span></div>'
            f'<div><b class="mono">{len(pack["topics"])}</b><span>{P["topicsN"]}</span></div></div>'
            f'<section><h2>{P["barsTitle"]}</h2><p class="sub">{a(sub_hours)}</p><div class="panel"><div class="legend">'
            + ''.join(f'<span><i style="background:{c}"></i>{P["act"][k]}</span>' for k, c in (('learn', 'var(--accent)'), ('ex', 'var(--accent2)'), ('rev', 'var(--warn)'), ('test', 'var(--bad)')))
            + f'</div><div class="scroll" id="bars"></div></div></section>'
            f'<section><h2>{P["timelineTitle"]}</h2><p class="sub">{P["timelineSub"]}</p><div class="panel"><div class="scroll" id="timeline"></div></div></section>'
            f'<section><h2>{P["progTitle"]}</h2><p class="sub">{P["progSub"]}</p><div class="panel"><div class="scroll" id="prog"></div></div></section>'
            f'<section><h2>{P["daysTitle"]}</h2><p class="sub">{P["daysSub"]}</p><div class="days" id="days"></div></section></main>')

# ---------------------------------------------------------------- assemble
def build(pack_dir, out_dir, pages=None):
    pack, topics, plan = load_pack(pack_dir)
    I18N = json.load(open(KIT / 'i18n.json', encoding='utf-8'))
    S = I18N[pack['lang']]
    F = pack['features']
    pages = pages or [p for p in PAGES if p != 'plano' or F.get('plan')]
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    link, faces, family = font_block(pack['font'])
    css = theme_css(pack, family) + (KIT / 'assets' / 'core.css').read_text(encoding='utf-8')
    kcss = katex_css()
    core_js = (KIT / 'assets' / 'core.js').read_text(encoding='utf-8')
    store = pack.get('storage') or {}
    store = {'prefix': store.get('prefix', pack['slug'] + '-'), 'docs': store.get('docs', {}), 'ls': store.get('ls', {})}
    results = {}
    for page in pages:
        cx = Ctx(pack, page, S)
        head, title = header(pack, page, S)
        if page == 'silabo':
            body = page_silabo(pack, topics, S, cx); src = {str(n): {'syllabus': topics[n].get('syllabus', [])} for n in topics}
        elif page == 'resumo':
            body = page_resumo(pack, topics, S, cx); src = {str(n): {k: topics[n].get(k) for k in ('resumo', 'examples')} for n in topics}
        elif page == 'revisao':
            body = page_revisao(pack, topics, S, cx); src = {str(n): {k: topics[n].get(k) for k in ('lesson', 'worked', 'exercises', 'shortage')} for n in topics}
        else:
            if not plan:
                fail('plano requested but plan.json missing')
            body = page_plano(pack, plan, S); src = plan
        packjs = {'page': page, 'title': title, 'course': pack['course'], 'short': pack['short'], 'lang': pack['lang'], 't': S,
                  'exam': pack.get('exam'), 'urls': pack['urls'], 'topics': {str(t['n']): t['name'] for t in pack['topics']},
                  'store': store, 'features': F}
        scripts = [f'{CDN}/KaTeX/{KATEX_V}/katex.min.js', f'{CDN}/KaTeX/{KATEX_V}/contrib/auto-render.min.js', f'{CDN}/KaTeX/{KATEX_V}/contrib/copy-tex.min.js']
        if F.get('calc') and page in ('resumo', 'revisao'):
            scripts.append(f'{CDN}/mathjs/{MATHJS_V}/math.min.js')
        page_js = (KIT / 'assets' / f'{page}.js').read_text(encoding='utf-8') if page in ('revisao', 'plano') else 'commonInit();'
        plan_js = f'const PLAN={js(plan)};' if page == 'plano' else ''
        config = {k: v for k, v in pack.items() if k != 'topics'}
        config.update({'topics': pack['topics'], 'page': page, 'built': datetime.date.today().isoformat(), 'kit': 'study-pack kit 1'})
        doc = (f'<!doctype html><html lang="{pack["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<meta name="claude:viewport-fit-sides" content="cover"><title>{a(title)}</title>'
               f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{link}{faces}'
               f'<style>{kcss}</style><style>{css}</style></head><body class="p-{page}">'
               f'{head}{body}{drawers(pack, page, S)}'
               f'<script type="application/json" id="pack-config">{js(config)}</script>'
               f'<script type="application/json" id="pack-src">{js(src)}</script>'
               + ''.join(f'<script src="{s}" defer></script>' for s in scripts)
               + f'<script>window.addEventListener("DOMContentLoaded",function(){{const PACK={js(packjs)};{plan_js}\n'
               + f'{core_js}\n{page_js}\n}});</script></body></html>')
        if 'target="_blank"' in doc:
            fail(f'{page}: target="_blank" is not allowed')
        p = out / f'{page}.html'
        p.write_text(doc, encoding='utf-8')
        results[page] = (p, len(doc.encode()))
    return results

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('pack'); ap.add_argument('--out', default=None); ap.add_argument('--pages', default=None)
    args = ap.parse_args()
    try:
        r = build(args.pack, args.out or os.path.join(args.pack, 'out'), args.pages.split(',') if args.pages else None)
    except BuildError as e:
        print('BUILD ERROR:', e); sys.exit(1)
    for k, (p, n) in r.items():
        print(f'{k:8s} {n/1024:7.0f} KB  {p}')
