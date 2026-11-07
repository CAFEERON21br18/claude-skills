#!/usr/bin/env python3
"""study-pack kit — make the skeleton of tests.json (the Testes page), consistent with the plan.

    python3 tests.py PACK_DIR

Writes tests.json with every test, its topics and how many questions it needs ("need"), and keeps
the questions already written for a test with the same id (safe to re-run after changing the plan).
Then write the questions (EXERCISE objects + "topic", see SCHEMA.md) and build.

Fixed rules:
- daily  "d<YYYY-MM-DD>": one per plan day that has a "quiz" session, on that day's topics.
         2 questions per topic, at least 4, at most 8. ~15 min.
- topics "b<first>-<last>": blocks of 3 consecutive topics (last block may have 2–4). 2 questions per topic. ~20–30 min.
- mock   "m1" (and "m2" when there are more than 7 days of plan): all topics, 2 questions per topic,
         at least 10, at most 25; m1 is the one linked from the last day's mixed test.
Without a plan: no daily tests, only topic tests and mocks.
"""
import json, sys, pathlib

def main(d):
    d = pathlib.Path(d)
    pack = json.load(open(d / 'pack.json', encoding='utf-8'))
    L = pack['lang']
    W = {'pt': ('Teste do dia', 'Temas', 'Teste geral'), 'fr': ('Test du jour', 'Thèmes', 'Test général'), 'en': ('Daily test', 'Topics', 'Full test')}[L]
    old = {}
    if (d / 'tests.json').exists():
        for t in json.load(open(d / 'tests.json', encoding='utf-8')).get('tests', []):
            old[t['id']] = t.get('questions', [])
    tests = []
    plan = json.load(open(d / 'plan.json', encoding='utf-8')) if (d / 'plan.json').exists() else None
    if plan:
        for day in plan['days']:
            q = [s for s in day['s'] if s['a'] == 'quiz']
            if not q:
                continue
            tp = q[0]['q']
            tests.append({'id': 'd' + day['d'], 'kind': 'daily', 'date': day['d'], 'title': f'{W[0]} · {", ".join(map(str, tp))}',
                          'topics': tp, 'need': max(4, min(8, 2 * len(tp))), 'minutes': 15})
    ns = [t['n'] for t in pack['topics']]
    blocks = [ns[i:i + 3] for i in range(0, len(ns), 3)]
    if len(blocks) > 1 and len(blocks[-1]) == 1:
        blocks[-2] += blocks.pop()
    for b in blocks:
        tests.append({'id': f'b{b[0]}-{b[-1]}', 'kind': 'topics', 'title': f'{W[1]} {b[0]}–{b[-1]}' if len(b) > 1 else f'{W[1]} {b[0]}',
                      'topics': b, 'need': 2 * len(b), 'minutes': 10 * len(b)})
    days = len(plan['days']) if plan else 0
    for i in range(1, (3 if days > 7 else 2)):
        need = max(10, min(25, 2 * len(ns)))
        tests.append({'id': f'm{i}', 'kind': 'mock', 'title': f'{W[2]} {i}', 'topics': ns, 'need': need, 'minutes': max(30, need * 4)})
    for t in tests:
        t['questions'] = old.get(t['id'], [])
    json.dump({'tests': tests}, open(d / 'tests.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    todo = [(t['id'], t['need'] - len(t['questions'])) for t in tests if len(t['questions']) < t['need']]
    print(f'tests.json: {len(tests)} tests ({sum(t["kind"] == "daily" for t in tests)} daily, {sum(t["kind"] == "topics" for t in tests)} topic, {sum(t["kind"] == "mock" for t in tests)} full)')
    for i, n in todo:
        print(f'TO WRITE {i}: {n} question(s)')

if __name__ == '__main__':
    main(sys.argv[1])
