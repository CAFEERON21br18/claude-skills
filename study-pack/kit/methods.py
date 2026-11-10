"""study-pack kit — method parts: one block per study method, validated and rendered by build.py.

pack.json › "methods": {"learning": ["active_recall", "feynman", …], "time": "pomodoro", "hansei": true}
topics/<n>.json › "parts": {"<method>": {…}}   (shapes in SCHEMA.md › Method parts)

Every learning method listed in pack.methods needs its part in every topic (interleaving: from topic 2).
"""
import json, re

LEARNING = ['active_recall', 'spaced', 'learning_by_doing', 'kumon', 'worked_examples', 'shuhari',
            'problem_first', 'interleaving', 'feynman', 'mindmap', 'sq3r', 'cornell']
TIME = ['pomodoro', 'kaizen', 'finnish']
LEGACY = {'blurting': 'active_recall', 'flowtime': None, 'long': None, 'flashcards': None}
# where each part is drawn: Resumo top / Resumo end / Revisão before the lesson / Revisão after the lesson
WHERE = {'sq3r': 'resumo', 'cornell': 'resumo', 'mindmap': 'both', 'active_recall': 'revisao-top', 'problem_first': 'revisao-top'}


def norm_methods(pack):
    """pack.methods with legacy names folded in, unknown names refused. None when the pack has no methods."""
    m = pack.get('methods')
    if not m:
        return None
    out = []
    for x in m.get('learning', []):
        x = LEGACY.get(x, x)
        if x is None:
            continue
        if x not in LEARNING:
            raise ValueError(f'pack.json › methods.learning: unknown method "{x}" (use one of {", ".join(LEARNING)})')
        if x not in out:
            out.append(x)
    t = m.get('time')
    if t and LEGACY.get(t, t) not in TIME and t not in LEGACY:
        raise ValueError(f'pack.json › methods.time: unknown time method "{t}" (use one of {", ".join(TIME)})')
    return {'learning': out, 'time': t if t in TIME else None, 'hansei': bool(m.get('hansei'))}


# ---------------------------------------------------------------- validation
def validate_parts(pack, topics, words, validate_exercise, validate_solution, fail, seen):
    M = norm_methods(pack)
    if not M:
        return
    for t in pack['topics']:
        n = t['n']; tp = topics[n]; P = tp.get('parts') or {}
        for m in M['learning']:
            if m == 'interleaving' and n == 1:
                continue
            if m not in P and m != 'learning_by_doing':
                fail(f'topic {n}: method "{m}" is on in pack.json but topics/{n}.json › parts.{m} is missing (see SCHEMA.md › Method parts)')
            CHECK[m](P.get(m), n, tp, words, lambda e, w: validate_exercise(e, w, seen), validate_solution, fail)
        for m in P:
            if m not in LEARNING and m != 'hansei':
                fail(f'topic {n}: unknown part "{m}"')


def need(cond, fail, msg):
    if not cond:
        fail(msg)


def qa_list(xs, n, where, k, fail):
    need(isinstance(xs, list) and len(xs) >= k, fail, f'topic {n}: parts.{where} needs at least {k} question/answer pairs')
    for i, x in enumerate(xs, 1):
        need(str(x.get('q', '')).strip() and str(x.get('a', '')).strip(), fail, f'topic {n}: parts.{where} item {i} needs "q" and "a"')


def c_active_recall(p, n, tp, words, vex, vsol, fail):
    qa_list(p.get('questions'), n, 'active_recall.questions', 4, fail)
    need(len(p.get('keys', [])) >= 3, fail, f'topic {n}: parts.active_recall.keys needs at least 3 key points (to compare the "write what you remember" page against)')


def c_spaced(p, n, tp, words, vex, vsol, fail):
    qa_list(p.get('quick'), n, 'spaced.quick', 4, fail)


def c_learning_by_doing(p, n, tp, words, vex, vsol, fail):
    lv = {e.get('level') for e in tp.get('exercises', [])}
    need({1, 2, 3} <= lv, fail, f'topic {n}: learning by doing needs graded exercises: give every exercise a "level" 1, 2 or 3 and have at least one of each (has {sorted(x for x in lv if x)})')


def c_kumon(p, n, tp, words, vex, vsol, fail):
    need(isinstance(p, list) and 3 <= len(p) <= 5, fail, f'topic {n}: parts.kumon is a list of 3–5 levels, each a list of exercises')
    for i, lvl in enumerate(p, 1):
        need(isinstance(lvl, list) and len(lvl) >= 3, fail, f'topic {n}: Kumon level {i} needs at least 3 short exercises')
        for e in lvl:
            vex(e, f'topic {n} (Kumon level {i})')


def c_worked_examples(p, n, tp, words, vex, vsol, fail):
    need(isinstance(p, list) and len(p) >= 2, fail, f'topic {n}: parts.worked_examples needs at least 2 pairs {{"example", "twin"}}')
    for i, x in enumerate(p, 1):
        vsol(x.get('example', {}), f'topic {n}: worked example {i}')
        vex(x.get('twin', {}), f'topic {n} (twin of worked example {i})')


def c_shuhari(p, n, tp, words, vex, vsol, fail):
    for st in ('shu', 'ha', 'ri'):
        need(len(p.get(st, [])) >= 1, fail, f'topic {n}: parts.shuhari.{st} needs at least 1 exercise')
        for e in p[st]:
            vex(e, f'topic {n} (Shuhari {st})')
    for e in p['shu']:
        need(len(e.get('hints', [])) >= 2, fail, f'topic {n}: Shu exercise {e.get("id")} needs "hints": the model steps to follow (≥ 2)')
    for e in p['ri']:
        need(e.get('type') == 'free', fail, f'topic {n}: Ri exercise {e.get("id")} must be "free" (an open problem)')


def c_problem_first(p, n, tp, words, vex, vsol, fail):
    e = p.get('starter', {})
    vex(e, f'topic {n} (starter problem)')
    need(len(e.get('hints', [])) >= 2, fail, f'topic {n}: the starter problem needs at least 2 "hints"')
    need(words(p.get('compare')) >= 20, fail, f'topic {n}: parts.problem_first.compare needs ≥ 20 words: how the lesson solves the starter problem, compared with a first try')


def c_interleaving(p, n, tp, words, vex, vsol, fail):
    need(isinstance(p, list) and len(p) >= 4, fail, f'topic {n}: parts.interleaving needs at least 4 mixed exercises')
    ts = set()
    for e in p:
        vex(e, f'topic {n} (mixed set)')
        need(isinstance(e.get('topic'), int) and 1 <= e['topic'] <= n, fail, f'topic {n}: mixed exercise {e.get("id")} needs "topic" between 1 and {n}')
        ts.add(e['topic'])
    need(len(ts) >= 2 and n in ts, fail, f'topic {n}: the mixed set must mix this topic with at least one earlier topic')


def c_feynman(p, n, tp, words, vex, vsol, fail):
    need(words(p.get('task')) >= 8, fail, f'topic {n}: parts.feynman.task needs the explain-it task (≥ 8 words)')
    need(len(p.get('checklist', [])) >= 4, fail, f'topic {n}: parts.feynman.checklist needs at least 4 points a good explanation covers')


def c_mindmap(p, n, tp, words, vex, vsol, fail):
    br = p.get('branches', [])
    need(str(p.get('center', '')).strip(), fail, f'topic {n}: parts.mindmap needs "center"')
    need(len(br) >= 3 and all(len(b.get('leaves', [])) >= 2 and b.get('label') for b in br), fail, f'topic {n}: parts.mindmap needs ≥ 3 branches, each with a "label" and ≥ 2 "leaves"')
    bl = p.get('blanks', [])
    need(len(bl) >= 3, fail, f'topic {n}: parts.mindmap.blanks needs ≥ 3 [branch, leaf] positions to hide in "complete the map"')
    for b in bl:
        need(isinstance(b, list) and len(b) == 2 and 0 <= b[0] < len(br) and 0 <= b[1] < len(br[b[0]]['leaves']), fail, f'topic {n}: parts.mindmap.blanks has a bad position {b}')


def c_sq3r(p, n, tp, words, vex, vsol, fail):
    need(words(p.get('survey')) >= 20, fail, f'topic {n}: parts.sq3r.survey needs the overview (≥ 20 words)')
    need(len(p.get('questions', [])) >= 3, fail, f'topic {n}: parts.sq3r.questions needs ≥ 3 guiding questions')
    need(len(p.get('recap', [])) >= 3, fail, f'topic {n}: parts.sq3r.recap needs ≥ 3 points (the answers to the guiding questions)')


def c_cornell(p, n, tp, words, vex, vsol, fail):
    cs = p.get('cues', [])
    need(len(cs) >= 4 and all(c.get('cue') and c.get('note') for c in cs), fail, f'topic {n}: parts.cornell.cues needs ≥ 4 {{"cue", "note"}} rows')
    need(words(p.get('summary')) >= 25, fail, f'topic {n}: parts.cornell.summary needs ≥ 25 words')


CHECK = {'active_recall': c_active_recall, 'spaced': c_spaced, 'learning_by_doing': c_learning_by_doing, 'kumon': c_kumon,
         'worked_examples': c_worked_examples, 'shuhari': c_shuhari, 'problem_first': c_problem_first, 'interleaving': c_interleaving,
         'feynman': c_feynman, 'mindmap': c_mindmap, 'sq3r': c_sq3r, 'cornell': c_cornell}


# ---------------------------------------------------------------- rendering
class R:
    """Rendering helpers handed over by build.py (md, a, mtx, exercise_html, example_html)."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def box(cls, title, sub, inner, n, key, S, r):
    lbl = f'{title} · {S["topic"]} {n}'
    return (f'<section class="mpart {cls} fblk" id="{key}" data-note="{key}" data-topic="{n}" data-label="{r.a(lbl)}">'
            f'<div class="mph"><span class="eyebrow">{r.a(S["methods"]["eyebrow"])}</span><h3>{r.a(title)}</h3>'
            + (f'<p class="hint">{r.a(sub)}</p>' if sub else '') + f'<span class="nicon"></span></div>{inner}<div class="nslot"></div></section>')


def qa_html(xs, cx, r, S):
    return '<ol class="qa">' + ''.join(
        f'<li><div class="qq prose{r.mtx(x["q"])}">{r.md(x["q"], cx)}</div><details class="qd"><summary>{S["methods"]["showAnswer"]}</summary>'
        f'<div class="prose{r.mtx(x["a"])}">{r.md(x["a"], cx)}</div></details></li>' for x in xs) + '</ol>'


def pad(key, S, r, ph=None, rows=6):
    return (f'<label class="lbl" for="pad-{key}">{r.a(S["methods"]["yourPage"])}</label>'
            f'<textarea class="mpad" id="pad-{key}" data-pad="{key}" rows="{rows}" placeholder="{r.a(ph or S["methods"]["padPh"])}"></textarea>')


def ul(items, cx, r, cls='prose'):
    return f'<ul class="{cls}">' + ''.join(f'<li class="{r.mtx(x)}">{r.inline(x, cx)}</li>' for x in items) + '</ul>'


def exs(lst, n, prefix, cx, pack, S, r):
    return '<div class="exs">' + ''.join(r.exercise_html(e, n, j + 1, cx, pack, S, num=f'{prefix}{j + 1}') for j, e in enumerate(lst)) + '</div>'


def mindmap_html(p, cx, r, S, blanks=None):
    hide = {tuple(b) for b in (blanks or [])}
    out = []
    for i, b in enumerate(p['branches']):
        lv = ''
        for j, leaf in enumerate(b['leaves']):
            if (i, j) in hide:
                lv += (f'<li class="mblank"><input type="text" class="mfill" aria-label="{r.a(S["methods"]["fillAria"].format(b=b["label"]))}" data-ans="{r.a(re.sub(r"[$*]", "", leaf))}">'
                       f'<span class="mans{r.mtx(leaf)}" hidden>{r.inline(leaf, cx)}</span></li>')
            else:
                lv += f'<li class="{r.mtx(leaf)}">{r.inline(leaf, cx)}</li>'
        out.append(f'<div class="mbr g{i % 5} {"ml" if i % 2 == 0 else "mr"}"><div class="mbl{r.mtx(b["label"])}">{r.inline(b["label"], cx)}</div><ul>{lv}</ul></div>')
    n = len(p['branches'])
    return (f'<div class="mmap" style="--rows:{(n + 1) // 2}"><svg class="mlinks" aria-hidden="true" focusable="false"></svg>'
            f'<div class="mctr{r.mtx(p["center"])}">{r.inline(p["center"], cx)}</div><div class="mbrs">{"".join(out)}</div></div>')


def resumo_top(pack, tp, n, cx, S, r):
    """Parts drawn before the Resumo explanation (SQ3R survey + questions)."""
    M = norm_methods(pack); P = tp.get('parts') or {}; L = S['methods']
    if not M or 'sq3r' not in M['learning'] or 'sq3r' not in P:
        return ''
    p = P['sq3r']
    inner = (f'<div class="sq"><b>{L["sq3r"]["s"]}</b><div class="prose{r.mtx(p["survey"])}">{r.md(p["survey"], cx)}</div></div>'
             f'<div class="sq"><b>{L["sq3r"]["q"]}</b>{ul(p["questions"], cx, r)}</div><p class="hint">{r.a(L["sq3r"]["read"])}</p>')
    return box('m-sq3r', L['sq3r']['title'], L['sq3r']['sub'], inner, n, f'r{n}-sq3r', S, r)


def resumo_end(pack, tp, n, cx, S, r):
    """Parts drawn after the Resumo explanation (Cornell, mind map, SQ3R recite + review)."""
    M = norm_methods(pack); P = tp.get('parts') or {}; L = S['methods']; out = ''
    if not M:
        return ''
    on = lambda m: m in M['learning'] and m in P
    if on('cornell'):
        p = P['cornell']
        rows = ''.join(f'<tr><th scope="row" class="{r.mtx(c["cue"])}">{r.inline(c["cue"], cx)}</th><td><button type="button" class="cnote{r.mtx(c["note"])}">{r.inline(c["note"], cx)}</button></td></tr>' for c in p['cues'])
        inner = (f'<div class="xact"><button type="button" class="btn sm ctog" aria-pressed="false">{L["cornell"]["cover"]}</button></div>'
                 f'<table class="cornell"><thead><tr><th scope="col">{L["cornell"]["cues"]}</th><th scope="col">{L["cornell"]["notes"]}</th></tr></thead><tbody>{rows}</tbody></table>'
                 f'<div class="csum"><b>{L["cornell"]["summary"]}</b><div class="prose{r.mtx(p["summary"])}">{r.md(p["summary"], cx)}</div></div>')
        out += box('m-cornell', L['cornell']['title'], L['cornell']['sub'], inner, n, f'r{n}-cornell', S, r)
    if on('mindmap'):
        out += box('m-mindmap', L['mindmap']['title'], L['mindmap']['sub'], mindmap_html(P['mindmap'], cx, r, S), n, f'r{n}-mindmap', S, r)
    if on('sq3r'):
        p = P['sq3r']
        inner = (f'<div class="sq"><b>{L["sq3r"]["r1"]}</b>{pad(f"r{n}-sq3r", S, r, L["sq3r"]["recitePh"])}</div>'
                 f'<details class="sq"><summary>{L["sq3r"]["r2"]}</summary>{ul(p["recap"], cx, r)}</details>')
        out += box('m-sq3r', L['sq3r']['end'], '', inner, n, f'r{n}-sq3r2', S, r)
    return out


def revisao_top(pack, tp, n, cx, S, r):
    """Parts drawn before the Revisão lesson: question-first (active recall) and the starter problem."""
    M = norm_methods(pack); P = tp.get('parts') or {}; L = S['methods']; out = ''
    if not M:
        return ''
    on = lambda m: m in M['learning'] and m in P
    if on('problem_first'):
        out += box('m-pf', L['pf']['title'], L['pf']['sub'], exs([P['problem_first']['starter']], n, 'P', cx, pack, S, r), n, f'ch{n}-pf', S, r)
    if on('active_recall'):
        p = P['active_recall']
        inner = (qa_html(p['questions'], cx, r, S) + f'<div class="sq"><b>{L["ar"]["blurt"]}</b>{pad(f"ch{n}-ar", S, r, L["ar"]["blurtPh"])}'
                 f'<details class="sq"><summary>{L["ar"]["compare"]}</summary>{ul(p["keys"], cx, r)}</details></div>')
        out += box('m-ar', L['ar']['title'], L['ar']['sub'], inner, n, f'ch{n}-ar', S, r)
    return out


def revisao_end(pack, tp, n, cx, S, r):
    """Parts drawn after the Revisão lesson and worked example, before the plain exercises."""
    M = norm_methods(pack); P = tp.get('parts') or {}; L = S['methods']; out = ''
    if not M:
        return ''
    on = lambda m: m in M['learning'] and m in P
    if on('problem_first'):
        c = P['problem_first']['compare']
        out += box('m-pf', L['pf']['back'], '', f'<div class="prose{r.mtx(c)}">{r.md(c, cx)}</div>', n, f'ch{n}-pf2', S, r)
    if on('worked_examples'):
        inner = ''.join(f'<div class="twin"><div class="xs">{r.example_html(x["example"], n, f"W{j + 1}", f"ch{n}-w{j + 1}", cx, pack, S, open_=True)}</div>'
                        f'<p class="hint twinh">{r.a(L["we"]["now"])}</p>{exs([x["twin"]], n, f"W{j + 1}′", cx, pack, S, r)}</div>' for j, x in enumerate(P['worked_examples']))
        out += box('m-we', L['we']['title'], L['we']['sub'], inner, n, f'ch{n}-we', S, r)
    if on('shuhari'):
        p = P['shuhari']
        inner = ''.join(f'<div class="stage"><h4>{L["sh"][st]}</h4><p class="hint">{r.a(L["sh"][st + "_b"])}</p>{exs(p[st], n, st.capitalize(), cx, pack, S, r)}</div>' for st in ('shu', 'ha', 'ri'))
        out += box('m-sh', L['sh']['title'], L['sh']['sub'], inner, n, f'ch{n}-sh', S, r)
    if on('kumon'):
        inner = ''.join(f'<div class="klevel" data-level="{i + 1}"><h4>{L["ku"]["level"].format(k=i + 1)}</h4><p class="klock hint" hidden>{r.a(L["ku"]["locked"])}</p>'
                        f'<div class="kbody">{exs(lvl, n, f"K{i + 1}.", cx, pack, S, r)}</div></div>' for i, lvl in enumerate(P['kumon']))
        out += box('m-ku', L['ku']['title'], L['ku']['sub'], inner, n, f'ch{n}-ku', S, r)
    if on('interleaving'):
        mixed = []
        for e in P['interleaving']:
            e = json.loads(json.dumps(e)); k = e.pop('topic')
            e['key']['method'] = f'**{S["topic"]} {k} · {pack["topics"][k - 1]["name"]}.** ' + e['key'].get('method', '')
            mixed.append(e)
        out += box('m-il', L['il']['title'], L['il']['sub'], exs(mixed, n, 'M', cx, pack, S, r), n, f'ch{n}-il', S, r)
    if on('mindmap'):
        p = P['mindmap']
        inner = mindmap_html(p, cx, r, S, p['blanks']) + f'<div class="xact"><button type="button" class="btn sm mcheck">{L["mindmap"]["check"]}</button></div>'
        out += box('m-mindmap', L['mindmap']['fill'], L['mindmap']['fill_b'], inner, n, f'ch{n}-mindmap', S, r)
    if on('feynman'):
        p = P['feynman']
        checks = ''.join(f'<li><label><input type="checkbox" data-chk="ch{n}-fy-{i}"> <span class="{r.mtx(c)}">{r.inline(c, cx)}</span></label></li>' for i, c in enumerate(p['checklist']))
        inner = (f'<div class="prose{r.mtx(p["task"])}">{r.md(p["task"], cx)}</div>{pad(f"ch{n}-fy", S, r, L["fy"]["ph"], 8)}'
                 f'<div class="sq"><b>{L["fy"]["check"]}</b><ul class="chk">{checks}</ul></div>')
        out += box('m-fy', L['fy']['title'], L['fy']['sub'], inner, n, f'ch{n}-fy', S, r)
    if on('spaced'):
        out += box('m-sp', L['sp']['title'], L['sp']['sub'], qa_html(P['spaced']['quick'], cx, r, S), n, f'ch{n}-sp', S, r)
    return out


def revisao_last(pack, tp, n, cx, S, r):
    """After the exercises: Hansei, the 2-minute reflection (pack.methods.hansei)."""
    M = norm_methods(pack); L = S['methods']
    if not M or not M['hansei']:
        return ''
    qs = L['hs']['q'] + list((tp.get('parts') or {}).get('hansei', []))
    inner = ''.join(f'<div class="sq"><b class="{r.mtx(q)}">{r.inline(q, cx)}</b><textarea class="mpad" rows="2" data-pad="ch{n}-hs-{i}" aria-label="{r.a(re.sub(r"[$*]", "", q))}"></textarea></div>' for i, q in enumerate(qs))
    return box('m-hs', L['hs']['title'], L['hs']['sub'], inner, n, f'ch{n}-hs', S, r)


def sort_graded(pack, exercises):
    """Learning by doing: plain exercises from level 1 to 3."""
    M = norm_methods(pack)
    if M and 'learning_by_doing' in M['learning']:
        return sorted(exercises, key=lambda e: e.get('level') or 9)
    return exercises
