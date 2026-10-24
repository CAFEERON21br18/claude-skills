---
name: study-pack
description: Turns course material from Notion or uploaded files into a linked study pack (Sílabo, Resumo, Revisão, optional Plano), or updates an existing pack, with one fixed question form and a fixed page kit so every course looks and works the same.
---

# Study Pack

Four linked pages for one course, always built by the **kit** (`kit/` in github.com/CAFEERON21br18/claude-skills, folder `study-pack/kit`):

1. **Sílabo**: numbered topics, bare essentials.
2. **Resumo**: the full course, complete explanations, ≥ 3 solved examples per topic.
3. **Revisão**: short lesson + exercises (yours / the user's), grading, history, notes, tutor.
4. **Plano** (optional): dated plan to the exam, charts, ticks.

## Rule zero: the kit decides the look, you only write content

- Every page comes out of `kit/build.py`. Never write or patch page HTML, CSS or JS by hand, never "improve" the layout, never add a page-specific style. Same options ⇒ same pages, whatever the course (CDI, AL, LP…).
- You write **only** the JSON described in `kit/SCHEMA.md` (with Python `json.dump`), then build, check, publish.
- The questions are **always** the form from `kit/questions.py`, in its order, in its format. Never reword, reorder, split, or ask them another way. Never list theme names without their colors.
- If something can't be done with the kit, say so in one line in the final message. Don't work around it in HTML.

What the kit fixes for you (don't re-implement): the header (CDI layout: course line + title on the left, the 4 pack tabs on the right, tools on the second row: countdown · page tools · *As minhas notas* · light/dark button with the sun/moon icon of ruben-bonanni-ribeiro.dev), the topic rail, KaTeX with embedded fonts, wide-maths fitting, notes, tutor chat, graph calculator, focus mode, countdown in calendar days, same-tab links, phone layout, storage.

Tools per page (fixed order, an option that is off is simply absent):

| Page | Header tools | Strip under header |
|---|---|---|
| Sílabo | countdown · Foco · As minhas notas · ☾/☀ | — |
| Resumo | countdown · Calculadora · Foco · As minhas notas · ☾/☀ | — |
| Revisão | countdown · Calculadora · Foco · Só erradas · Histórico · As minhas notas · ☾/☀ | done / right / to review + saved |
| Plano | countdown · Hoje · Esconder feitas · ☾/☀ | sessions done + hours |

## Step 0 — Kit, and does a pack already exist?

1. Get the kit, every time (it may have changed):
   `git clone --depth 1 https://github.com/CAFEERON21br18/claude-skills /tmp/sp && cp -r /tmp/sp/study-pack/kit ./kit`
   Read `kit/SCHEMA.md`.
2. List the user's artifacts (`Artifact` list, scope "all", limit 200) and look for "Sílabo/Syllabus/Programa — <Course>", "Resumo — <Course>", "Revisão/Revision — <Course>", "Plano — <Course>" or close names.
3. **Found** → ask once, plain: "Já existe um pacote de <Course>. Atualizo esse ou crio um novo?" (Atualizar o existente (recomendado) · Criar um novo). If update: "O que muda?" (Juntar material novo · Mudar opções · Juntar uma página que falta · Refazer os exercícios).
   **Ambiguous name** → ask once which one, with the closest matches and "Nenhum, começar do zero". **Not found** → go on silently.

### Update mode
- Read **each existing page in full** with `Artifact` `action:"read"` **without `path`** now, in Step 0. The publish is refused unless the whole live version was read. A big page comes back as a saved file: read that file in chunks of ~150–200 lines until the end. Then also save each page's HTML (`read` with `path:"index.html"`) for `extract.py`.
- `python3 kit/extract.py pack <saved pages…>` rebuilds `pack/` (pack.json, topics, plan.json) from kit pages. Keep `slug`, `storage`, `urls`, topic numbers and exercise ids as they are.
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

1. `python3 kit/questions.py --lang <pt|fr|en> [--mine] [--calc] [--lesson-style] [--exam YYYY-MM-DD]`
   (`--mine` if the user uploaded their own exercises, `--calc` if calculation-heavy, `--lesson-style` if that Notion page exists, `--exam` if a date was found.)
2. Call the Visualizer `read_me` (module `elicitation`), then `show_widget` with **exactly** the printed HTML, title `study_pack_details`. Nothing else in the widget, no extra question.
3. The answer comes back as one line (`Theme: … · Font: … · Features: … · Exercise format: … · Source: … · Per topic: … · Language: … · Graph calc: … · Tutor: … · Plan: … · Deadline: … · Hours: …`). Map it to `pack.json`.
4. No Visualizer in this session → send the output of `questions.py … --text` verbatim (it shows each theme with its hex colors) and wait for the numbered answers. No other format, ever.
5. Skipped or unanswered (unattended run) → defaults: Focus theme, Atkinson Hyperlegible, sidebar + focus + history + progress + countdown, lesson-style if found else multiple choice + free answer, 50/50 if the user has exercises else yours, 5 per topic, conversation language, calculator yes if calculation-heavy, tutor yes, no plan. Say which defaults were used.

Then, before building:
- **Source = mine only** and some topics have none of the user's exercises → say which topics now, and ask once: leave them without exercises (with the notice) or fill those topics only with course / Claude exercises.
- "Other" theme → copy the closest preset in `kit/themes.json`, change only colors, run `python3 kit/check_contrast.py <file>` until it passes, put the object in `pack.json` `theme`.
- Formats → exercise types: *lesson-style* = its rules (below); *Como na fonte* = keep the sheet's form (open question → `free`; MCQ / true-false only where the sheet has them); *Escolha múltipla* = `mcq`; *Resposta livre* = `free`; *V/F* = `tf`. (Fill-in-the-blank is not in the kit.)

## Step 3 — Write the content (JSON only)

Split the topics into groups and write them with **up to 4 subagents in parallel** (e.g. 1–3, 4–6, 7–9, 10–11). Give each: `kit/SCHEMA.md`, its topics' material, the answers from Step 2, and these rules. Each writes `pack/topics/<n>.json` with a Python script (`json.dump`, never by hand) and checks every computation with sympy. Then read their files and check they follow the rules.

**Sílabo** (`syllabus`): 2–6 bullets per topic, ≤ 12 words, noun phrases / rules / formulas, no sentences, no filler. Every exam-relevant rule, nothing invented.

**Resumo** (`resumo` + `examples`): every definition, theorem, rule and method of the topic, explained completely (intuition → formal statement → when and how to use it), course notation; `def` / `thm` / `formula` / `method` / `trap` blocks. **≥ 3 solved examples** per topic, simple → exam level, different methods: the user's exercises with resolutions first, then course examples, then new ones. Every step has `do` + `why` (+ `trap` where students slip). Origin label: the real source, or `"new"` → "Novo". Never label an invented example with a course source. When an MCQ is reused as an example, keep only the solution steps: drop sentences about the options ("A troca…", "A opção B…", "C e D…").

**Revisão** (`lesson`, `worked`, `exercises`): short lesson blocks, one `worked` example, then the exercises.

Exercise selection:
- *Mine only, All*: every user exercise under its topic, nothing added; a topic with none gets the notice. *Mine only, N*: the best N per topic — most exam-relevant first, then variety (each method once, easy → exam level, no two testing the same thing the same way); fewer than N → all of them + `shortage` notice.
- *50/50, All*: every user exercise + as many by Claude, aimed at what theirs covers least. *50/50, N*: half the user's (chosen as above, rounded up), half Claude's in the same style.
- *Yours*: course exercises first, then new ones in the same style.

Resolutions given by the user: they are the answer key — keep their steps and notation, explain each step (what, why, trap). Missing steps: complete them, `by_claude: true`. Check every resolution (recompute with sympy); a wrong step is never fixed silently: `flag` with the text and the correction. No resolution: write one and verify it.

**lesson-style rules** (when chosen; the Notion page wins if it says more): `mcq` with exactly 4 options A–D; calculation questions `gate: true` ("Resolve no papel primeiro" + "Já resolvi — mostrar opções") and `free_too: true` (paste working or a photo, Claude grades it); maths options one per line (default layout), each on a single line; every wrong option is a typical mistake and its `why` names it; the correct letter varies (never the same letter more than twice in a row).

Text: `**bold**`, never italics; maths in `$…$` / `$$…$$`; recall links `[[n]]` when Recall is on.

## Step 4 — Plan (only if Plano = yes)

Put the settings in `pack.json` → `plan` (start = today, `hours`: "auto" or the number, `busy` days with other exams and their notes, `weights` for heavy topics, `hours_note` in the pack language), then `python3 kit/plan.py pack`. It prints what had to be cut when time is short: say it in the final message.

## Step 5 — Build, check, publish

1. `python3 kit/build.py pack --out pack/out` (stops on any schema error: fix the JSON, never the HTML).
2. `python3 kit/check.py pack/out --shots` must print **ALL CHECKS PASSED** (no page overflow at 400 / 1440 px light & dark, nothing clipped, 0 KaTeX errors, no raw `$`, no JS error, fixed header and tool order, no new-tab links, interactions work). Then **look** at `pack/out/shots/*` (header, dense maths blocks, phone dark). Fix the JSON, rebuild, re-check once.
3. Load `artifact-capabilities` and declare what the pages use: account storage (`db`) and viewer identity (`user`) for notes, history and ticks; asking Claude (`sample`) for the tutor and the grading (Sílabo, Resumo, Revisão). Plano: `db` + `user` only.
4. **New pack**: publish the 4 files (titles come from the pages, icon "book"), put the 4 URLs in `pack.json` → `urls`, rebuild, re-check, republish each to its URL (the tabs and cross-links need the URLs). **Update**: URLs are already in `pack.json`; publish each page to its `url`.

## Finish

A few lines only: what was built or updated (the cards carry the links), anything missing from the material, exercises from the user / the course / written by Claude, **the list of the user's resolutions flagged as wrong** (exercise + step), what the plan had to cut, and anything that couldn't be enabled (tutor, account storage). Say once that formulas copy as LaTeX (select + copy, or double-click a formula). No recap of the steps.
