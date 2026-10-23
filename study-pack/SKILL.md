---
name: study-pack
description: Turns course material from Notion or uploaded files into a linked study pack (syllabus, full resumo, interactive revision, optional study plan), or updates an existing pack, after personalization questions.
---

# Study Pack

Builds (or updates) up to four linked artifacts from one course's material:

1. **Syllabus — <Course>**: numbered topics, bare essentials only.
2. **Resumo — <Course>**: the complete content with full explanations and at least 3 solved examples per topic.
3. **Revision — <Course>**: interactive lesson and exercises, personalized, with tutor chat and notes.
4. **Study Plan — <Course>** (optional): day-by-day plan up to a deadline, with a graph view.

All four share the same topic numbering and link to each other: `Syllabus#t<n>`, `Resumo#r<n>`, `Revision#ch<n>`. On load, each artifact scrolls to the anchor in its URL.

## Step 0 — Does a pack already exist?

Before anything else, list the user's artifacts (`Artifact` list, scope "all") and look for titles "Syllabus — / Resumo — / Revision — / Study Plan — <Course>" (or close matches of the course name).

- **Found**: ask (AskUserQuestion) "A study pack for <Course> already exists. Update it or create a new one?" · Update the existing pack (Recommended) · Create a new pack. Then, if Update: "What should change?" (multiSelect) · Add new material · Change options (theme, font, exercises…) · Add a missing artifact · Regenerate exercises.
- **Not found but unsure** (the course name is ambiguous): ask once "Is there already a study pack for this course?" with the closest matches as options and "No, start fresh".
- **Not found**: go on to Step 1 silently.

**Update mode rules**
- Read every existing artifact of the pack first (`Artifact` read) and its `<script type="application/json" id="pack-config">` block (see Config block below). Reuse its theme, font, language and options: only ask the questions the user wants to change, plus the ones the new material raises (e.g. exercise source if they now uploaded exercises).
- Publish with the existing `url` every time, so links, notes, chat notes and question history survive. Never drop a capability the page already declares, never rename or reorder database collections.
- Topic numbering never changes: existing topics keep their number; new topics get the next numbers. If a new topic belongs in the middle of the course order, keep its new number and say so in one line.
- Merge, don't overwrite: new definitions, examples and exercises are added to the right topic; the user's notes and attempts are untouched. If new material contradicts the old, keep the newer source and say which point changed.
- Finish by listing what was added or changed per artifact.

## Step 1 — Gather the material

- Sources: Notion pages the user names or links (fetch each one with the Notion tools and follow the child pages that belong to the course), uploaded files (PDF, docx, slides, images — read them in full), or pasted text. If the user names a course but gives no source, search Notion for it and confirm the page in one line.
- Read everything before writing. Collect every topic, definition, theorem or rule, method, typical trap, worked example, every exercise with its source (sheet + number), and the exam date if it appears.
- **The user's own exercises**: if the user uploaded exercises they have to do (exercise sheets, past exams, homework), tag each one: source (sheet + number), topic number, difficulty, method(s) used, and whether a **resolution** is included (full, partial, final answer only, none).
- Build the **master topic list**: numbered 1, 2, 3… in the course's order, one topic per number, never letters. All artifacts share this numbering and it never changes.
- Note whether the course is **calculation-heavy** (math, physics, statistics, engineering, finance, anything with functions, equations or numeric answers). This decides question 2d-1.
- If a source is missing or unreadable, say which one and continue with the rest.

## Step 2 — Ask the personalization questions

Ask before building anything. Use AskUserQuestion (max 4 questions per call, max 4 options per question; "Other" is added automatically and lets the user type). In a session without it, ask the same questions in plain text as numbered lists. Write the questions in the user's language. Never ask something the request (or, in update mode, the pack config) already answers. Skip a question whose condition isn't met.

**2a — Color theme** (7 choices, so it doesn't fit AskUserQuestion):
Focus (cream, slate & sage — made for concentration and dyslexia) · Black & orange · Yellow, white & orange · Yellow, white & blue · Dark blue & light blue · Black & pink · Something else.
When the Visualizer is available, show an inline picker: one clickable swatch per theme showing background / surface / text / accent, plus a text field for "something else"; each click calls `sendPrompt` with the choice. Otherwise list the seven in plain text and let the user answer with a number.

The **Focus** theme follows readability research (British Dyslexia Association style guide, low-glare reading): no pure white, no pure black, soft contrast, calm cool accent.
- Light: background `#F7F1E3` (cream), surface `#FDF9EF`, text `#2E3440` (dark slate), muted `#5B6472`, accent `#4F7F6E` (sage), accent-2 `#5A7FA6` (soft blue), trap card `#B5564B` on `#F6E3DE`.
- Dark: background `#1F2328`, surface `#272C33`, text `#E6E1D6` (warm off-white), accent `#8DB5A5`, accent-2 `#8EAED0`.
- Line height 1.6–1.8, max line length ~70 characters, left-aligned text (never justified), no italics for emphasis (use bold), generous paragraph spacing.

**2b — First call:**
1. Features (multiSelect): Sidebar (contents + progress) · Focus highlight (dims everything except the part being read) · Question history · Progress tracker
2. Exercise types (multiSelect): Multiple choice · Free answer corrected by Claude (paste working or a photo) · True / false · Fill in the blank
3. Exercise source — **only if the user uploaded their own exercises**: My exercises only · 50/50 mine & yours · Yours (from the course + written by Claude)
4. Font: Atkinson Hyperlegible (most readable) · Lexend · OpenDyslexic (made for dyslexia) · IBM Plex Sans — "Other" to type any Google Font name

**2c — Second call:**
1. Exercises per topic:
   - If source is *My exercises* or *50/50*: All my exercises · 5 (Recommended) · 8 · 3 — "Other" for any number.
   - Otherwise: 3 · 5 (Recommended) · 8 · 10.
2. Language of the artifacts: Français · Português · English
3. Extra options (multiSelect): Exam countdown · Recall links to earlier topics · "Review only" filter for missed questions · Light/dark switch
4. Study plan with a deadline? Yes · No

**2d — Third call** (only the questions whose condition is met; skip the call if none):
1. Graph calculator — **only if the course is calculation-heavy**: Yes, add a graph calculator (Recommended) · No
2. Tutor chat inside the artifacts (ask questions, auto-notes of what you didn't get): Yes (Recommended) · No
3. Deadline — **only if Study plan = Yes**: the exam date found in the material (show it, only if found) · In 1 week · In 2 weeks — "Other" to type a date
4. Hours per day — **only if Study plan = Yes**: You know (Recommended) · Enter my number
   If "Enter my number": ask once more — 1h · 2h · 3h · 4h, "Other" for any number.

Defaults if the user skips a question: Focus theme if they mention concentration or dyslexia, else Dark blue & light blue · Sidebar + Focus highlight + Progress tracker · Multiple choice + Free answer · 50/50 if they uploaded exercises, else Yours · 5 per topic · Atkinson Hyperlegible · language of the conversation · no plan · graph calculator Yes when calculation-heavy · tutor chat Yes.

## Exercise selection rules (used by Resumo and Revision)

**Source = My exercises**
- *All my exercises*: use every one of the user's exercises, placed under its topic, nothing added. A topic with none gets a one-line notice ("No exercise of yours covers this topic") and no invented ones.
- *A number*: per topic, pick the best N of the user's exercises: the most exam-relevant first, then variety — each method of the topic covered at least once, a spread of difficulty (easy → exam level), no two that test the same thing the same way. If a topic has fewer than N, use all of them and say so.

**Source = 50/50 mine & yours**
- *All my exercises*: every one of the user's exercises, plus the same number written by Claude in the same style, aimed at the methods and traps the user's set covers least.
- *A number*: half from the user's (chosen by the rules above, rounded up), half written by Claude, same style and notation, filling the gaps in methods and difficulty.

**Source = Yours**: course exercises first (keep sheet + number), then new ones in the same style to reach the count.

Always label each exercise's origin: "Your sheet 3, ex. 2" · "Course, sheet 1, ex. 4" · "New".

**Resolutions provided by the user**
- When an exercise comes with a resolution, that resolution is the answer key. Keep its steps and notation, and explain it: for each step, *what* is done and *why* (the rule or definition it uses, linked to its topic), plus the trap a student would fall into at that step.
- Partial resolution or final answer only: complete the missing steps in the same style and mark them "Completed by Claude".
- Check every provided resolution (recompute in code when possible). If one looks wrong, don't silently fix it: show the original, flag "This step looks wrong", and give the corrected working next to it.
- No resolution: write a full one and verify it.

## Step 3 — Syllabus artifact

Load `artifact-design` first, and `artifact-capabilities` for the notes (state). Hand-built HTML artifact (not a Docs type), so it carries the theme and the anchors.

- Title "Syllabus — <Course>", chosen theme, font and language.
- One block per topic: big number + topic name (≤ 6 words), then 2–6 bullets of what must be known.
- Each bullet ≤ 12 words: noun phrases, rules or formulas. No explanatory sentences, no intro, no conclusion, no filler ("it is important to", "note that").
- Complete: every topic and every exam-relevant rule from the material is there. Nothing invented beyond it.
- Math with MathJax (cdnjs). Anchor ids `t1`, `t2`…
- Each topic links to `Resumo#r<n>` and `Revision#ch<n>` once those exist (republish with the links).
- **Notes** on each topic block (see Notes below).
- Re-read before publishing: if a bullet can lose a word without losing meaning, cut it.

## Step 4 — Resumo artifact

Load `artifact-design` (and `artifact-capabilities` for notes, tutor chat and graph calculator state). Title "Resumo — <Course>", same theme, font and language. This is the complete reference: where the Syllabus is the skeleton and the Revision is practice, the Resumo is the full course, readable on its own.

For each topic `n` (section id `r<n>`, heading "n · Name"):
- **Full explanation**: every definition, theorem, rule and method of the topic from the material, explained completely — intuition first, then the formal statement, then when and how to use it. Definitions in boxed cards, properties and formulas in a formula card, traps in a red card ("Trap n"). Course notation throughout.
- **At least 3 solved examples**, from simple to exam level, covering different methods of the topic. Take them from the user's exercises with resolutions first, then course examples, then new ones. Every step written out and justified (same rules as resolutions above). Each example has its origin label.
- **Links** at the top and bottom of the section: "Essentials → Syllabus#t<n>" · "Practice → Revision#ch<n>"; recall links to earlier topics where a notion comes from (if Recall links is on).
- **Notes**, tutor chat and graph calculator as chosen (see Shared components).
- Header: table of contents with all topics; link to the Study Plan if it exists.

Check before publishing: every topic of the master list is present, each has ≥ 3 solved examples, every result is verified (recompute math in code), nothing contradicts the source material, the page works at phone width.

## Step 5 — Revision artifact

Load `artifact-design`, and also `artifact-capabilities` whenever Free answer, Question history, notes, tutor chat or graph calculator is on. If the user already has revision artifacts (list the artifacts and read the most recent revision one), match their structure: one reading column, numbered sections, light/dark tokens, MathJax.

For each topic `n` (section id `ch<n>`, heading "n · Name"):

- **Explanation**: short paragraphs, definitions in boxed cards, traps in a red card ("Trap n"), one step-by-step worked example in the course's own notation. A "Full version → Resumo#r<n>" link at the top.
- **Exercises**: the chosen number, types and source (Exercise selection rules). Each one has an answer and an explanation of *why*; for the user's exercises with a resolution, the explanation follows that resolution step by step. MCQ wrong options are plausible mistakes, and the explanation names the mistake behind each one.
- Multiple choice: instant right/wrong coloring, then the explanation. Free answer: textarea + photo upload, sent to Claude for a verdict (correct / partly / wrong) and the corrected working; "Show answer key" as the fallback when the capability is unavailable.
- **Notes** on each section and on each exercise.

How each option is built:

- **Sidebar** → left contents rail with per-topic progress dots and jump links; a floating button on phones.
- **Focus highlight** → the paragraph or exercise being read stays at full contrast, everything else dims (opacity ≈ 0.15); toggle button; respects reduced motion.
- **Question history** → panel listing every attempt (question, answer given, right/wrong, date), filterable, with "Redo"; saved with a state capability, else localStorage wrapped in try/catch.
- **Progress tracker** → done / missed counts and a bar per topic and overall.
- **Exam countdown** → header box with the date and days left.
- **Recall links** → dotted accent links back to the earlier topic a notion comes from.
- **Review only** → filter showing only missed questions.
- **Light/dark switch** → toggle that sets `data-theme`.

Check before publishing: every topic of the master list is present, the exercise count per topic matches the choice (or the notice explains why not), every answer is verified (recompute math in code when possible), every user resolution was checked, the page works at phone width.

## Shared components (Syllabus, Resumo, Revision)

### Notes (always on)
- A small note icon on every topic block (Syllabus), every section and solved example (Resumo), every section and every exercise (Revision). Hidden by default: the icon only shows a dot/count when a note exists.
- Click the icon → a note card unfolds under that block: free text (Markdown + `$…$` math rendered with MathJax), date, edit, delete. Click again to fold it.
- A "My notes" panel (header button) lists all notes of the artifact by topic, with a filter (all / my notes / didn't-understand notes) and a jump link to each one.
- Notes on an exercise also appear in that exercise's Question history entry.
- Saved with a state capability (per viewer, survives republishes); fallback localStorage wrapped in try/catch, with a one-line warning that notes then live in this browser only.

### Tutor chat (if Yes)
- A chat button (bottom-right) opens a chat panel; on phones it is a full-height sheet. Uses the "ask Claude" runtime capability.
- Every question is sent with context: course name, the current topic (the section in view), that topic's content from the artifact, and the exercise if the chat was opened from one ("Ask about this" button on each exercise and example). The tutor answers in the artifact's language, with the course's notation, MathJax-rendered, short, and links to the right `#r<n>` / `#ch<n>`. It never just gives the answer to an exercise the user hasn't attempted: hint first, full solution on request.
- **Didn't-understand notes**: after each exchange, a "Save as note" button; and when the user says they don't get something (or after 2+ questions on the same point), the tutor offers to save automatically. The note is written by Claude: *what wasn't clear* (one line) + *the explanation that worked* (short) + link to the section. It is attached, hidden, to the section or exercise it's about, with a distinct "?" icon, and appears in "My notes" under "Didn't understand". Click to read, edit or delete.
- Chat history per topic is kept with the same state capability.
- If the capability is unavailable: hide the chat button and say so in one line in the finish message; notes still work.

### Graph calculator (if Yes)
- A "Graph calc" button in the header of Resumo and Revision. Click → a floating rectangle (≈ 380×320, resizable from the corner) appears over the page; drag it freely by its title bar (pointer events, works with touch); a minimize and a close button; it never blocks scrolling of the page beneath. Position, size and content are remembered.
- Desmos-like behavior, built in-page (canvas + math.js from cdnjs for parsing):
  - Expression list: one expression per line, each with its own color and a show/hide toggle; `y = f(x)`, `f(x) = …` definitions reusable in later lines, implicit-free explicit functions, `x = a` vertical lines, points `(a, b)`, parametric `(cos t, sin t)`, inequalities shaded.
  - Unknown letters become sliders automatically (`a = 1` with a draggable slider, adjustable range).
  - Plot: grid with labeled axes, pan by dragging, zoom with wheel / pinch, "reset view" button, trace a curve by hovering to show coordinates, mark zeros, extrema and intersections on click.
  - A plain-number line acts as a scientific calculator (`2^10`, `sqrt(2)`, `sin(pi/6)`, `log`, `ln`, `e`, `pi`), result shown at the right of the line.
  - Degrees/radians toggle; LaTeX preview of each expression.
- "Plot this" button on formulas and examples that contain a function: opens the calculator pre-filled with it.

### Config block
Each artifact carries `<script type="application/json" id="pack-config">` with: course, version date, theme, font, language, features, exercise types, source, count, extras, graph calc, tutor chat, plan settings, the master topic list (number + name), the source files/pages used, and the URLs of the other artifacts. Update mode reads it.

## Step 6 — Study Plan (only if the user said Yes)

Build it after the other artifacts are published, so their URLs exist.

- Days available: today up to the day before the deadline (the deadline day is the exam).
- **"You know"**: estimate each topic's load from its size and difficulty in the material (and the number of the user's exercises in it). Default 2h on weekdays, 3h on weekends, never more than 4h. Structure: first pass in course order (read Resumo → do Revision exercises); spaced reviews of each topic at about +1, +3 and +7 days (Syllabus + missed questions + own notes); the last day is a mixed test built from missed questions; keep ~10 % buffer. If the time is too short, say so in one line and compress (fewer reviews, hardest topics first).
- **User's number**: same structure, scaled exactly to that many hours per day; if it can't cover everything, say what was cut.
- Artifact "Study Plan — <Course>", same theme, font and language:
  - Summary row: deadline, days left, total hours, number of topics.
  - Day-by-day list: date, hours, sessions. Each session = topic n + action (read / exercises / review / mock test) + duration + links to `Syllabus#t<n>`, `Resumo#r<n>` and `Revision#ch<n>`. One checkbox per session, saved (state capability, else localStorage).
  - Graph view: stacked bar chart of hours per day colored by topic; a timeline (topic rows × days) showing when each topic is learned and reviewed; a done-vs-planned progress line. Load the `dataviz` skill if it is listed.
- Add a link to the plan in the header of the Syllabus, Resumo and Revision.

## Fonts
- Atkinson Hyperlegible, Lexend, IBM Plex Sans and any typed name: Google Fonts.
- **OpenDyslexic** is not on Google Fonts: get the woff2 files (regular + bold) from npm or GitHub (antijingoist/opendyslexic), both reachable from the workspace, and embed them with `@font-face` (asset upload or base64). If they can't be fetched, use Lexend and say so in one line. With OpenDyslexic, keep the Focus spacing rules (line height ≥ 1.6, no justified text, no italics).

## Finish

A few lines only: what was built or updated (the artifact cards carry the links), anything missing from the material, how many exercises came from the user / the course / were written, how many user resolutions were flagged as wrong, and any feature that couldn't be enabled (chat, font). No recap of the steps.
