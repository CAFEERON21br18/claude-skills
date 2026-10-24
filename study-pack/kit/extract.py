#!/usr/bin/env python3
"""study-pack kit — update mode: rebuild PACK_DIR from the published pages.

    python3 extract.py PACK_DIR page1.html [page2.html ...]

Each kit page carries <script id="pack-config"> and <script id="pack-src">. This writes pack.json,
topics/<n>.json and plan.json so you can merge the new material and rebuild with the SAME ids,
storage keys and URLs. A page without these blocks is an old (pre-kit) pack: the script says so;
then infer the settings from the page and write pack.json yourself (keep its storage keys: see SKILL.md).
"""
import sys, re, json, html, pathlib

def block(s, id_):
    m = re.search(rf'<script type="application/json" id="{id_}">(.*?)</script>', s, re.S)
    return json.loads(m.group(1).replace('<\\/', '</')) if m else None

def main(d, files):
    d = pathlib.Path(d); (d / 'topics').mkdir(parents=True, exist_ok=True)
    pack = None; topics = {}; plan = None; old = []
    for f in files:
        s = open(f, encoding='utf-8').read()
        cfg, src = block(s, 'pack-config'), block(s, 'pack-src')
        if not cfg or src is None:
            old.append(f); continue
        page = cfg.pop('page'); cfg.pop('built', None); cfg.pop('kit', None)
        pack = pack or cfg
        if page == 'plano':
            plan = src
        else:
            for n, part in src.items():
                topics.setdefault(int(n), {'n': int(n)}).update({k: v for k, v in part.items() if v is not None})
    if pack:
        json.dump(pack, open(d / 'pack.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        for n, t in topics.items():
            json.dump(t, open(d / 'topics' / f'{n}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if plan:
            json.dump(plan, open(d / 'plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'pack.json + {len(topics)} topics' + (' + plan.json' if plan else '') + f' written to {d}')
    for f in old:
        print(f'OLD PACK (no kit data): {f} — infer settings from the page, keep its storage keys')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
