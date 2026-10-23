#!/usr/bin/env python3
"""study-pack kit — make plan.json for the Plano page.

    python3 plan.py PACK_DIR

Reads pack.json → "plan" settings:
  "plan": {"start": "YYYY-MM-DD" (default today),
           "hours": "auto" | number of hours per day,
           "busy": {"YYYY-MM-DD": {"hours": 1, "note": "Exame de IEI às 10:30"}},
           "weights": {"1": 1.0, "2": 1.4, ...}   (topic load; default 1)}
and the exam date in pack.json → "exam".

Rules (fixed): days from start to the day before the exam. "auto" = 2h weekdays, 3h weekends, never above 4h.
First pass in course order (learn + exercises, 50/50); reviews at about +1, +3 and +7 days; the last day is a
mixed test (90 min) + review; ~10 % of the time is left free. Prints what had to be cut when time is short.
"""
import json, sys, datetime, pathlib, math

def r5(x):
    return max(5, int(round(x / 5.0)) * 5)

def main(d):
    d = pathlib.Path(d)
    pack = json.load(open(d / 'pack.json', encoding='utf-8'))
    ps = pack.get('plan') or {}
    exam = datetime.date.fromisoformat(pack['exam']['date'])
    start = datetime.date.fromisoformat(ps['start']) if ps.get('start') else datetime.date.today()
    days = [start + datetime.timedelta(i) for i in range((exam - start).days)]
    if len(days) < 2:
        print('PLAN ERROR: fewer than 2 days before the exam'); sys.exit(1)
    hours = ps.get('hours', 'auto'); busy = ps.get('busy', {})
    cap = {}
    for day in days:
        iso = day.isoformat()
        if iso in busy and 'hours' in busy[iso]:
            h = busy[iso]['hours']
        elif hours == 'auto':
            h = 3 if day.weekday() >= 5 else 2
        else:
            h = float(hours)
        cap[iso] = int(min(h, 4) * 60)
    last = days[-1].isoformat()
    sched = {day.isoformat(): [] for day in days}
    left = dict(cap)
    # last day: mixed test + review of everything
    sched[last].append({'t': 0, 'a': 'test', 'm': min(90, left[last])}); left[last] -= sched[last][0]['m']
    if left[last] >= 15:
        sched[last].append({'t': 0, 'a': 'rev', 'm': left[last]}); left[last] = 0
    work_days = [x.isoformat() for x in days[:-1]]
    total = sum(cap[x] for x in work_days) * 0.9
    topics = [t['n'] for t in pack['topics']]
    W = {n: float((ps.get('weights') or {}).get(str(n), 1.0)) for n in topics}
    sw = sum(W.values())
    first_budget, rev_budget = total * 0.62, total * 0.38
    first = {n: first_budget * W[n] / sw for n in topics}
    # first pass: fill each day up to 65 % so reviews fit, in course order
    soft = {x: int(cap[x] * 0.65) for x in work_days}
    learned = {}; i = 0; cut = []
    for n in topics:
        need = {'learn': r5(first[n] / 2), 'ex': r5(first[n] / 2)}
        for act in ('learn', 'ex'):
            m = need[act]
            while m > 0 and i < len(work_days):
                x = work_days[i]
                room = min(soft[x], left[x])
                if room < 15:
                    i += 1; continue
                take = m if m <= room else r5(room - 2) if room >= 20 else room
                take = min(take, room)
                sched[x].append({'t': n, 'a': act, 'm': take}); left[x] -= take; soft[x] -= take; m -= take
                learned.setdefault(n, x)
            if m > 0:
                cut.append(f'topic {n}: {m} min of {act}')
    # reviews
    rev_each = {n: r5(max(15, rev_budget * W[n] / sw / 3)) for n in topics}
    for n in topics:
        if n not in learned:
            continue
        base = datetime.date.fromisoformat(learned[n])
        for off in (1, 3, 7):
            target = base + datetime.timedelta(off)
            placed = False
            for x in work_days:
                if datetime.date.fromisoformat(x) < target:
                    continue
                if left[x] >= rev_each[n]:
                    sched[x].append({'t': n, 'a': 'rev', 'm': rev_each[n]}); left[x] -= rev_each[n]; placed = True; break
                if left[x] >= 15:
                    sched[x].append({'t': n, 'a': 'rev', 'm': left[x]}); left[x] = 0; placed = True; break
            if not placed:
                cut.append(f'topic {n}: review +{off}d')
    out = {'days': [{'d': x, 'note': (busy.get(x) or {}).get('note', ''), 's': sched[x]} for x in sched if sched[x]],
           'hours_note': ps.get('hours_note', ''), 'cut': cut}
    json.dump(out, open(d / 'plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tot = sum(s['m'] for day in out['days'] for s in day['s'])
    print(f'plan.json: {len(out["days"])} days, {tot/60:.1f} h planned')
    for c in cut:
        print('CUT', c)

if __name__ == '__main__':
    main(sys.argv[1])
