# Mapa — authoring guide (any course)

The Mapa page is one engine. You never touch its HTML/CSS/JS. You choose **two switches**, write `map.json` (schema in `SCHEMA.md`), build, check, publish.

## 1. Choose the switches from the course

| Course type | `kind` | `layout` | Groups (1–5, one colour each) | An arrow A → B says |
|---|---|---|---|---|
| History, geography, economics, literature periods | `causal` | `timeline` | themes / strands (war & economy, Russia, society, art) | A led to B |
| Maths, physics, statistics, CS theory | `prereq` | `layers` | chapters or families of ideas | you need A before B |
| Programming, algorithms | `prereq` (concepts) or `process` (one algorithm) | `layers` | concept families | A before B |
| Biology, chemistry, medicine pathways | `process` | `layers` (or `timeline` for evolution/epochs) | systems / stages | step A, then step B |
| Languages (grammar) | `prereq` | `layers` | grammar areas | learn A before B |
| Law, civics | `causal` | `layers` or `timeline` | branches / institutions | A leads to B |

Worked examples: `example-maps/history-causal-timeline.json` (50 cards, 4 bands, 28 columns, 7 routes) and `example-maps/maths-prereq-layers.json` (7 cards).

## 2. Build the skeleton first (you, not subagents)

1. **Groups**: 1–5, named for the student (≤ 30 chars). They become colour + symbol (● ■ ▲ ◆ ★), so colour is never the only cue.
2. **Cols** (timeline only): ordered columns, as fine as the course needs (years, months). Several cards may share a cell; they stack.
3. **Nodes**: 15–50. One card = one idea the student must be able to explain. `label` ≤ 40 chars, `text` one line, `topic` = topic number so the card links to Resumo / Revisão. Never put maths in a label.
4. **Edges**: only real links, each with a `why` of one sentence. Aim for 1–2 edges per card; a card with 6+ is a hub: check it is right. No cycles; on a timeline an edge never goes backwards.
5. **Routes**: 4–8 guided paths of 4–10 steps (the "stories" of the course). Every step pair must be an edge.
6. **Eras** (timeline): 3–5 quick-jump chips pointing at a column.

## 3. Enrich the cards (subagents, one per group, in parallel)

Give each subagent: its nodes with the labels of their causes/effects, `pack/topics/<n>.json` as the only source, and this brief (translate to the pack language):

> For each node write `ctx` (2–3 sentences: what was before / why this appears), `what` (3–5 short sentences: what happened or how it works; **bold** 1–3 key words), `keys` (3–5 items ≤ 10 words: what to remember for the test), `terms` (0–3 `{t, d}`, `d` ≤ 14 words), `hook` (one concrete picture to remember), `pages` (only if the source gives pages), `extra` (facts that are NOT in the source; ideally empty). Sentences ≤ 18 words, one idea each, concrete words, no nested parentheses. Dates and numbers exactly as in the source. Don't invent: if the source doesn't cover it, leave it out or put it in `extra`. Write with `json.dump`; validate that every id is present and no sentence is longer than 18 words. Report doubts about facts.

Then read the files yourself: check dates, names, numbers against the topics; move general-knowledge definitions that are not in the source to `extra` or drop them; fix any `ctx` that is a list (it must be a string). Say in the final message what is in `extra`.

## 4. Build, check, look

`python3 kit/build.py pack --out pack/out`, then `python3 kit/check.py pack/out --shots` and look at the Mapa screenshots (cards readable, no overlapping lines over text, panel text wraps). `check.py` clicks a card, ticks "Já sei", follows a route and answers a Treino question.

## What the page gives the student (so you write for it)

- **Mapa**: tap a card → the causes/prerequisites (dashed amber) and consequences (solid accent) light up; panel: summary, 🔊 Ouvir, "Já sei" (saved), "Só esta cadeia", links to Resumo/Revisão, then Contexto · Explicação · A reter · Imagem · Vocabulário · links to neighbours.
- **Rotas**: one idea at a time, with the "porque…" sentence between steps.
- **Treino**: "why / what next / which sentence is really about X" questions with feedback; distractors come from other cards.
- Dyslexia: short chunks, symbol + colour, no timers, a read-aloud button, OpenDyslexic if chosen in `pack.json`, nothing animates when the system asks for reduced motion.

## Limits

6–80 nodes (split bigger courses by chapter into two packs). 5 groups max. Labels ≤ 40 chars. One language per pack (`pt`, `fr`, `en` texts exist in `i18n.json`).
