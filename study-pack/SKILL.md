---
name: study-pack
description: Turns course material from Notion or uploaded files into a lean numbered syllabus, an interactive revision artifact and an optional dated study plan, after personalization questions.
---

# Study Pack

Builds up to three linked artifacts from one course's material:

1. **Syllabus — <Course>**: numbered topics, bare essentials only.
2. **Revision — <Course>**: interactive lesson and exercises, personalized.
3. **Study Plan — <Course>** (optional): day-by-day plan up to a deadline, linked to 1 and 2, with a graph view.

## Step 1 — Gather the material

- Sources: Notion pages the user names or links (fetch each one with the Notion tools and follow the child pages that belong to the course), uploaded files (PDF, docx, slides, images — read them in full), or pasted text. If the user names a course but gives no source, search Notion for it and confirm the page in one line.
- Read everything before writing. Collect every topic, definition, theorem or rule, method, typical trap, worked example, every exercise with its source (sheet + number), and the exam date if it appears.
- Build the **master topic list**: numbered 1, 2, 3… in the course's order, one topic per number, never letters. All three artifacts share this numbering and it never changes.
- If a source is missing or unreadable, say which one and continue with the rest.

## Step 2 — Ask the personalization questions

Ask before building anything. Use AskUserQuestion (max 4 questions per call, max 4 options per question; "Other" is added automatically and lets the user type). In a session without it, ask the same questions in plain text as numbered lists. Write the questions in the user's language. Never ask something the request already answers.

**2a — Color theme** (6 choices, so it doesn't fit AskUserQuestion):
Black & orange · Yellow, white & orange · Yellow, white & blue · Dark blue & light blue · Black & pink · Something else.
When the Visualizer is available, show an inline picker: one clickable swatch per theme showing background / surface / accent, plus a text field for "something else"; each click calls `sendPrompt` with the choice. Otherwise list the six in plain text and let the user answer with a number.

**2b — Options** (one AskUserQuestion call):
1. Features (multiSelect): Sidebar (contents + progress) · Focus highlight (dims everything except the part being read) · Question history · Progress tracker
2. Exercise types (multiSelect): Multiple choice · Free answer corrected by Claude (paste working or a photo) · True / false · Fill in the blank
3. Exercises per topic: 3 · 5 (Recommended) · 8 · 10
4. Font: Atkinson Hyperlegible (most readable) · IBM Plex Sans · Lexend — "Other" to type any Google Font name

**2c — Second call:**
1. Language of the artifacts: Français · Português · English
2. Extra options (multiSelect): Exam countdown · Recall links to earlier topics · "Review only" filter for missed questions · Light/dark switch
3. Study plan with a deadline? Yes · No

**2d — Only if Study plan = Yes** (if No, no more plan questions):
1. Deadline: the exam date found in the material (show it, only if found) · In 1 week · In 2 weeks — "Other" to type a date
2. Hours per day: You know (Recommended) · Enter my number
   If "Enter my number": ask once more — 1h · 2h · 3h · 4h, "Other" for any number.

Defaults if the user skips a question: Dark blue & light blue · Sidebar + Focus highlight + Progress tracker · Multiple choice + Free answer · 5 per topic · Atkinson Hyperlegible · language of the conversation · no plan.

## Step 3 — Syllabus artifact

Load `artifact-design` first. Hand-built HTML artifact (not a Docs type), so it carries the theme and the anchors.

- Title "Syllabus — <Course>", chosen theme, font and language.
- One block per topic: big number + topic name (≤ 6 words), then 2–6 bullets of what must be known.
- Each bullet ≤ 12 words: noun phrases, rules or formulas. No explanatory sentences, no intro, no conclusion, no filler ("it is important to", "note that").
- Complete: every topic and every exam-relevant rule from the material is there. Nothing invented beyond it.
- Math with MathJax (cdnjs). Anchor ids `t1`, `t2`… Once the Revision artifact exists, each topic links to its section there (republish the syllabus with the links).
- Re-read before publishing: if a bullet can lose a word without losing meaning, cut it.

## Step 4 — Revision artifact

Load `artifact-design`, and also `artifact-capabilities` whenever Free answer or Question history is on (they need runtime capabilities: asking Claude, keeping state). If the user already has revision artifacts (list the artifacts and read the most recent revision one), match their structure: one reading column, numbered sections, light/dark tokens, MathJax.

For each topic `n` (section id `ch<n>`, heading "n · Name"):

- **Explanation**: short paragraphs, definitions in boxed cards, traps in a red card ("Trap n"), one step-by-step worked example in the course's own notation.
- **Exercises**: the chosen number and types. Take them from the material first (keep the source: sheet + number), then write new ones in the same style to reach the count. Each one has an answer and an explanation of *why*. MCQ wrong options are plausible mistakes, and the explanation names the mistake behind each one.
- Multiple choice: instant right/wrong coloring, then the explanation. Free answer: textarea + photo upload, sent to Claude for a verdict (correct / partly / wrong) and the corrected working; "Show answer key" as the fallback when the capability is unavailable.

How each option is built:

- **Sidebar** → left contents rail with per-topic progress dots and jump links; a floating button on phones.
- **Focus highlight** → the paragraph or exercise being read stays at full contrast, everything else dims (opacity ≈ 0.15); toggle button; respects reduced motion.
- **Question history** → panel listing every attempt (question, answer given, right/wrong, date), filterable, with "Redo"; saved with a state capability, else localStorage wrapped in try/catch.
- **Progress tracker** → done / missed counts and a bar per topic and overall.
- **Exam countdown** → header box with the date and days left.
- **Recall links** → dotted accent links back to the earlier topic a notion comes from.
- **Review only** → filter showing only missed questions.
- **Light/dark switch** → toggle that sets `data-theme`.

On load, if the URL has `#ch<n>`, scroll to that topic (the Study Plan links rely on this).

Check before publishing: every topic of the master list is present, the exercise count per topic matches the choice, every answer is verified (recompute math in code when possible), the page works at phone width.

## Step 5 — Study Plan (only if the user said Yes)

Build it after the other two are published, so their URLs exist.

- Days available: today up to the day before the deadline (the deadline day is the exam).
- **"You know"**: estimate each topic's load from its size and difficulty in the material. Default 2h on weekdays, 3h on weekends, never more than 4h. Structure: first pass in course order; spaced reviews of each topic at about +1, +3 and +7 days; the last day is a mixed test built from missed questions; keep ~10 % buffer. If the time is too short, say so in one line and compress (fewer reviews, hardest topics first).
- **User's number**: same structure, scaled exactly to that many hours per day; if it can't cover everything, say what was cut.
- Artifact "Study Plan — <Course>", same theme, font and language:
  - Summary row: deadline, days left, total hours, number of topics.
  - Day-by-day list: date, hours, sessions. Each session = topic n + action (learn / exercises / review / mock test) + duration + links to `Syllabus#t<n>` and `Revision#ch<n>`. One checkbox per session, saved (state capability, else localStorage).
  - Graph view: stacked bar chart of hours per day colored by topic; a timeline (topic rows × days) showing when each topic is learned and reviewed; a done-vs-planned progress line. Load the `dataviz` skill if it is listed.
- Add a link to the plan in the Revision artifact's header.

## Finish

A few lines only: what was built (the artifact cards carry the links), anything missing from the material, how many exercises came from the course vs. were written. No recap of the steps.
