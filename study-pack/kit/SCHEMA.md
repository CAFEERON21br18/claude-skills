# Pack JSON — the only thing Claude writes

`build.py` turns these files into the pages (Sílabo, Resumo, Revisão, optional Testes, optional Mapa, optional Plano). Write them with a Python script (`json.dump`), never by hand, so LaTeX backslashes survive. Text fields use the small markdown below.

## Text fields (markdown-lite)

- Paragraphs separated by a blank line; `- ` lists; `1. ` lists; `**bold**` (never italics).
- Maths in `$…$` (inline) or `$$…$$` (display), KaTeX syntax. Write `<` and `>` normally (the build escapes them).
- `[Resumo 3](#r3)`, `[Revisão 3](#ch3)`, `[Sílabo 3](#t3)`: links between pages (same tab).
- `[[3]]` or `[[3|text]]`: dotted recall link to topic 3 on the same page.

## pack.json

```json
{
 "slug": "cdi",                      // storage prefix → "cdi-" (localStorage + db docs). Never change it on update.
 "course": "Cálculo Diferencial e Integral I",
 "short": "CDI-I", "school": "IST", "lang": "pt",          // pt | fr | en
 "exam": {"label": "1.º Teste", "date": "2026-11-06", "time": "18:00"},
 "theme": "focus",                   // focus | black-orange | yellow-white-orange | yellow-white-blue | darkblue-lightblue | black-pink | {custom object, same keys as themes.json}
 "font": "Atkinson Hyperlegible",    // Atkinson Hyperlegible | Lexend | OpenDyslexic | IBM Plex Sans | any Google Font name
 "features": {"sidebar": true, "focus": true, "history": true, "progress": true, "countdown": true,
              "recall": true, "review_only": true, "calc": true, "tutor": true, "plan": true, "map": true, "tests": true},
 "exercise": {"format": ["lesson-style"], "source": "mine|mix|yours", "count": 5},   // count: number or "all"
 "urls": {"silabo": "", "resumo": "", "revisao": "", "testes": "", "mapa": "", "plano": ""},   // artifact URLs; "" until published
 "storage": {"prefix": "cdi-", "docs": {"revisao": "revisao", "plano": "plano"}, "ls": {"revisao": "cdi-revisao-v1"}},  // only for packs made before the kit: keep their old keys
 "plan": {"start": "2026-10-24", "hours": "auto", "busy": {"2026-10-27": {"hours": 1, "note": "Exame de IEI às 10:30"}}, "weights": {"3": 1.5}, "hours_note": "2h nos dias úteis, 3h ao fim-de-semana"},
 "methods": {"learning": ["active_recall", "worked_examples", "feynman"], "time": "pomodoro", "hansei": true},   // optional: see › Method parts
 "topics": [{"n": 1, "name": "Reais, módulos e indução", "meta": "Aula 1"}],
 "sources": ["Notion › Ruben › IST › CDI: Aulas 1–11"]
}
```

## topics/&lt;n&gt;.json

```json
{
 "n": 1,
 "syllabus": ["Axiomas de corpo e de ordem de $\\mathbb R$", "…"],          // 2–6 bullets, ≤ 12 words each
 "resumo":   [BLOCK, …],        // full explanation (Resumo)
 "examples": [EXAMPLE, …],      // ≥ 3 (Resumo)
 "lesson":   [BLOCK, …],        // short lesson (Revisão)
 "worked":   EXAMPLE,           // one step-by-step example (Revisão)
 "exercises":[EXERCISE, …],     // Revisão
 "shortage": "Só há 2 exercícios teus neste tópico.",  // optional one-line notice
 "parts": {"active_recall": {…}, "feynman": {…}}       // one per method in pack.methods (see › Method parts)
}
```

**BLOCK** `{"kind": "p|def|thm|formula|method|trap|bookerr|note", "title": "…", "body": "markdown", "explain": "markdown", "plot": "x^2-2"}`
(`plot` optional: adds "Ver no gráfico" when the calculator is on. `bookerr` = red "Gralha no livro" box.)
`explain` = **"Em palavras simples"**: what it means in everyday words, why it is true or useful, when you use it. Required (≥ 12 words) on `def`, `thm`, `formula`, `method` in the Resumo and on `def`, `thm`, `formula` in the Revisão lesson.

**EXAMPLE** `{"title", "origin", "statement", "method", "steps": [STEP…], "answer", "check"?, "plot"?, "reconstructed"?: true}`
`method` = **"Como abordar"** (required, ≥ 8 words): what in the statement tells you which method to use, and why. `check` = **"Verificação"** (optional, recommended): a quick test that the answer is right.

**STEP** `{"do": "…", "why": "…", "trap"?: "…", "by_claude"?: true, "flag"?: {"text": "what looks wrong", "fix": "corrected working"}}`
Every step has a `do` (the working, nothing skipped) and a `why` (the rule or idea that justifies it). Examples and keys need ≥ 2 steps (true/false: ≥ 1).

**EXERCISE**
```json
{"id": "e1-3", "type": "mcq|tf|free", "origin": "Ficha 3, ex. 2 | Course, sheet 1, ex. 4 | new",
 "q": "statement",
 "options": ["A", "B", "C", "D"],          // mcq: exactly 4
 "why": ["why A…", "…", "…", "…"],          // mcq: 4 (tf: 2) — each wrong one names the typical mistake
 "correct": 0,                              // mcq 0..3 ; tf 0 = true, 1 = false
 "gate": true,                              // calculation question: "Resolve no papel primeiro" + "Já resolvi — mostrar opções"
 "free_too": true,                          // also show the free-answer correction box under the options
 "layout": "two",                           // optional: options in two columns (only short, non-maths options)
 "key": {"method": "how you should have attacked it", "steps": [STEP…], "answer": "…", "check": "…"},   // complete correction: method + every step + answer (+ check)
 "plot": "…", "reconstructed": true,
 "hints": ["Pista 1", "Pista 2"],           // optional: progressive hints (required on Shu and starter problems)
 "level": 2,                                // learning by doing: 1 (direct) · 2 (one more step) · 3 (exam level)
 "topic": 2}                                // in tests.json and in parts.interleaving: the topic the question is about
```
Each MCQ `why` is a full sentence (≥ 6 words): why it is right, or which mistake leads to it.

- `origin: "new"` shows "Novo". Never label an invented exercise or example with a course source.
- Ids: `e<topic>-<k>`. On update, the same exercise (same sheet + number) keeps its id; new ones take the next numbers.

## Method parts

`pack.methods.learning` lists the student's learning methods (from the app's study-profile quiz, or the question form). **Every listed method needs its part in every topic** (`topics/<n>.json › parts.<method>`); interleaving starts at topic 2; learning by doing has no part of its own (it grades the plain exercises). `time` (pomodoro | kaizen | finnish) only shapes the plan. `hansei: true` adds the 2-minute reflection at the end of each Revisão topic (3 fixed questions + optional `parts.hansei: ["topic-specific question"]`). No flashcards. Legacy names: `blurting` → active_recall.

Exercises inside parts are ordinary EXERCISEs (same gate, ids unique across the whole pack, e.g. `e3-k12`, `e3-w1`, `e3-m2`); they count in the topic progress.

| Method | Page · where | `parts.<method>` | Minimum |
|---|---|---|---|
| `active_recall` | Revisão · before the lesson | `{"questions": [{"q", "a"}], "keys": ["key point"]}` — closed-book questions, then "write everything you remember", compared with `keys` | 4 questions, 3 keys |
| `spaced` | Revisão · after the lesson | `{"quick": [{"q", "a"}]}` — 5-minute review to redo after 1, 3, 7 days | 4 |
| `learning_by_doing` | Revisão · exercises | no part: every plain exercise gets `"level"` 1–3, shown easiest first | one of each level |
| `kumon` | Revisão · after the lesson | `[[EXERCISE…], …]` — 3–5 levels of short drills; a level opens at 90 % right on the one before | 3 per level |
| `worked_examples` | Revisão · after the lesson | `[{"example": EXAMPLE, "twin": EXERCISE}]` — solved example, then the same problem with other numbers | 2 pairs |
| `shuhari` | Revisão · after the lesson | `{"shu": [EXERCISE + hints], "ha": [EXERCISE], "ri": [EXERCISE type free]}` — copy the model, vary it, open problem | 1 each, Shu ≥ 2 hints |
| `problem_first` | Revisão · before + after the lesson | `{"starter": EXERCISE + hints, "compare": "how the lesson solves it vs a first try"}` | 2 hints, compare ≥ 20 words |
| `interleaving` | Revisão · after the lesson | `[EXERCISE + "topic"]` — this topic mixed with earlier ones; the key starts by naming the topic (added by the build) | 4, ≥ 2 topics incl. this one |
| `feynman` | Revisão · after the lesson | `{"task": "Explica … a alguém de 12 anos", "checklist": ["what a good explanation covers"]}` | task ≥ 8 words, 4 checks |
| `mindmap` | Resumo (map) + Revisão (complete the map) | `{"center", "branches": [{"label", "leaves": []}], "blanks": [[branch, leaf]]}` | 3 branches × 2 leaves, 3 blanks |
| `sq3r` | Resumo · before + after the explanation | `{"survey": "overview", "questions": ["guiding question"], "recap": ["answer"]}` | survey ≥ 20 words, 3 + 3 |
| `cornell` | Resumo · after the explanation | `{"cues": [{"cue", "note"}], "summary": "…"}` — notes can be covered to self-test | 4 rows, summary ≥ 25 words |

Pads (the "write what you remember", Feynman, SQ3R and Hansei boxes) and Feynman ticks are saved in the browser under `<slug>-m-…`. `example-methods/` is a pack with every part on (`python3 example-methods/make.py` rebuilds it).

## Quality gate (build.py refuses the pack otherwise)

| What | Minimum |
|---|---|
| Resumo explanation of a topic (bodies + `explain`) | 180 words |
| Revisão lesson of a topic | 70 words, with at least one `p` paragraph |
| `explain` on def / thm / formula (/ method in the Resumo) | 12 words |
| `method` on every example and every exercise key | 8 words |
| steps per example / key | 2 (true/false: 1), each with `do` and a `why` of ≥ 3 words |
| MCQ `why` lines | 6 words each |

Formulas count as two words. These are floors, not targets: the SKILL.md › Explanations rules decide the real length.

## plan.json

Made by `plan.py` (never by hand on a new plan). On update, keep the dated sessions as they are (ticks are keyed by date + index); only change texts and counts.
With `features.tests`, each day but the last ends with `{"t": 0, "a": "quiz", "m": 15, "q": [topics]}` (the daily test).
The Plano page adapts the plan live (nothing to write): unfinished sessions of past days move to the next days, the load follows the student's pace over the last 4 days (50–100 %), a topic under 60 % in a finished test gets a 20-min extra review the next day, and when time runs out only plain reviews are dropped. "Plano original" shows the plan as made.

## tests.json (only when `features.tests` is on) — the Testes page

Run `python3 tests.py PACK_DIR` (after `plan.py`): it writes every test with its `topics` and `need`; then write the questions.

```json
{"tests": [
 {"id": "d2026-11-06", "kind": "daily", "date": "2026-11-06", "title": "Teste do dia · 1, 2", "topics": [1, 2], "need": 4, "minutes": 15, "questions": [EXERCISE + "topic", …]},
 {"id": "b1-3", "kind": "topics", "title": "Temas 1–3", "topics": [1, 2, 3], "need": 6, "minutes": 30, "questions": […]},
 {"id": "m1", "kind": "mock", "title": "Teste geral 1", "topics": [1, …, 11], "need": 22, "minutes": 90, "questions": […]}
]}
```
Rules: ids unique (question ids too, e.g. `m1-q7`); every question has `topic` (one of the test's topics) and a complete `key`; `need` questions at least; topic and mock tests cover every one of their topics. Questions are **new** (not copies of the Revisão exercises), same style and difficulty as the exam, mixed types. Daily tests check what was studied that day; mocks look like the real test. Results are saved under `<slug>-testes` and feed the Plano.


## map.json (only when `features.map` is on) — the Mapa page

One generic engine for every course. The **content** says what the course is; the engine never changes. Pick the two switches that fit the course:

| `kind` (what an arrow means: A → B) | Use for | Arrow means |
|---|---|---|
| `causal` | history, geography, economics, literature periods | A **caused / led to** B |
| `prereq` | maths, physics, CS, languages (grammar) | you need A **before** B |
| `process` | biology, chemistry, algorithms, procedures | step A **comes before** step B |

| `layout` | Use for | Needs |
|---|---|---|
| `timeline` | things with a real order in time; one coloured band per group | `cols` (ordered columns) + `col` on every node |
| `layers` | no calendar; the engine puts each idea in the column of its longest dependency chain | nothing else |

```json
{
 "kind": "causal|prereq|process", "layout": "timeline|layers",
 "groups": [{"id": "P", "name": "Guerra e paz"}],            // 1–5 groups: colour (theme token) + symbol ● ■ ▲ ◆ ★
 "cols":   [{"id": "1914", "label": "1914–18"}],             // timeline only, in order
 "eras":   [{"label": "Anos 20", "col": "1923"}],            // optional quick-jump chips (timeline only)
 "nodes": [{
   "id": "e1", "group": "P", "col": "1914",                  // col: timeline only
   "label": "I Guerra Mundial",                              // ≤ 40 chars, plain text, no maths
   "text": "One-line summary (shown big).",
   "ctx":  "Context: what came before / why it appears. 2–3 short sentences. A string.",
   "what": ["Explanation, one short sentence per item.", "Use **bold** for 1–3 key words."],   // list, 3–5 items
   "keys": ["What to remember for the test (≤ 10 words each)"],                              // list, 3–5 items
   "terms": [{"t": "Armistício", "d": "Pausa nos combates, não é a paz."}],                  // optional vocabulary
   "hook": "A picture to remember: dominós.",                // optional memory image
   "pages": "Manual, p. 28 (Doc. 14)",                       // optional
   "extra": ["Facts that are NOT in the user's sources (Claude's own knowledge). Empty is best."],   // optional, shown as such
   "topic": 3                                                // optional: topic n → links "Ver no Resumo / Praticar" and "Ver no mapa" on the other pages
 }],
 "edges":  [{"a": "e1", "b": "e3", "why": "One sentence: why A leads to B."}],
 "routes": [{"name": "Rússia: do czar à URSS", "nodes": ["e1", "r2", "r3"]}]   // each consecutive pair must be an edge
}
```

Rules enforced by `build.py`: 6–80 nodes; unique ids; every node has `ctx`, `what`, `keys`; edges point to existing nodes, no duplicates, no cycles, never backwards in time on a timeline; every route step is an edge; at least one route. A node with no edge is only a warning. Write sentences of at most ~18 words. Everything must come from the user's material; anything else goes in `extra`.
The page has three tabs: **Mapa** (tap a card: context, explanation, key points, vocabulary, memory image, causes/consequences), **Rotas** (guided steps along `routes`), **Treino** (why / what next / key-point questions). "Já sei" ticks are saved under `<slug>-mapa`.
Other pages get a "Ver no mapa" link per topic when the node has a `topic` and `urls.mapa` is set; the map opens with `#t<n>` (cards of topic n) or `#n-<id>` (one card).
If the map text contains `$…$`, KaTeX is loaded on the Mapa page automatically.
