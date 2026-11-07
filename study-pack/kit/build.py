#!/usr/bin/env python3
"""study-pack kit — build the pack pages (up to five) from JSON.

    python3 build.py PACK_DIR [--out OUT_DIR] [--pages silabo,resumo,revisao,mapa,plano]

PACK_DIR holds pack.json, topics/<n>.json, plan.json (plan) and map.json (idea map) — see SCHEMA.md.
Every page gets the same header, rail, tools and styles. Do not hand-edit the output:
change the JSON and rebuild. The build stops on any schema error.
"""
import json, re, sys, os, base64, html, tarfile, io, subprocess, argparse, datetime, pathlib

KIT = pathlib.Path(__file__).resolve().parent
CACHE = KIT / '.cache'
PAGES = ['silabo', 'resumo', 'revisao', 'testes', 'mapa', 'plano']

def enabled(page, F):
    """plano, mapa and testes are optional pages (features.plan / features.map / features.tests)."""
    return {'plano': F.get('plan'), 'mapa': F.get('map'), 'testes': F.get('tests')}.get(page, True)
KATEX_V = '0.16.9'
MATHJS_V = '12.4.1'
CDN = 'https://cdnjs.cloudflare.com/ajax/libs'
MATRIX_RE = re.compile(r'\\begin\{(p|b|B|v|V)?matrix\}|\\begin\{array\}|\\begin\{cases\}')

WARNINGS = []

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
    mp = json.load(open(d / 'map.json', encoding='utf-8')) if (d / 'map.json').exists() else None
    ts = json.load(open(d / 'tests.json', encoding='utf-8')) if (d / 'tests.json').exists() else None
    validate(pack, topics, plan)
    if pack['features'].get('tests'):
        if ts is None:
            fail('features.tests is on but tests.json is missing (run tests.py, then write the questions)')
        validate_tests(ts, pack)
    if pack['features'].get('map'):
        if mp is None:
            fail('features.map is on but map.json is missing (see SCHEMA.md › map.json)')
        validate_map(mp, pack)
    return pack, topics, plan, mp, ts

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
        for where, blocks in (('resumo', tp.get('resumo', [])), ('lesson', tp.get('lesson', []))):
            for b in blocks:
                if b.get('kind', 'p') not in BLOCK_KINDS:
                    fail(f'topic {n}: unknown block kind {b.get("kind")}')
                validate_block(b, n, where)
        if tp.get('resumo'):
            w = sum(words(b.get('body')) + words(b.get('explain')) for b in tp['resumo'])
            if w < MIN_WORDS['resumo']:
                fail(f'topic {n}: the Resumo explanation has {w} words; write at least {MIN_WORDS["resumo"]} (explain every notion, see SKILL.md › Explanations)')
        if tp.get('lesson'):
            w = sum(words(b.get('body')) + words(b.get('explain')) for b in tp['lesson'])
            if w < MIN_WORDS['lesson'] or not any(b.get('kind', 'p') == 'p' for b in tp['lesson']):
                fail(f'topic {n}: the Revisão lesson needs at least one explanation paragraph and {MIN_WORDS["lesson"]} words (has {w})')
        for x in tp.get('examples', []) + ([tp['worked']] if tp.get('worked') else []):
            validate_solution(x, f'topic {n}: example "{x.get("title", "?")}"')
        for e in tp.get('exercises', []):
            validate_exercise(e, f'topic {n}', seen)
    if pack['features'].get('plan') and plan is None:
        fail('features.plan is on but plan.json is missing (run plan.py)')

# ---- content quality gate (points that make a page understandable, not just short)
BLOCK_KINDS = ('p', 'def', 'thm', 'formula', 'method', 'trap', 'bookerr', 'note')
EXPLAIN_KINDS = {'resumo': ('def', 'thm', 'formula', 'method'), 'lesson': ('def', 'thm', 'formula')}
MIN_WORDS = {'resumo': 180, 'lesson': 70, 'explain': 12, 'method': 8, 'why': 3, 'mcqwhy': 6}

def words(s):
    """Word count; every $…$ formula counts as two words (it carries content)."""
    s = re.sub(r'\$\$.+?\$\$|\$[^$]+\$', ' F F ', str(s or ''), flags=re.S)
    return len(re.findall(r'[\w’\'-]+', s))

def validate_block(b, n, where):
    if b.get('kind', 'p') in EXPLAIN_KINDS[where] and words(b.get('explain')) < MIN_WORDS['explain']:
        fail(f'topic {n} ({where}): block "{b.get("title", b.get("kind"))}" needs "explain": what it means in plain words, why it is true or useful, when to use it (≥ {MIN_WORDS["explain"]} words)')

def validate_steps(steps, where, minimum=2):
    if len(steps or []) < minimum:
        fail(f'{where}: the resolution needs at least {minimum} steps, each one written out')
    for i, s in enumerate(steps, 1):
        if not str(s.get('do', '')).strip():
            fail(f'{where}: step {i} has no "do"')
        if words(s.get('why')) < MIN_WORDS['why']:
            fail(f'{where}: step {i} needs a "why" (the rule or idea that justifies it, ≥ {MIN_WORDS["why"]} words)')

def validate_solution(x, where):
    for k in ('title', 'statement', 'steps', 'answer', 'origin'):
        if k not in x:
            fail(f'{where} missing "{k}"')
    if words(x.get('method')) < MIN_WORDS['method']:
        fail(f'{where}: needs "method": how to recognise the type of problem and which method to choose, before the steps (≥ {MIN_WORDS["method"]} words)')
    validate_steps(x['steps'], where)
    if not str(x.get('answer', '')).strip():
        fail(f'{where}: empty answer')

def validate_exercise(e, where, seen, topics_ok=None):
    for k in ('id', 'type', 'q', 'origin', 'key'):
        if k not in e:
            fail(f'{where}: exercise {e.get("id","?")} missing "{k}"')
    if e['id'] in seen:
        fail(f'duplicate exercise id {e["id"]}')
    seen.add(e['id'])
    w = f'{where}: exercise {e["id"]}'
    if e['type'] not in ('mcq', 'tf', 'free'):
        fail(f'{w}: type must be mcq, tf or free')
    if e['type'] == 'mcq':
        if len(e.get('options', [])) != 4:
            fail(f'{w}: mcq needs exactly 4 options')
        if len(e.get('why', [])) != 4:
            fail(f'{w}: mcq needs 4 "why" lines (one per option)')
        if not isinstance(e.get('correct'), int) or not 0 <= e['correct'] < 4:
            fail(f'{w}: correct must be 0..3')
        for i, y in enumerate(e['why']):
            if words(y) < MIN_WORDS['mcqwhy']:
                fail(f'{w}: "why" of option {"ABCD"[i]} is too short: say why it is right, or which mistake leads to it')
    if e['type'] == 'tf' and e.get('correct') not in (0, 1):
        fail(f'{w}: tf correct must be 0 (true) or 1 (false)')
    key = e['key']
    if words(key.get('method')) < MIN_WORDS['method']:
        fail(f'{w}: key needs "method": how you should have attacked it (what to notice in the statement, which method, why) (≥ {MIN_WORDS["method"]} words)')
    validate_steps(key.get('steps'), w, 1 if e['type'] == 'tf' else 2)
    if not str(key.get('answer', '')).strip():
        fail(f'{w}: key needs the final "answer"')
    if topics_ok is not None and e.get('topic') not in topics_ok:
        fail(f'{w}: "topic" must be one of the test topics {sorted(topics_ok)}')

def validate_tests(ts, pack):
    """tests.json: daily tests (from the plan), tests on a few topics, full mock tests."""
    if not isinstance(ts.get('tests'), list) or not ts['tests']:
        fail('tests.json: "tests" must be a non-empty list (run tests.py, then fill the questions)')
    allt = {t['n'] for t in pack['topics']}; ids = set(); seen = set()
    for t in ts['tests']:
        for k in ('id', 'kind', 'title', 'topics', 'need', 'questions'):
            if k not in t:
                fail(f'tests.json: test {t.get("id", "?")} missing "{k}"')
        if t['id'] in ids:
            fail(f'tests.json: duplicate test id {t["id"]}')
        ids.add(t['id'])
        if t['kind'] not in ('daily', 'topics', 'mock'):
            fail(f'tests.json: test {t["id"]}: kind must be daily, topics or mock')
        tp = set(t['topics'])
        if not tp or not tp <= allt:
            fail(f'tests.json: test {t["id"]}: topics {t["topics"]} must be topic numbers of the pack')
        if len(t['questions']) < t['need']:
            fail(f'tests.json: test {t["id"]} has {len(t["questions"])} of {t["need"]} questions: write the missing ones')
        for q in t['questions']:
            validate_exercise(q, f'tests.json › {t["id"]}', seen, tp)
        if t['kind'] != 'daily' or len(tp) > 1:
            missing = tp - {q['topic'] for q in t['questions']}
            if missing:
                fail(f'tests.json: test {t["id"]}: no question on topic(s) {sorted(missing)}')

def validate_map(mp, pack):
    """map.json: generic knowledge map. Same checks whatever the course (history, maths, biology, code…)."""
    for k in ('kind', 'layout', 'groups', 'nodes', 'edges'):
        if k not in mp:
            fail(f'map.json: missing "{k}"')
    if mp['kind'] not in ('causal', 'prereq', 'process'):
        fail('map.json: kind must be causal, prereq or process')
    if mp['layout'] not in ('timeline', 'layers'):
        fail('map.json: layout must be timeline or layers')
    gs = [g['id'] for g in mp['groups']]
    if not 1 <= len(gs) <= 5 or len(set(gs)) != len(gs):
        fail('map.json: 1 to 5 groups with unique ids (they get the 5 theme colours)')
    ids = [n['id'] for n in mp['nodes']]
    if len(set(ids)) != len(ids):
        fail('map.json: duplicate node id')
    if not 6 <= len(ids) <= 80:
        fail(f'map.json: {len(ids)} nodes; use 6 to 80 (split bigger maps by chapter)')
    cols = {c['id'] for c in mp.get('cols', [])}
    if mp['layout'] == 'timeline' and not cols:
        fail('map.json: layout "timeline" needs "cols" (ordered columns) and a "col" on every node')
    topics = {t['n'] for t in pack['topics']}
    for n in mp['nodes']:
        for k in ('id', 'group', 'label', 'text', 'ctx', 'what', 'keys'):
            if not n.get(k):
                fail(f'map.json: node {n.get("id", "?")} missing "{k}"')
        if n['group'] not in gs:
            fail(f'map.json: node {n["id"]} has unknown group {n["group"]}')
        if mp['layout'] == 'timeline' and n.get('col') not in cols:
            fail(f'map.json: node {n["id"]} has unknown col {n.get("col")}')
        if n.get('topic') is not None and n['topic'] not in topics:
            fail(f'map.json: node {n["id"]} points to unknown topic {n["topic"]}')
        if '$' in n['label']:
            fail(f'map.json: node {n["id"]}: no maths in the label (cards are plain text); put it in text/what/keys')
        if len(n['label']) > 40:
            fail(f'map.json: node {n["id"]} label is longer than 40 characters (cards are small)')
        if not isinstance(n['ctx'], str) or not isinstance(n['text'], str) or not isinstance(n.get('hook', ''), str) or not isinstance(n.get('pages', ''), str):
            fail(f'map.json: node {n["id"]}: ctx, text, hook and pages are strings (not lists)')
        if not isinstance(n['what'], list) or not isinstance(n['keys'], list):
            fail(f'map.json: node {n["id"]}: "what" and "keys" must be lists')
        for t in n.get('terms', []):
            if 't' not in t or 'd' not in t:
                fail(f'map.json: node {n["id"]}: terms are {{"t","d"}}')
    S = set(ids); seen = set(); out = {i: [] for i in ids}
    for e in mp['edges']:
        for k in ('a', 'b', 'why'):
            if not e.get(k):
                fail(f'map.json: edge {e} missing "{k}"')
        if e['a'] not in S or e['b'] not in S or e['a'] == e['b']:
            fail(f'map.json: bad edge {e["a"]} -> {e["b"]}')
        if (e['a'], e['b']) in seen:
            fail(f'map.json: duplicate edge {e["a"]} -> {e["b"]}')
        seen.add((e['a'], e['b'])); out[e['a']].append(e['b'])
    if mp['layout'] == 'timeline':
        order = {c['id']: i for i, c in enumerate(mp['cols'])}
        byid = {n['id']: n for n in mp['nodes']}
        for e in mp['edges']:
            if order[byid[e['a']]['col']] > order[byid[e['b']]['col']]:
                fail(f'map.json: edge {e["a"]} -> {e["b"]} goes backwards in time (check the columns)')
    # no cycles (a cause cannot come from its own effect)
    state = {}
    def dfs(x):
        state[x] = 1
        for y in out[x]:
            if state.get(y) == 1:
                fail(f'map.json: cycle through {x} -> {y}')
            if y not in state:
                dfs(y)
        state[x] = 2
    for i in ids:
        if i not in state:
            dfs(i)
    linked = {e['a'] for e in mp['edges']} | {e['b'] for e in mp['edges']}
    lone = [i for i in ids if i not in linked]
    if lone:
        WARNINGS.append(f'map.json: nodes with no edge at all (fine only if they really link to nothing): {lone}')
    for r in mp.get('routes', []):
        if len(r.get('nodes', [])) < 2 or not r.get('name'):
            fail('map.json: a route needs a name and at least 2 nodes')
        for x, y in zip(r['nodes'], r['nodes'][1:]):
            if (x, y) not in seen:
                fail(f'map.json: route "{r["name"]}": {x} -> {y} is not an edge')
    if not mp.get('routes'):
        fail('map.json: at least one route is needed (the "Rotas" tab)')
    for x in mp.get('eras', []):
        if mp['layout'] != 'timeline' or x.get('col') not in cols:
            fail(f'map.json: era {x} must point to a column of a timeline')

# ---------------------------------------------------------------- text
class Ctx:
    def __init__(self, pack, page, S):
        self.pack, self.page, self.S = pack, page, S
        self.prefix = {'silabo': 't', 'resumo': 'r', 'revisao': 'ch', 'testes': 'x', 'mapa': 'm', 'plano': 'd'}[page]

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

def header(pack, page, S, mapkind='causal'):
    F = pack['features']
    cur = ' aria-current="page"'
    nav = ''.join(
        f'<a href="{a(pack["urls"].get(p, "") or "#")}"{cur if p == page else ""}>{S["page"][p]}</a>'
        for p in PAGES if enabled(p, F))
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
    if page == 'testes':
        tools.append(f'<button type="button" class="btn" id="todayBtn">{S["today"]}</button>')
    if page == 'plano':
        tools.append(f'<button type="button" class="btn" id="origBtn" aria-pressed="false">{S["plan"]["origBtn"]}</button>')
        tools.append(f'<button type="button" class="btn" id="todayBtn">{S["today"]}</button>')
        tools.append(f'<button type="button" class="btn" id="hideDoneBtn" aria-pressed="false">{S["hideDone"]}</button>')
    if page not in ('plano', 'mapa', 'testes'):
        tools.append(f'<button type="button" class="btn" id="notesBtn">{S["notes"]}<span data-notecount></span></button>')
    tools.append(f'<button type="button" class="theme" id="themeBtn" aria-label="{a(S["themeAria"])}" title="{a(S["themeAria"])}">{MOON}{SUN}</button>')
    title = f'{S["pageLong"][page] if page != "mapa" else S["mapa"]["kinds"][mapkind]["title"]} — {pack["course"]}'
    strip = ''
    if page == 'revisao' and F.get('progress', True):
        strip = '<div class="overall"><div class="wrap"><span id="oText" class="mono"></span><div class="bar" aria-hidden="true"><i class="okb" id="oOk"></i><i class="badb" id="oBad"></i></div><span id="saved" class="saved"></span></div></div>'
    if page in ('plano', 'testes'):
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
    if page not in ('plano', 'mapa', 'testes'):
        out += (f'<div class="scrim" id="notesScrim" hidden></div><aside class="drawer" id="notesDrawer" hidden aria-label="{a(N["title"])}"><header><h3>{N["title"]}</h3><button type="button" class="btn sm" id="notesClose">{S["close"]}</button></header>'
                f'<div class="filters"><button type="button" class="btn sm" data-nf="all" aria-pressed="true">{N["all"]}</button><button type="button" class="btn sm" data-nf="mine" aria-pressed="false">{N["mine"]}</button><button type="button" class="btn sm" data-nf="q" aria-pressed="false">{N["q"]}</button></div>'
                f'<p class="hint" id="notesWhere"></p><ul class="dlist" id="notesList"></ul></aside>')
    if page not in ('plano', 'mapa', 'testes') and F.get('tutor', True):
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
    if b.get('explain'):
        body += f'<div class="plain{mtx(b["explain"])}"><b>{S["plain"]}</b> {md(b["explain"], cx)}</div>'
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

def howto(m, cx, S):
    return f'<div class="howto{mtx(m)}"><b>{S["howto"]}</b> {md(m, cx)}</div>' if m else ''

def checkline(c, cx, S):
    return f'<div class="check{mtx(c)}"><b>{S["check"]}</b> {md(c, cx)}</div>' if c else ''

def example_html(x, n, j, key, cx, pack, S, open_=False):
    num = f'{n}.{j}' if j else f'{n}'
    pb = plot_btn(x.get('plot'), pack, S)
    tutor = pack['features'].get('tutor', True)
    ask = f'<button type="button" class="btn sm ghost" data-ask="example" hidden>{S["tutor"]["ask"]}</button>' if tutor else ''
    return (f'<article class="xmp fblk" id="{key}" data-note="{key}" data-topic="{n}" data-label="{a(S["example"] + " " + num)}">'
            f'<div class="xh"><span class="xn mono">{num}</span><h4>{a(x["title"])}</h4><span class="src eyebrow">{a(origin_label(x, S))}</span><span class="nicon"></span></div>'
            f'<div class="xstmt prose{mtx(x["statement"])}">{md(x["statement"], cx)}</div>'
            f'<details class="sol"{" open" if open_ else ""}><summary>{S["showSolution"]}</summary>{howto(x.get("method"), cx, S)}{steps_html(x["steps"], cx, S)}'
            f'<div class="ans{mtx(x["answer"])}"><b>{S["result"]}</b> {md(x["answer"], cx)}</div>{checkline(x.get("check"), cx, S)}</details>'
            f'<div class="xact">{ask}{pb}</div><div class="nslot"></div></article>')

MAPTOPICS = set()

def maplink(pack, n, S):
    """'See on the map' link, only when the Mapa page is on and topic n has cards in it."""
    u = pack['urls'].get('mapa')
    return [(f'{u}#t{n}', S['mapa']['seeOnMap'])] if pack['features'].get('map') and u and n in MAPTOPICS else []

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
                    + xlinks([(f'{U["resumo"]}#r{n}', S['readAll'].format(n=n)), (f'{U["revisao"]}#ch{n}', S['practice'].format(n=n))] + maplink(pack, n, S))
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
        links = [(f'{U["silabo"]}#t{n}', S['essential'].format(n=n)), (f'{U["revisao"]}#ch{n}', S['practice'].format(n=n))] + maplink(pack, n, S)
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

def exercise_html(e, n, j, cx, pack, S, test=False):
    eid = e['id']; typ = e['type']
    key = e['key']
    keyh = (f'<div class="key" hidden><h5>{S["keyTitle"]}</h5>{howto(key.get("method"), cx, S)}{steps_html(key.get("steps", []), cx, S)}'
            + (f'<div class="ans{mtx(key.get("answer"))}"><b>{S["result"]}</b> {md(key["answer"], cx)}</div>' if key.get('answer') else '')
            + checkline(key.get('check'), cx, S)
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
        body += free_box(eid, S, not test) + keyh
    tutor = pack['features'].get('tutor', True) and not test
    ask = f'<button type="button" class="btn sm ghost" data-ask="ex" hidden>{S["tutor"]["ask"]}</button>' if tutor else ''
    pb = plot_btn(e.get('plot'), pack, S)
    corr = f' data-correct="{e["correct"]}"' if typ in ('mcq', 'tf') else ''
    num = f'{j}' if test else f'{n}.{j}'
    src = f'{S["topic"]} {n} · {pack["topics"][n - 1]["name"]}' if test else origin_label(e, S)
    lbl = f'{num} · {src}'
    note = '' if test else f' data-note="{eid}"'
    return (f'<article class="ex {typ}{"" if test else " fblk"}" id="{eid}" data-id="{eid}" data-n="{n}"{corr}{note} data-topic="{n}" data-label="{a(lbl)}">'
            f'<div class="exhead"><span class="exn mono">{num}</span><span class="src eyebrow">{a(src)}</span><span class="badge" hidden></span><span class="nicon"></span></div>'
            f'<div class="q prose{mtx(e["q"])}">{md(e["q"], cx)}</div>{body}<div class="xact">{ask}{pb}</div>' + ('' if test else f'<button type="button" class="btn redo sm" hidden>{S["redo"]}</button>') + '<div class="nslot"></div></article>')

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
                    + xlinks([(f'{U["resumo"]}#r{n}', S['fullVersion'].format(n=n)), (f'{U["silabo"]}#t{n}', S['essential'].format(n=n))] + maplink(pack, n, S))
                    + prog + '<div class="nslot"></div>'
                    + f'<div class="lesson">{blocks}</div>{wk}<h3 class="exh fblk">{S["yourExercises"] if pack.get("exercise", {}).get("source") == "mine" else S["exercises"]}</h3>{shortage}<div class="exs">{exh}</div></section>')
    intro = f'<div class="intro"><p class="hint">{a(S["intro"]["revisao"])}</p><p class="hint">{a(S["intro"]["notesHint"])}</p><p class="hint" id="chatOff" hidden>{a(S["tutor"]["off"])}</p></div>'
    empty = f'<p class="empty" id="emptyMiss">{a(S["emptyMiss"])}</p>'
    return f'<div class="wrap layout">{rail(pack, "revisao", S)}<main>{intro}{empty}{"".join(secs)}</main></div>'

def page_mapa(pack, mp, S):
    M = S['mapa']; K = M['kinds'][mp['kind']]
    GM = ['●', '■', '▲', '◆', '★']
    legend = ''.join(f'<span class="s g{i}"><span class="mp-gm" aria-hidden="true">{GM[i]}</span>{a(g["name"])}</span>' for i, g in enumerate(mp['groups'])) if len(mp['groups']) > 1 else ''
    eras = f'<div class="mp-eras" id="mpEras"><span class="mp-lbl">{a(M["jump"])}</span></div>' if mp.get('eras') else ''
    tabs = ''.join(f'<button type="button" class="btn" data-act="mode" data-tab data-m="{k}" aria-pressed="{"true" if k == "map" else "false"}">{a(M["tabs"][k])}</button>' for k in ('map', 'routes', 'train'))
    return (f'<main class="wrap mp"><div class="mp-main"><div class="mp-vwrap"><div class="mp-tabs" role="group" aria-label="{a(K["title"])}">{tabs}</div>{eras}' + (f'<div class="mp-legend" aria-label="{a(M["legend"])}">{legend}</div>' if legend else '') +
            f'<div id="mpVp" tabindex="0" role="application" aria-label="{a(K["title"])}"><div id="mpWorld"></div>'
            f'<div class="mp-ctl"><button type="button" class="btn" data-act="zin" aria-label="{a(M["zoomIn"])}">+</button><button type="button" class="btn" data-act="zout" aria-label="{a(M["zoomOut"])}">−</button><button type="button" class="btn" data-act="fit" aria-label="{a(M["fit"])}" title="{a(M["fit"])}">⤢</button></div></div></div>'
            f'<aside class="mp-panel" id="mpPanel" aria-live="polite"></aside></div></main>')

def fmt_day(iso, lang):
    y, m, d = map(int, iso.split('-'))
    return f'{d} {MONTHS[lang][m - 1]}'

def page_testes(pack, ts, S, cx):
    X = S['tests']; U = pack['urls']
    groups = {'daily': [], 'topics': [], 'mock': []}
    for t in ts['tests']:
        tps = ', '.join(str(n) for n in t['topics'])
        meta = [fmt_day(t['date'], pack['lang'])] if t.get('date') else []
        meta += [X['topicsLbl'].format(t=tps), X['nq'].format(n=len(t['questions']))]
        if t.get('minutes'):
            meta.append(X['mins'].format(m=t['minutes']))
        qs = ''.join(exercise_html(q, q['topic'], j + 1, cx, pack, S, test=True) for j, q in enumerate(t['questions']))
        links = ''.join(f'<a href="{a(U["revisao"])}#ch{n}">{a(S["page"]["revisao"])} {n}</a>' for n in t['topics'])
        groups[t['kind']].append(
            f'<article class="tst" id="{a(t["id"])}" data-test="{a(t["id"])}" data-kind="{t["kind"]}" data-topics="{",".join(map(str, t["topics"]))}"' + (f' data-date="{t["date"]}"' if t.get('date') else '') + '>'
            f'<div class="tsth"><div class="tstt"><h3>{a(t["title"])}</h3><span class="eyebrow">{a(" · ".join(meta))}</span></div>'
            f'<span class="tscore mono" hidden></span><button type="button" class="btn tstart">{X["start"]}</button></div>'
            f'<div class="tstbody" hidden><p class="hint">{a(X["howTo"])}</p><div class="exs">{qs}</div>'
            f'<div class="tacts"><button type="button" class="btn solid tfinish">{X["finish"]}</button><button type="button" class="btn tredo" hidden>{X["redo"]}</button></div>'
            f'<div class="tresult" hidden></div><div class="xlinks">{links}</div></div></article>')
    secs = ''
    for k in ('daily', 'topics', 'mock'):
        if groups[k]:
            secs += f'<section class="tsec" id="sec-{k}"><h2>{X["sec"][k]}</h2><p class="sub">{X["secSub"][k]}</p><div class="tlist">{"".join(groups[k])}</div></section>'
    return f'<main class="wrap tmain"><div class="intro"><p class="hint">{a(X["intro"])}</p><p class="hint" id="gradeOff" hidden>{a(X["gradeOff"])}</p></div>{secs}</main>'

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
            + ''.join(f'<span><i style="background:{c}"></i>{P["act"][k]}</span>' for k, c in (('learn', 'var(--accent)'), ('ex', 'var(--accent2)'), ('rev', 'var(--warn)'), ('quiz', 'var(--ok)'), ('test', 'var(--bad)')) if k != 'quiz' or pack['features'].get('tests'))
            + f'</div><div class="scroll" id="bars"></div></div></section>'
            f'<section><h2>{P["timelineTitle"]}</h2><p class="sub">{P["timelineSub"]}</p><div class="panel"><div class="scroll" id="timeline"></div></div></section>'
            f'<section><h2>{P["progTitle"]}</h2><p class="sub">{P["progSub"]}</p><div class="panel"><div class="scroll" id="prog"></div></div></section>'
            f'<section><h2>{P["daysTitle"]}</h2><p class="sub">{P["daysSub"]}</p><div class="adapt" id="adapt" hidden></div><div class="days" id="days"></div></section></main>')

# ---------------------------------------------------------------- assemble
def build(pack_dir, out_dir, pages=None):
    global MAPTOPICS
    pack, topics, plan, mp, ts = load_pack(pack_dir)
    MAPTOPICS = {n['topic'] for n in mp['nodes'] if n.get('topic') is not None} if mp else set()
    I18N = json.load(open(KIT / 'i18n.json', encoding='utf-8'))
    S = I18N[pack['lang']]
    F = pack['features']
    pages = pages or [p for p in PAGES if enabled(p, F)]
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    link, faces, family = font_block(pack['font'])
    css = theme_css(pack, family) + (KIT / 'assets' / 'core.css').read_text(encoding='utf-8')
    kcss = katex_css()
    mapa_css = (KIT / 'assets' / 'mapa.css').read_text(encoding='utf-8')
    core_js = (KIT / 'assets' / 'core.js').read_text(encoding='utf-8')
    store = pack.get('storage') or {}
    store = {'prefix': store.get('prefix', pack['slug'] + '-'), 'docs': store.get('docs', {}), 'ls': store.get('ls', {})}
    results = {}
    for page in pages:
        cx = Ctx(pack, page, S)
        head, title = header(pack, page, S, mp['kind'] if mp else 'causal')
        if page == 'silabo':
            body = page_silabo(pack, topics, S, cx); src = {str(n): {'syllabus': topics[n].get('syllabus', [])} for n in topics}
        elif page == 'resumo':
            body = page_resumo(pack, topics, S, cx); src = {str(n): {k: topics[n].get(k) for k in ('resumo', 'examples')} for n in topics}
        elif page == 'revisao':
            body = page_revisao(pack, topics, S, cx); src = {str(n): {k: topics[n].get(k) for k in ('lesson', 'worked', 'exercises', 'shortage')} for n in topics}
        elif page == 'mapa':
            body = page_mapa(pack, mp, S); src = mp
        elif page == 'testes':
            body = page_testes(pack, ts, S, cx); src = ts
        else:
            if not plan:
                fail('plano requested but plan.json missing')
            body = page_plano(pack, plan, S); src = plan
        packjs = {'page': page, 'title': title, 'course': pack['course'], 'short': pack['short'], 'lang': pack['lang'], 't': S,
                  'exam': pack.get('exam'), 'urls': pack['urls'], 'topics': {str(t['n']): t['name'] for t in pack['topics']},
                  'store': store, 'features': F,
                  'tests': [{'id': t['id'], 'kind': t['kind'], 'date': t.get('date'), 'topics': t['topics']} for t in ts['tests']] if ts and F.get('tests') else []}
        mapmath = page == 'mapa' and '$' in json.dumps(mp, ensure_ascii=False)   # maths only when the map uses it
        scripts = [] if page == 'mapa' and not mapmath else [f'{CDN}/KaTeX/{KATEX_V}/katex.min.js', f'{CDN}/KaTeX/{KATEX_V}/contrib/auto-render.min.js', f'{CDN}/KaTeX/{KATEX_V}/contrib/copy-tex.min.js']
        if F.get('calc') and page in ('resumo', 'revisao'):
            scripts.append(f'{CDN}/mathjs/{MATHJS_V}/math.min.js')
        page_js = (KIT / 'assets' / f'{page}.js').read_text(encoding='utf-8') if page in ('revisao', 'plano', 'mapa', 'testes') else 'commonInit();'
        plan_js = f'const PLAN={js(plan)};' if page == 'plano' else ''
        config = {k: v for k, v in pack.items() if k != 'topics'}
        config.update({'topics': pack['topics'], 'page': page, 'built': datetime.date.today().isoformat(), 'kit': 'study-pack kit 3'})
        doc = (f'<!doctype html><html lang="{pack["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<meta name="claude:viewport-fit-sides" content="cover"><title>{a(title)}</title>'
               f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{link}{faces}'
               f'<style>{kcss if page != "mapa" or mapmath else ""}</style><style>{css}{mapa_css if page == "mapa" else ""}</style></head><body class="p-{page}">'
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
    for w in WARNINGS:
        print('WARNING:', w)
