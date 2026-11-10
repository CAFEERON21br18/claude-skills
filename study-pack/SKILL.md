---
name: study-pack
description: Turns course material from Notion or uploaded files into a linked study pack (Sílabo, Resumo, Revisão, optional Testes, Mapa and Plano), or updates an existing pack, with one fixed question form and a fixed page kit so every course looks and works the same.
---

# Study Pack

Linked pages for one course (three always, three optional), always built by the **kit** (`kit/` in github.com/CAFEERON21br18/claude-skills, folder `study-pack/kit`):

1. **Sílabo**: numbered topics, bare essentials.
2. **Resumo**: the full course, explained so that someone who reads it understands it, ≥ 3 solved examples per topic.
3. **Revisão**: short but clear lesson + exercises (yours / the user's), each with a complete step-by-step correction, plus the parts of the student's study methods (Resumo gets the SQ3R, Cornell and mind-map parts); grading, history, notes, tutor (its notes are saved on the exercise or block the chat is about and shown at the top of it).
4. **Testes** (optional): a daily test at the end of each plan day on that day's topics, tests on a few topics, full mock tests; answer everything, then see the full correction; results feed the Plano.
5. **Mapa** (optional): an idea map for any kind of course (causes in history, prerequisites in maths/CS, steps in biology/procedures). Every card carries context, explanation, key points, vocabulary and a memory image; three tabs: Mapa · Rotas (guided paths) · Treino (questions).
6. **Plano** (optional): dated plan to the exam, charts, ticks; it adapts by itself to what the student really did (unfinished sessions move on, load follows their pace, weak topics from the tests get an extra review).

## Rule zero: the kit decides the look, you only write content

- Every page comes out of `kit/build.py`. Never write or patch page HTML, CSS or JS by hand, never "improve" the layout, never add a page-specific style. Same options ⇒ same pages, whatever the course (CDI, AL, LP…).
- You write **only** the JSON described in `kit/SCHEMA.md` (with Python `json.dump`), then build, check, publish.
- The questions are **always** the form from `kit/questions.py`, in its order, in its format. Never reword, reorder, split, or ask them another way. Never list theme names without their colors.
- If something can't be done with the kit, say so in one line in the final message. Don't work around it in HTML.

What the kit fixes for you (don't re-implement): the header (CDI layout: course line + title on the left, the pack tabs on the right (3 to 6), tools on the second row: countdown · page tools · *As minhas notas* · light/dark button with the sun/moon icon of ruben-bonanni-ribeiro.dev), the topic rail, KaTeX with embedded fonts, wide-maths fitting, notes, tutor chat, graph calculator, focus mode, countdown in calendar days, same-tab links, phone layout, storage.

Tools per page (fixed order, an option that is off is simply absent):

| Page | Header tools | Strip under header |
|---|---|---|
| Sílabo | countdown · Foco · As minhas notas · ☾/☀ | — |
| Resumo | countdown · Calculadora · Foco · As minhas notas · ☾/☀ | — |
| Revisão | countdown · Calculadora · Foco · Só erradas · Histórico · As minhas notas · ☾/☀ | done / right / to review + saved |
| Testes | countdown · Hoje · ☾/☀ | tests done + average |
| Mapa | countdown · ☾/☀ (the map has its own Mapa · Rotas · Treino tabs, zoom and Ouvir inside the page) | — |
| Plano | countdown · Plano original · Hoje · Esconder feitas · ☾/☀ | sessions done + hours |

## Step 0 — Kit, and does a pack already exist?

1. Get the kit, every time (it may have changed):
   `git clone --depth 1 https://github.com/CAFEERON21br18/claude-skills /tmp/sp && cp -r /tmp/sp/study-pack/kit ./kit`
   Read `kit/SCHEMA.md`.
2. List the user's artifacts (`Artifact` list, scope "all", limit 200) and look for "Sílabo/Syllabus/Programa — <Course>", "Resumo — <Course>", "Revisão/Revision — <Course>", "Testes tipo/Tests — <Course>", "Mapa/Map/Carte — <Course>", "Plano — <Course>" or close names.
3. **Found** → ask once, plain: "Já existe um pacote de <Course>. Atualizo esse ou crio um novo?" (Atualizar o existente (recomendado) · Criar um novo). If update: "O que muda?" (Juntar material novo · Mudar opções · Juntar uma página que falta (Testes, Mapa ou Plano) · Refazer os exercícios).
   **Ambiguous name** → ask once which one, with the closest matches and "Nenhum, começar do zero". **Not found** → go on silently.

### Update mode
- Read **each existing page in full** with `Artifact` `action:"read"` **without `path`** now, in Step 0. The publish is refused unless the whole live version was read. A big page comes back as a saved file: read that file in chunks of ~150–200 lines until the end. Then also save each page's HTML (`read` with `path:"index.html"`) for `extract.py`.
- `python3 kit/extract.py pack <saved pages…>` rebuilds `pack/` (pack.json, topics, plan.json, map.json, tests.json) from kit pages. A pack made with an older kit fails the new quality gate (explain / method / full keys): bring every topic up to it (Step 3) before building — that is the point of the update. Keep `slug`, `storage`, `urls`, topic numbers and exercise ids as they are.
- **Old pack (no kit data)**: infer the settings from the page (theme, font, language, features, count) and write `pack.json`. Copy its storage keys into `"storage"` so progress survives: the localStorage key (e.g. `cdi-revisao-v1`, `lp-revision-v2`) in `storage.ls.revisao`, the db document name (e.g. `revisao`, `lp-revision-v2`) in `storage.docs.revisao`, and the same for `plano` and the theme prefix.
- Exercises: the same exercise (same sheet + number) keeps its id; new ones take the next numbers. Attempts on removed exercises show as "Exercício da versão anterior": say so at the end.
- Plano kept: never move dated sessions (ticks are keyed by date + index); only update texts, counts and links. A plan rebuilt from scratch loses the old ticks: say so at the end.
- Only ask the questions the user wants to change, plus the ones the new material raises (e.g. source if they now uploaded exercises). Reuse everything else from `pack.json`.
- Publish to the existing `url` of each page. Finish with what changed, per page.

## Step 1 — Gather the material (before any question)

- Sources: Notion pages named or linked (fetch each, follow the course's child pages), uploaded files (PDF, docx, slides, images, read in full), pasted text. Course named but no source → search Notion, confirm the page in one line.
- Search Notion for a page named like **"lesson-style"** (the user's own exercise format). If found, read it: it becomes the first exercise-format option.
- Collect every topic, definition, theorem, method, trap, worked example, exercise with its source (sheet + number), exam date, and for the user's own exercises: topic, difficulty, methods, resolution (full / partial / answer only / none).
- **Statements missing** (a sheet with only answers): say it in one line right now, before the questions, and ask for the PDF. Never invent a statement. A statement rebuilt from another page of the user's or from the answer table gets `"reconstructed": true` ("enunciado reconstituído").
- **Textbook in Notion**: extract it with one subagent per block of topics (e.g. 1–3, 4–8, 9–11), in parallel. Each returns JSON per topic: definitions and theorems with the book's numbering, traps, ≥ 4 worked examples with steps (what + why) and final answer; each recomputes every number with sympy and flags book errors instead of fixing them silently → `bookerr` blocks ("Gralha no livro").
- Master topic list: numbered 1, 2, 3… in course order, never letters. Never renumbered later.
- Calculation-heavy course (maths, physics, statistics, engineering, finance) → the calculator question is shown.
- Unreadable source → say which one, continue.

## Step 2 — The questions (one fixed form)

1. `python3 kit/questions.py --lang <pt|fr|en> [--mine] [--calc] [--lesson-style] [--exam YYYY-MM-DD] [--methods a,b,c]`
   (`--mine` if the user uploaded their own exercises, `--calc` if calculation-heavy, `--lesson-style` if that Notion page exists, `--exam` if a date was found, `--methods` with the student's methods when known: the Study Pack app's study-profile quiz result, what the user said, or the existing `pack.methods` in update mode; add `hansei` if it is on.)
2. Call the Visualizer `read_me` (module `elicitation`), then `show_widget` with **exactly** the printed HTML, title `study_pack_details`. Nothing else in the widget, no extra question.
3. The answer comes back as one line (`Theme: … · Font: … · Features: … · Exercise format: … · Source: … · Per topic: … · Language: … · Graph calc: … · Tutor: … · Plan: … · Deadline: … · Hours: … · Methods: …`). Map it to `pack.json` (Methods → `methods.learning`, Hansei → `methods.hansei: true`; no methods picked → no `methods`).
4. No Visualizer in this session → send the output of `questions.py … --text` verbatim (it shows each theme with its hex colors) and wait for the numbered answers. No other format, ever.
5. Skipped or unanswered (unattended run) → defaults: Focus theme, Atkinson Hyperlegible, sidebar + focus + history + progress + countdown, lesson-style if found else multiple choice + free answer, 50/50 if the user has exercises else yours, 5 per topic, conversation language, calculator yes if calculation-heavy, tutor yes, plan yes only if an exam date was found (the plan is counted back from that date), methods from `--methods` else active recall + spaced repetition + worked examples. Say which defaults were used.

Then, before building:
- **Source = mine only** and some topics have none of the user's exercises → say which topics now, and ask once: leave them without exercises (with the notice) or fill those topics only with course / Claude exercises.
- "Other" theme → copy the closest preset in `kit/themes.json`, change only colors, run `python3 kit/check_contrast.py <file>` until it passes, put the object in `pack.json` `theme`.
- Formats → exercise types: *lesson-style* = its rules (below); *Como na fonte* = keep the sheet's form (open question → `free`; MCQ / true-false only where the sheet has them); *Escolha múltipla* = `mcq`; *Resposta livre* = `free`; *V/F* = `tf`. (Fill-in-the-blank is not in the kit.)

## Step 3 — Write the content (JSON only)

Split the topics into groups and write them with **up to 4 subagents in parallel** (e.g. 1–3, 4–6, 7–9, 10–11). Give each: `kit/SCHEMA.md`, its topics' material, the answers from Step 2, and these rules (Explanations, Complete corrections, Method parts, and the page rules below). Each writes `pack/topics/<n>.json` with a Python script (`json.dump`, never by hand) and checks every computation with sympy. Then read their files and check they follow the rules (`parts` present for every method, in every topic).

**Explanations — someone who reads must understand.** Short is fine; unclear is not. For every notion (definition, theorem, rule, method):
- Say what it means in everyday words, then the formal statement, then when and how you use it. The formal part goes in `body`, the plain-words part in `explain` ("Em palavras simples") — required on def / thm / formula (and method in the Resumo).
- Define every symbol and word the first time it appears. Never "é óbvio", "basta ver", "trivialmente", "como sabemos".
- Give the reason, not only the rule: why it is true or why it works, in one or two sentences.
- Link ideas: what this notion is needed for, what it comes from (recall links `[[n]]`).
- One idea per sentence, ≤ ~20 words, concrete words. A list of formulas is never an explanation.
- The Revisão lesson is shorter than the Resumo but must stand alone: an opening `p` paragraph that explains the topic, then cards each with `explain`.
- The kit refuses thin topics (see SCHEMA.md › Quality gate). The floors are a minimum, not the goal.

**Complete corrections — exactly how you should have solved it.** Every exercise key, every Resumo example and the Revisão worked example:
- `method` ("Como abordar"): what in the statement tells you which method to use, and why that one.
- `steps`: every step written out, none skipped ("simplificando…" is not a step); each with `do` (the working) and `why` (the rule or idea that justifies it), `trap` where students usually slip.
- `answer`, and `check` ("Verificação": substitute back, test a value, check units or signs) whenever one exists.
- MCQ: each `why` is a full sentence; the right one says why it is right, each wrong one names the mistake that leads to it. The full key is shown after answering.

**Comprehension check (always).** When the topic files are written, give each group to a **fresh subagent that has not seen the source** and ask it to read the Resumo and Revisão parts (method parts included) as a student: list every sentence, step or symbol it cannot follow, and every correction step that jumps. Fix all of it, then build.

**Mapa** (only if `features.map`; read `kit/MAP-GUIDE.md`): write `pack/map.json` after the topics exist, so every card can point to its topic (`topic`). Choose the engine switches from the course, never from the look:
- `kind`: `causal` (history, geography, economics, literature), `prereq` (maths, physics, CS, grammar), `process` (biology, chemistry, algorithms, procedures).
- `layout`: `timeline` when a real calendar orders the ideas (one coloured band per theme, `cols` in order), else `layers` (the engine orders by dependency).
- 1–5 `groups` (the main themes), 15–50 `nodes`, every arrow with a one-sentence `why`, 4–8 `routes` (guided paths; each step must be an edge).
Every node needs `label` (≤ 40 chars), `text` (one line), `ctx` (context), `what` (3–5 short sentences), `keys` (3–5 things to remember), and where the material allows `terms`, `hook` (a picture to remember), `pages`. Write the skeleton (groups, cols, nodes with label/text/topic, edges, routes) yourself, then enrich the nodes with **up to 4 subagents in parallel** (one per group), each reading only the topics' JSON as source. Dyslexia-friendly rules: sentences ≤ 18 words, one idea per sentence, concrete words. Nothing outside the user's material goes in the main fields: put it in `extra` (shown as "Acrescentado por Claude") and say so in the final message. Add `"map": true` to `features` and `"mapa": ""` to `urls`.

**Sílabo** (`syllabus`): 2–6 bullets per topic, ≤ 12 words, noun phrases / rules / formulas, no sentences, no filler. Every exam-relevant rule, nothing invented.

**Resumo** (`resumo` + `examples`): every definition, theorem, rule and method of the topic, explained completely (intuition → formal statement → when and how to use it), course notation; `def` / `thm` / `formula` / `method` / `trap` blocks. **≥ 3 solved examples** per topic, simple → exam level, different methods: the user's exercises with resolutions first, then course examples, then new ones. Every step has `do` + `why` (+ `trap` where students slip). Origin label: the real source, or `"new"` → "Novo". Never label an invented example with a course source. When an MCQ is reused as an example, keep only the solution steps: drop sentences about the options ("A troca…", "A opção B…", "C e D…").

**Revisão** (`lesson`, `worked`, `exercises`): short lesson blocks, one `worked` example, then the exercises.

**Method parts** (only when `pack.methods` is set; shapes and minimums in `kit/SCHEMA.md` › Method parts). The pack adapts to how the student learns: every method listed gets its own part in **every topic** (`topics/<n>.json › parts`), and the build refuses a missing one. Write them from the same material, same notation, same correction rules (every exercise inside a part has a complete key). No flashcards, ever.
- **Active recall**: closed-book questions on the core of the topic (what, why, when), short answers; `keys` = the 3–5 points a good "write everything you remember" page must contain.
- **Spaced repetition**: 4–6 quick questions answerable in 5 minutes in total, the ones worth seeing again after 1, 3, 7 days.
- **Learning by doing**: give every plain exercise a `level` (1 direct application · 2 one extra step · 3 exam level), at least one of each; add exercises if needed.
- **Kumon**: 3–5 levels of very short drills (≥ 3 each), one small step harder per level, the last close to exam level; each drill tests one thing.
- **Worked examples**: 2–3 solved examples (not the Resumo ones), each followed by its twin: the same problem with other numbers, same method.
- **Shuhari**: Shu = the model problem again with `hints` that walk its steps; Ha = the same method on a changed case; Ri = an open `free` problem (choose the method, invent a case, explain).
- **Problem first**: a starter problem solvable by intuition before the lesson, ≥ 2 progressive `hints`, and `compare`: how the lesson's method solves it and why it beats a first try.
- **Interleaving** (from topic 2): ≥ 4 exercises mixing this topic with earlier ones (`topic` on each), similar-looking on purpose so the student must first recognise the topic; at least one from this topic.
- **Feynman**: one task "explain … to a 12-year-old" on the hardest idea of the topic, and 4–6 checklist points a good explanation covers (the idea, an example, the why, no jargon).
- **Mind map**: the topic as a centre + 3–6 branches of 2–4 short leaves (≤ 6 words), and 3+ `blanks` on leaves worth recalling.
- **SQ3R**: a 2–3 sentence survey of the topic, 3–5 guiding questions the Resumo answers, and the `recap` answers in the same order.
- **Cornell**: 4–8 rows, cue = a question or keyword, note = its short answer; a 2–3 sentence summary.
- **Hansei** (`hansei: true`): nothing to write; optionally 1 topic-specific question in `parts.hansei`.
- Time method (`pomodoro` · `kaizen` · `finnish`): nothing to write in the pages.

Exercise selection:
- *Mine only, All*: every user exercise under its topic, nothing added; a topic with none gets the notice. *Mine only, N*: the best N per topic — most exam-relevant first, then variety (each method once, easy → exam level, no two testing the same thing the same way); fewer than N → all of them + `shortage` notice.
- *50/50, All*: every user exercise + as many by Claude, aimed at what theirs covers least. *50/50, N*: half the user's (chosen as above, rounded up), half Claude's in the same style.
- *Yours*: course exercises first, then new ones in the same style.

Resolutions given by the user: they are the answer key — keep their steps and notation, explain each step (what, why, trap). Missing steps: complete them, `by_claude: true`. Check every resolution (recompute with sympy); a wrong step is never fixed silently: `flag` with the text and the correction. No resolution: write one and verify it.

**lesson-style rules** (when chosen; the Notion page wins if it says more): `mcq` with exactly 4 options A–D; calculation questions `gate: true` ("Resolve no papel primeiro" + "Já resolvi — mostrar opções") and `free_too: true` (paste working or a photo, Claude grades it); maths options one per line (default layout), each on a single line; every wrong option is a typical mistake and its `why` names it; the correct letter varies (never the same letter more than twice in a row).

Text: `**bold**`, never italics; maths in `$…$` / `$$…$$`; recall links `[[n]]` when Recall is on.

**Testes** (only if `features.tests`; needs the plan for the daily tests): after Step 4, run `python3 kit/tests.py pack`. It writes `pack/tests.json` with every test, its topics and how many questions it needs (`need`), consistent with the plan: one **daily test** per plan day on that day's topics (so a student who studies 3 topics a day gets a short test on those 3 at the end of the day), **topic tests** on blocks of 3 topics (a mini test after every 3 topics), and 2 **full mock tests** at the end, like two exam papers. Write the questions with up to 4 subagents (one per kind or per block): **new** questions (not copies of the Revisão exercises), same style, types and difficulty as the exam and as the Revisão, mixed types, every one with `topic` and a complete correction (same rules as above). Daily tests check that day's material only; mocks look like the real test. Add `"tests": true` to `features` and `"testes": ""` to `urls`. Re-running `tests.py` after a plan change keeps the questions of tests whose id did not change.

## Step 4 — Plan (only if Plano = yes)

Put the settings in `pack.json` → `plan` (start = today, `hours`: "auto" or the number, `busy` days with other exams and their notes, `weights` for heavy topics, `hours_note` in the pack language), then `python3 kit/plan.py pack`. It prints what had to be cut when time is short: say it in the final message. With Testes on, each day ends with its 15-min daily test (linked to the Testes page); run `tests.py` after it.

The Plano adapts itself in the page (nothing to write, never edit the plan for it): sessions of past days that were not ticked move to the next days (learning and exercises first), the next days' load follows the student's real pace over the last 4 days (50–100 % of the plan), a topic scored under 60 % in a finished test gets a 20-min extra review the next day, and when time runs out only plain reviews are dropped (learning, exercises and extra reviews never are). A box says what was adjusted; "Plano original" shows the plan as made.

## Step 5 — Build, check, publish

1. `python3 kit/build.py pack --out pack/out` (stops on any schema error: fix the JSON, never the HTML).
2. `python3 kit/check.py pack/out --shots` must print **ALL CHECKS PASSED** (no page overflow at 400 / 1440 px light & dark, nothing clipped, 0 KaTeX errors, no raw `$`, no JS error, fixed header and tool order, no new-tab links, interactions work). Then **look** at `pack/out/shots/*` (header, dense maths blocks, phone dark). Fix the JSON, rebuild, re-check once.
3. Load `artifact-capabilities` and declare what the pages use: account storage (`db`) and viewer identity (`user`) for notes, history and ticks; asking Claude (`sample`) for the tutor and the grading (Sílabo, Resumo, Revisão, Testes). Plano and Mapa: `db` + `user` only (the build warns that `sample` is mentioned in the shared code; ignore it for those two).
4. **New pack**: publish the 3 to 6 files (titles come from the pages, icon "book", "map" for the Mapa, "check" for the Testes), put the URLs in `pack.json` → `urls` (including `testes` and `mapa`), rebuild, re-check, republish each to its URL (the tabs and cross-links need the URLs). **Update**: URLs are already in `pack.json`; publish each page to its `url`. Adding the Mapa or the Testes to an existing pack: publish it as a new artifact, put its URL in `urls.mapa` / `urls.testes`, rebuild, then republish every existing page to its own URL (they gain the tab and the links; progress is kept because storage keys do not change). Adding the Testes to an existing plan: set `features.tests`, re-run `plan.py` only if the user agrees to lose the old ticks (say so); otherwise keep `plan.json` and the daily tests are made only for days that already have a `quiz`.

## Finish

A few lines only: what was built or updated (the cards carry the links), anything missing from the material, exercises from the user / the course / written by Claude, **the list of the user's resolutions flagged as wrong** (exercise + step), what the plan had to cut, how many tests and questions were written, which map facts come from outside the user's material (`extra`), which study methods got their own parts, and anything that couldn't be enabled (tutor, account storage). Say once that formulas copy as LaTeX (select + copy, or double-click a formula). No recap of the steps.
